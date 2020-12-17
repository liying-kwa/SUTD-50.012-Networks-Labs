import config
import threading
import time
import udt
import util


# Selective Repeat reliable transport protocol.
class SelectiveRepeat:

  NO_PREV_ACK_MSG = "Don't have previous ACK to send, will wait for server to timeout."

  # "msg_handler" is used to deliver messages to application layer
  def __init__(self, local_port, remote_port, msg_handler):
    util.log("Starting up `Selective Repeat` protocol ... ")
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    self.sender_base = 0                        # Used for sender only
    self.next_sequence_number = 0               # Used for sender only
    self.timer = []                             # Used for sender only
    for i in range(config.WINDOW_SIZE):
        self.timer.append(self.set_timer(i))
    self.acknowledged=[0]*config.WINDOW_SIZE    # Used for sender only
    self.s_window = [b'']*config.WINDOW_SIZE    # Used for sender only
    self.r_window = [None]*config.WINDOW_SIZE   # Used for receiver only
    self.expected_sequence_number = 0           # Used for receiver only
    self.is_receiver = True
    self.sender_lock = threading.Lock()
    self.receiver_lock = threading.Lock()


  # Set timer for individual packet, i.e. packet #i in the s_window
  def set_timer(self, seq_num):
    # IMPT: Timers have to follow seq numbers instead of list index so that
    # their mappings will not be misaligned whenever the window shifts
    return threading.Timer((config.TIMEOUT_MSEC/1000.0), self._timeout, [seq_num])


  # "send" is called by application. Return true on success, false otherwise.
  def send(self, msg):
    self.is_receiver = False
    if self.next_sequence_number < (self.sender_base + config.WINDOW_SIZE):
      self._send_helper(msg)
      return True
    else:
      util.log("s_window is full. App data rejected.")
      time.sleep(1)
      return False


  # Helper fn for thread to send the next packet
  def _send_helper(self, msg):
    self.sender_lock.acquire()
    # Send next packet to receiver
    packet = util.make_packet(msg, config.MSG_TYPE_DATA, self.next_sequence_number)
    packet_data = util.extract_data(packet)
    i = self.next_sequence_number - self.sender_base
    self.s_window[i] = packet
    util.log("Sending data: " + util.pkt_to_string(packet_data))
    self.network_layer.send(packet)
    # Start the timer
    if self.timer[i] != None:
      if self.timer[i].is_alive(): self.timer[i].cancel()
    self.timer[i] = self.set_timer(self.next_sequence_number)
    self.timer[i].start()
    self.next_sequence_number += 1
    self.sender_lock.release()
    return


  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    msg_data = util.extract_data(msg)

    if(msg_data.is_corrupt):
      if(self.is_receiver):
        if self.expected_sequence_number == 0:
          util.log("Packet received is corrupted. " + self.NO_PREV_ACK_MSG)
          return
        util.log("Received corrupted data. Do nothing.")
      return
    
    # If ACK message, assume its for sender 
    if msg_data.msg_type == config.MSG_TYPE_ACK:
      self.sender_lock.acquire()
      # Seq_num = base of s_window. Cancel timer and shift s_window forward
      if(msg_data.seq_num == self.sender_base):
        util.log("Received ACK with seq # matching the base of the s_window: "
                 + util.pkt_to_string(msg_data) 
                 + ". Cancelling timer and moving s_window forward")
        self.timer[0].cancel()
        self.acknowledged[0] = 1
        # Shift base of s_window forward to unacknowledged packet with smallest seq_num
        add_to_base = config.WINDOW_SIZE
        for i in range(config.WINDOW_SIZE):
            if self.acknowledged[i] == 0:
                add_to_base = i
                break
        util.log("DEBUG: add_to_base = " + str(i))
        self.sender_base += add_to_base
        self.timer = self.timer[add_to_base:]
        for i in range(add_to_base): self.timer.append(None)
        self.acknowledged = self.acknowledged[add_to_base:]
        for i in range(add_to_base): self.acknowledged.append(0)
        self.s_window = self.s_window[add_to_base:]
        for i in range(add_to_base): self.s_window.append(b'')
      # Seq_num != base of s_window. Mark packet as received
      elif msg_data.seq_num > self.sender_base:
        util.log("Received ACK: " + util.pkt_to_string(msg_data)
                 + ". There are messages in-flight. Cancelling timer and marking as received.")
        i = msg_data.seq_num - self.sender_base
        if self.timer[i].is_alive(): 
          self.timer[i].cancel()
        self.acknowledged[i] = 1
      self.sender_lock.release()
      
    # If DATA message, assume its for receiver
    else:
      self.receiver_lock.acquire()
      assert msg_data.msg_type == config.MSG_TYPE_DATA
      # Packet with sequence number in [rcv_base, rcv_base+N-1]
      if msg_data.seq_num >= self.expected_sequence_number:
        # Buffer and send ACK
        util.log("Received DATA: " + util.pkt_to_string(msg_data))
        ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK, msg_data.seq_num)
        self.network_layer.send(ack_pkt)
        util.log("Buffering and sending ACK: " + util.pkt_to_string(util.extract_data(ack_pkt)))
        i = msg_data.seq_num - self.expected_sequence_number
        if self.r_window[i] == None: self.r_window[i] = msg_data.payload
        # If seq_num = base of r_window, deliver this and subsequent buffered packets to app. Shift r_window.
        if msg_data.seq_num == self.expected_sequence_number:
          util.log("Seq # matched base of r_window. Delivering msgs to app layer and moving r_window foward.")
          num_buffered = config.WINDOW_SIZE
          for i in range(config.WINDOW_SIZE):
            if self.r_window[i] == None:
              num_buffered = i
              break
            self.msg_handler(self.r_window[i])
          util.log("DEBUG: num_buffered =" + str(i))
          self.r_window = self.r_window[num_buffered:]
          for i in range(num_buffered): self.r_window.append(None)
          self.expected_sequence_number += num_buffered
      # Packet with sequence number in [rcv_base-N, rcv_base-1]
      else:
        # Send ACK
        util.log("Received OLD DATA: " + util.pkt_to_string(msg_data))
        ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK, msg_data.seq_num)
        util.log("Sending ACK: " + util.pkt_to_string(util.extract_data(ack_pkt)))
        self.network_layer.send(ack_pkt)
      self.receiver_lock.release()
    return


  # Cleanup resources.
  def shutdown(self):
    if not self.is_receiver: self._wait_for_last_ACK()
    for i in range(config.WINDOW_SIZE):
      if self.timer[i] != None:
        if self.timer[i].is_alive(): self.timer[i].cancel()
    util.log("Connection shutting down...")
    self.network_layer.shutdown()
    
    
  def _wait_for_last_ACK(self):
    while self.sender_base <= self.next_sequence_number-1:
      util.log("Waiting for last ACK from receiver with sequence # "
               + str(int(self.next_sequence_number-1)) + ".")
      time.sleep(1)


  def _timeout(self, seq_num):
    self.sender_lock.acquire()
    i = seq_num - self.sender_base
    util.log("Timeout! Resending packets with seq # " + str(self.sender_base + i) + ".")
    if self.timer[i] != None:
      if self.timer[i].is_alive(): 
        self.timer[i].cancel()
    self.timer[i] = self.set_timer(seq_num)
    pkt = self.s_window[i]
    util.log("Resending packet: " + util.pkt_to_string(util.extract_data(pkt)))
    self.network_layer.send(pkt)
    self.timer[i].start()
    self.sender_lock.release()
    return
