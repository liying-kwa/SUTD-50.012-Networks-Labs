#!/bin/bash

# 50.012 Networks
# Lab 2: Building your own RESTful APIs
# Student: Kwa Li Ying (1003833)
# Bash script with client curl commands


# Welcome page and floor system: GET requests

# Welcome page
echo "Test GET: Welcome page"
curl http://127.0.0.1:5000/
printf "\n"

# List rooms
echo "Test GET: List rooms"
curl http://127.0.0.1:5000/rooms
printf "\n"

# Check which floor each room is on
echo "Test GET: Check which floor each room is on"
curl http://127.0.0.1:5000/rooms/which-floor/1
curl http://127.0.0.1:5000/rooms/which-floor/2
curl http://127.0.0.1:5000/rooms/which-floor/3
printf "\n"


# Room vacancy: GET & PATCH/PUT requests

# Check availability of rooms and update accordingly. Updates require authentication
# Order of requests: check availability, update (auth), check availability, update (auth), check availability,
#	update (no auth), check availability
echo "Test GET: Check availability of all rooms (initial state)"
curl http://127.0.0.1:5000/rooms/availability
printf "\n\n"

echo "Test PATCH: Oka occupies room 1"
curl -i -u "admin:secret" -H "Content-type: application/json" -X PATCH http://127.0.0.1:5000/rooms/availability -d '{"1":{"available":"no", "user":"oka"}}'
printf "\n\n"

echo "Test GET: Check availability of all rooms (updated x1)"
curl http://127.0.0.1:5000/rooms/availability
printf "\n\n"

echo "Test PUT: Natalie leaves room 2"
curl -i -u "admin:secret" -H "Content-type: application/json" -X PUT http://127.0.0.1:5000/rooms/availability -d '{"2":{"available":"yes", "user":"NONE"}}'
printf "\n\n"

echo "Test GET: Check availability of all rooms (updated x2)"
curl http://127.0.0.1:5000/rooms/availability
printf "\n\n"

echo "Test PATCH: Liying tries to occupy room 3 without specifying authentication credentials"
curl -i -H "Content-type: application/json" -X PATCH http://127.0.0.1:5000/rooms/availability -d '{"3":{"available":"no", "user":"liying"}}'
printf "\n\n"

echo "Test GET: Check availability of all rooms (not updated)"
curl http://127.0.0.1:5000/rooms/availability
printf "\n\n"


# Message dashboard: GET, POST & DELETE requests

# Send messages over to add them to the messages dashboard and getting all messages from the dashboard. Admin can delete messages
# Order of requests: get messages, liying posts message (json), get messages, istd posts message (json), get messages,
#	liying posts message (text), get messages, liying posts message (binary), get messages, istd deletes liying's rude last message
echo "Test GET: Get all messages (initial state)"
curl http://127.0.0.1:5000/messages
printf "\n\n"

echo "Test POST: Liying sends a message in json format"
curl -i -H "Content-type: application/json" -X POST http://127.0.0.1:5000/messages -d '{"user":"liying", "message":"Can we have more rooms?"}'
printf "\n\n"

echo "Test GET: Getting all messages from dashboard (updated x1)"
curl http://127.0.0.1:5000/messages
printf "\n\n"

echo "Test POST: ISTD sends a message in json format"
curl -i -H "Content-type: application/json" -X POST http://127.0.0.1:5000/messages -d '{"user":"istd", "message":"We do not have enough space to build more rooms."}'
printf "\n\n"

echo "Test GET: Getting all messages from dashboard (updated x2)"
curl http://127.0.0.1:5000/messages
printf "\n\n"

echo "Test POST: Liying sends a message in text format"
curl -i -H "Content-type: text/plain" -X POST http://127.0.0.1:5000/messages --data "Why no space?"
printf "\n\n"

echo "Test GET: Getting all messages from dashboard (updated x3)"
curl http://127.0.0.1:5000/messages
printf "\n\n"

echo "Test POST: Liying tries to send a message in binary format"
curl -i -H "Content-type: applcation/octet-stream" -X POST http://127.0.0.1:5000/messages --data-binary @message.bin
printf "\n\n"

echo "Test GET: Getting all messages from dashboard (not updated)"
curl http://127.0.0.1:5000/messages
printf "\n\n"

echo "Test DELETE: ISTD deletes liying's last message"
curl -i -u "admin:secret" -X DELETE http://127.0.0.1:5000/messages?index=4
printf "\n\n"

echo "Test: GET: Getting all messages from dashboard (updated x4)"
curl http://127.0.0.1:5000/messages
printf "\n\n"
