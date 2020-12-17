# 50.012 Networks
# Lab 2: Building your own RESTful APIs
# Student: Kwa Li Ying (1003833)
# API code containing server code implemented with Flask


# import libraries
from flask import Flask, json, jsonify, request, Response
from functools import wraps

# Flask
app = Flask(__name__)

# Variables
messages = '{"message_log": [{"user":"istd", "message":"Hi everyone!"}, {"user":"istd", "message":"Feel free to use the dashboard for feedback."}]}'
availability = '{"1":{"available":"yes", "user":"NONE"}, "2":{"available":"no", "user":"natalie"}, "3":{"available":"yes", "user":"NONE"}}'

# Functions needed for authentication
def check_auth(username, password):
    return username == 'admin' and password == 'secret'

def authenticate():
    message = {'message': "Authenticate."}
    resp = jsonify(message)
    resp.status_code = 401
    resp.headers['WWW-Authenticate'] = 'Basic realm="Example"'
    return resp

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return authenticate()
        elif not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated



# Welcome and Room Details

# SUTD room information service welcome page
@app.route('/')
def api_root():
	return "Welcome to SUTD's room information service. \n"

# List rooms in "<room-id>. <room>" format
@app.route('/rooms')
def api_rooms():
	return """Rooms available:
1. PI Lab
2. DSL Lab
3. I3 Lab
"""


# Floor system

# Check which floor a room is on
@app.route('/rooms/which-floor')
def api_floors():
	return "/rooms/which-floor/<roomid> will return the floor that the room is on \n"

@app.route('/rooms/which-floor/<roomid>')
def api_floor(roomid):
	roomname = {"1":"PI Lab", "2":"DSL Lab", "3":"I3 Lab"}
	roomfloor = {"1":"5", "2":"4", "3":"6"}
	return "The {} is on floor {}. \n".format(roomname[roomid], roomfloor[roomid])


# Availability system

# Check availability of rooms
@app.route('/rooms/availability', methods=['GET'])
def api_availability():
	resp = Response(availability, status=200, mimetype='application/json')
	return resp

# Update availability of rooms. Requires authentication
@app.route('/rooms/availability', methods=['PATCH', 'PUT'])
@requires_auth
def api_availability_update():
	global availability
	availability_dict = json.loads(availability)
	availability_dict.update(request.json)
	availability = json.dumps(availability_dict)
	js = json.dumps(request.json)
	resp = Response(js, status=200, mimetype='application/json')
	return resp


# Message Dashboard system

# Message Dashboard: Retrieve all messages from the dashboard
@app.route('/messages', methods=['GET'])
def api_messages_get():
	resp = Response(messages, status=200, mimetype='application/json')
	return resp

# Message Dashboard: Receive a message posted by a user. Supports json and text formats
@app.route('/messages', methods=['POST'])
def api_messages_send():
	global messages
	if request.headers['Content-Type'] == 'application/json':
		messages_dict = json.loads(messages)
		messages_dict['message_log'].append(request.json)
		messages = json.dumps(messages_dict)
		js = json.dumps(request.json)
		resp = Response(js, status=200, mimetype='application/json')
		return resp
	elif request.headers['Content-Type'] == 'text/plain':
		messages_dict = json.loads(messages)
		messages_dict['message_log'].append({"user": "anonymous", "message": request.data})
		messages = json.dumps(messages_dict)
		js = json.dumps({"user": "anonymous", "message": request.data})
		resp = Response(js, status=200, mimetype='application/json')
		return resp
	else:
		resp = Response('Accepted content-types: application/json, text/plain', status=415, mimetype='text/plain')
		return resp

# Message Dashboard: Delete a message. Requires authentication
@app.route('/messages', methods=['DELETE'])
@requires_auth
def api_messages_delete():
	global messages
	messages_dict = json.loads(messages)
	try:
		if 'index' not in request.args:
			resp = Response('Specify message index', status=400, mimetype='text/plain')
			return resp
		elif int(request.args['index']) >= len(messages_dict['message_log']):
			resp = Response('Index specified exceeds number of messages', status=400, mimetype='text/plain')
			return resp
		else:
			popped_dict = messages_dict['message_log'].pop(int(request.args['index']))
			messages = json.dumps(messages_dict)
			js = json.dumps(popped_dict)
			resp = Response(js, status=200, mimetype='application/json')
			return resp
	except ValueError:
		resp = Response('Index must be an integer', status=400, mimetype='text/plain')
		return resp


# Main function
if __name__ == '__main__':
	app.run()

