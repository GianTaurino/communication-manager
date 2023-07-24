# Server (communication-manager)
import socket

import paho.mqtt.client as paho
import sys

import http.client
import json

from tinydb import TinyDB

TCP_IP = '169.254.222.189'  # server socket IP
TCP_PORT = 5005
BUFFER_SIZE = 1024

TEAM_ID = 1

MQTT_BROKER = "192.168.1.9"
MQTT_PORT = 1883
TOPIC = "worksite/team_" + str(TEAM_ID)

HTTP_SERVER = "192.168.1.15"
HTTP_PORT = 8000


def communication_manager(data):
    j_data = json.loads(data)

    new_danger = {
        "risk_uuid": j_data["uuid"],
        "team_id": TEAM_ID,
        "date": j_data["date-time"]
    }

    # MQTT notification
    client = paho.Client()
    if client.connect(host=MQTT_BROKER, port=MQTT_PORT, keepalive=60) == 0:
        print('\nPublishing to the broker')
        msg = "Danger detected around machine " + str(TEAM_ID)
        client.publish(topic=TOPIC, payload=msg)
        # time.sleep(2)
        print('Disconnected from broker')
    else:
        print("Could not connect to MQTT broker")
        sys.exit(-1)

    # Local storage
    db = TinyDB('db_team' + str(TEAM_ID) + '.json')
    db.insert(new_danger)
    print('\nLocal storage updated')

    # Central storage (HTTP server)
    try:
        HTTPConnection = http.client.HTTPConnection(HTTP_SERVER, HTTP_PORT)
        print('\nConnecting to HTTP server...')
        json_data = json.dumps(new_danger)
        HTTPConnection.request('POST', '/registerDanger', json_data)
        response = HTTPConnection.getresponse()
        print('HTTP POST: ', response.status, response.reason)
        HTTPConnection.close();
        print('Disconneted from HTTP server.\n')
    except:
        print('Could not connect to HTTP server')


while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    try:
        conn, addr = s.accept()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt")
        exit()
    # print ('Connection address:', addr)
    print('\n-----------------------')
    print('Danger detected')
    while 1:
        msg = conn.recv(BUFFER_SIZE)
        if not msg: break
        data = msg.decode('utf-8')
        jdata = json.loads(data)

        print("uuid: ", jdata["uuid"])
        print("date: ", jdata["date-time"])

        with open("/home/pi/Desktop/GattServer/detection.json", "w") as outfile:
            outfile.write(data)
        conn.send(msg)  # echo
        communication_manager(data)
    conn.close()