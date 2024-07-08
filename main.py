# -*- coding: utf-8 -*-
# @Time     :2023/12/26 18:08
# @Author   :ym
# @File     :combined_server.py
# @Software :PyCharm

import asyncio
import random
import ssl
import json
import time
import uuid
import threading
import requests
from flask import Flask
import websockets
from loguru import logger
from keep_alive import keep_alive

keep_alive()

NP_TOKEN = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMjUxODM2MTk2MjMzOTM2ODk2IiwiaWF0IjoxNzIwMjU1OTk0LCJleHAiOjE3MjE0NjU1OTR9.Ks2xI3NgtDe7VQlfRajShJn-rD47GFx3d2U0vsMM23DV4t-D_GEWisGZtP7Lj00ak-qQnWCxH_fH71wLv15oyg'
WEBSOCKET_URL_2 = "wss://nw.nodepay.ai:4576/websocket"
RETRY_INTERVAL = 60000  # in milliseconds
PING_INTERVAL = 10000  # in milliseconds

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + NP_TOKEN
}

response = requests.get("https://api.nodepay.ai/api/network/device-networks?page=0&size=10&active=false", headers=headers)
out = response.json()
USER_ID_2 = out['data'][0]['user_id']

async def connect_to_wss_1(user_id):
    device_id = str(uuid.uuid4())
    logger.info(f"Device ID for WebSocket 1: {device_id}")
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            async with websockets.connect(uri, ssl=ssl_context, extra_headers=custom_headers,
                                          server_hostname=server_hostname) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(f"WebSocket 1 send: {send_message}")
                        await websocket.send(send_message)
                        await asyncio.sleep(20)

                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"WebSocket 1 receive: {message}")
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "2.5.0"
                            }
                        }
                        logger.debug(f"WebSocket 1 auth response: {auth_response}")
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(f"WebSocket 1 pong response: {pong_response}")
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(f"WebSocket 1 error: {e}")

async def call_api_info(token):
    return {
        "code": 0,
        "data": {
            "uid": USER_ID_2,
        }
    }

async def connect_to_wss_2(token, reconnect_interval=RETRY_INTERVAL, ping_interval=PING_INTERVAL):
    browser_id = str(uuid.uuid4())
    logger.info(f"Browser ID for WebSocket 2: {browser_id}")

    retries = 0

    while True:
        try:
            async with websockets.connect(WEBSOCKET_URL_2) as websocket:
                logger.info("Connected to WebSocket 2")
                retries = 0

                async def send_ping(guid, options={}):
                    payload = {
                        "id": guid,
                        "action": "PING",
                        **options,
                    }
                    await websocket.send(json.dumps(payload))

                async def send_pong(guid):
                    payload = {
                        "id": guid,
                        "origin_action": "PONG",
                    }
                    await websocket.send(json.dumps(payload))

                async for message in websocket:
                    data = json.loads(message)

                    if data["action"] == "PONG":
                        await send_pong(data["id"])
                        await asyncio.sleep(ping_interval / 1000)
                        await send_ping(data["id"])

                    elif data["action"] == "AUTH":
                        api_response = await call_api_info(token)
                        if api_response["code"] == 0 and api_response["data"]["uid"]:
                            user_info = api_response["data"]
                            auth_info = {
                                "user_id": user_info["uid"],
                                "browser_id": browser_id,
                                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "extension_version",
                                "token": token,
                                "origin_action": "AUTH",
                            }
                            await send_ping(data["id"], auth_info)
                        else:
                            logger.error("Failed to authenticate")

        except Exception as e:
            logger.error(f"WebSocket 2 connection error: {e}")
            retries += 1
            logger.info(f"Retrying in {reconnect_interval / 1000} seconds...")
            await asyncio.sleep(reconnect_interval / 1000)

# Flask application
app = Flask(__name__)

@app.route('/')
def index():
    return "Hello World!"

def run_flask():
    app.run(debug=True)

# Main function to run both WebSocket connections
async def main():
    user_id_1 = '2hxta7lntWJzgQYqjNqOHt7Ww6T'
    task1 = connect_to_wss_1(user_id_1)
    task2 = connect_to_wss_2(NP_TOKEN)

    await asyncio.gather(task1, task2)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Run the main function in the main thread
if __name__ == '__main__':
    asyncio.run(main())
