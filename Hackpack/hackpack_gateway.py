#!/usr/bin/env python

import argparse
import json
import logging
import threading
import websocket

global_things = {
    'ADMIN_PASS': None,
    'SENSORS'   : {},
}

def receive_message(ws, message):
    data = json.loads(message)
    global_things['SENSORS'][ws][1].append(data)
    data = {'sensor': global_things['SENSORS'][ws][0], 'data': data}
    logged_message = json.dumps(data)
    logging.info(logged_message)
    print(logged_message)

def receive_error(ws, error):
    print("Error: {}".format(error))

def connection_closed(ws):
    print("Connection closed.")

def open_connection(ws):
    def run():
        ws.close()
    threading.Thread(target=run)

def create_sensor_connection(sensor_url):
    ws = websocket.WebSocketApp(
        sensor_url,
        on_message  = receive_message,
        on_error    = receive_error,
        on_close    = connection_closed
    )
    ws.on_open = open_connection
    try:
        global_things['SENSORS'][ws] = (len(global_things['SENSORS']), [])
        ws.run_forever()
    except:
        print("Could not connect to websocket: {}".format(sensor_url))

def main(admin_pass, sensors):
    logging.basicConfig(filename='gateway.log', level=logging.DEBUG)
    global_things['ADMIN_PASS'] = admin_pass

    print("Admin Pass: {}".format(global_things['ADMIN_PASS']))
    for number, sensor in enumerate(sensors):
        print("Sensor {}: {}".format(number, sensor))

    websocket.enableTrace(True)
    threads = [threading.Thread(target=create_sensor_connection, args=[sensor]) for sensor in sensors]
    for thread in threads:
        thread.start()
    print("All threads started.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('admin_pass', help="Server administrative password for posting to /api/readings.")
    parser.add_argument('sensors', nargs='+', help="Sensor websocket endpoints, e.g. ws://localhost:8080/ws")
    args = parser.parse_args()

    main(args.admin_pass, args.sensors)
