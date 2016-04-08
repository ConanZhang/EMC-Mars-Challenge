#!/usr/bin/env python

import argparse
import json
import threading
import time
import websocket

def on_message(ws, message):
    data = json.loads(message)
    print("{}: Solar Flare: {}, Temperature: {}, Radiation: {}".format(
        data['stamp'],
        data['solarFlare'],
        data['temperature'],
        data['radiation']
    ))

def on_error(ws, error):
    print("Error: {}".format(error))

def on_close(ws):
    print("Connection Closed")

def on_open(ws):
    def run():
        ws.close()
    threading.Thread(target=run)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('address', help="Websocket connection address")
    args = parser.parse_args()

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(args.address, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    try:
        ws.run_forever()
    except KeyboardInterrupt:
        print("Terminating")
