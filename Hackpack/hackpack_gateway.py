#!/usr/bin/env python

import argparse
import json
import logging
import requests
import threading
import time
import websocket

global_things = {
    'ADMIN_PASS': None,
    'SENSORS'   : {},
    'CONTROLLER': None,
}

def average(*numbers):
    result = 0
    for number in numbers:
        result += number
    return float(result) / float(len(numbers))

def post_data(data):
    auth_header = {'X-Auth-Token': global_things['ADMIN_PASS']}
    response = requests.post(global_things['CONTROLLER'], headers=auth_header, data=json.dumps(data))
    if response.status_code == 200:
        return
    elif response.status_code == 400:
        raise RuntimeError("Could not post data.")
    else:
        raise RuntimeError("Unknown issue posting data.")

def consume_data():
    data = []
    for sensor in global_things['SENSORS'].values():
        try:
            data.append(sensor[1].pop(0))
        except IndexError:
            continue
    temp_mean  = average(*[data[x]['temperature'] for x in range(len(data))])
    rad_mean   = int(average(*[data[x]['radiation'] for x in range(len(data))]))
    flare_mean = average(*[data[x]['solarFlare'] for x in range(len(data))])
    flare_mean = True if flare_mean > len(global_things['SENSORS']) / 2 else False
    result = {
        'temperature'   : temp_mean,
        'radiation'     : rad_mean,
        'solarFlare'    : flare_mean
    }
    post_data(result)
    logging.info(json.dumps({'average': True, 'data': result}))

def receive_message(ws, message):
    data = json.loads(message)
    global_things['SENSORS'][ws][1].append(data)
    data = {'average': False, 'data': {'sensor': global_things['SENSORS'][ws][0], 'data': data}}
    logged_message = json.dumps(data)
    logging.info(logged_message)

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

def main(controller_url, admin_pass, sensors):
    logging.basicConfig(filename='gateway.log', level=logging.DEBUG)
    global_things['CONTROLLER'] = controller_url
    global_things['ADMIN_PASS'] = admin_pass

    print("Admin Pass: {}".format(global_things['ADMIN_PASS']))
    for number, sensor in enumerate(sensors):
        print("Sensor {}: {}".format(number, sensor))

    websocket.enableTrace(True)
    threads = [threading.Thread(target=create_sensor_connection, args=[sensor]) for sensor in sensors]
    for thread in threads:
        thread.start()

    time.sleep(5)
    try:
        while True:
            consume_data()
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('controller_url', help="The Game Controller readings url, e.g. localhost:8080/api/readings")
    parser.add_argument('admin_pass', help="Server administrative password for posting to /api/readings")
    parser.add_argument('sensors', nargs='+', help="Sensor websocket endpoints, e.g. ws://localhost:8080/ws")
    args = parser.parse_args()

    main(args.controller_url, args.admin_pass, args.sensors)
