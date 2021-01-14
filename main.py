#!/usr/bin/env python3
# Exceptions voir : https://docs.python.org/fr/3.5/tutorial/errors.html
import asyncio
import time
from datetime import datetime
import os
import sys
import json
import socket
import websockets
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import sdnotify

from mqtt_client import MQTT_Domo
from tydomConnector import TydomWebSocketClient
from tydomMessagehandler import TydomMessageHandler
#


formatter_info = logging.Formatter("%(asctime)s -- %(name)s -- %(filename)s -- %(message)s")
logger_info = logging.getLogger("tydmqttdom")
handler_info = logging.handlers.TimedRotatingFileHandler("tydmqttdom.log", when="d", interval=1,backupCount=10, encoding="utf-8")
handler_info.setFormatter(formatter_info)
logger_info.setLevel(logging.INFO)
logger_info.addHandler(handler_info)

n = sdnotify.SystemdNotifier()
n.notify("READY=1")


logging.info('STARTING TYDMQTTDOM')

logging.info('Dectecting environnement......')


# DEFAULT VALUES
loop = asyncio.get_event_loop()
TYDOM_MAC='001A25xxxx'
TYDOM_PASSWORD='xxxxxxx'
TYDOM_IP = '192.168.1.xx'
#TYDOM_IP = 'mediation.tydom.com'
MQTT_USER = ''
MQTT_PASSWORD = ''
MQTT_HOST = '192.168.1.xx'
MQTT_PORT = 1883
MQTT_SSL = False
TYDOM_ALARM_PIN = None
TYDOM_ALARM_HOME_ZONE = 1
TYDOM_ALARM_NIGHT_ZONE = 2


try:
#    with open('/home/pi/tydmqttdom/config.json') as f:
    with open('config.json') as f:
        logger_info.info('config.json detected !  : parsing config.json....')
        n.notify("WATCHDOG=1")
        try:
            data = json.load(f)
            
            ####### CREDENTIALS TYDOM
            TYDOM_MAC = data['TYDOM_MAC'] #MAC Address of Tydom Box
            if data['TYDOM_IP'] != '':
                TYDOM_IP = data['TYDOM_IP'] #, 'mediation.tydom.com') # Local ip address, default to                                                     mediation.tydom.com for remote connexion if not specified
            TYDOM_PASSWORD = data['TYDOM_PASSWORD'] #Tydom password

            # CREDENTIALS MQTT
            
            if data['MQTT_HOST'] != '':
                MQTT_HOST = data['MQTT_HOST']
            
            MQTT_USER = data['MQTT_USER']
            MQTT_PASSWORD = data['MQTT_PASSWORD']

            if data['MQTT_PORT'] != 1883:
                MQTT_PORT = data['MQTT_PORT']

            if (data['MQTT_SSL'] == 'true') or (data['MQTT_SSL'] == True) :
                MQTT_SSL = True
                
            devices_list = data["devices"]            
            for id in devices_list:
                logger_info.info("traduction des devices pour domoticz {} : {}".format(id,devices_list[id]))

        except Exception as e:
            logger_info.info("Parsing error{}".format(e))

except FileNotFoundError :
    logger_info.info("No config.json..")
    ####### CREDENTIALS TYDOM
    TYDOM_MAC = os.getenv('TYDOM_MAC') #MAC Address of Tydom Box
# Local ip address, default to mediation.tydom.com for remote connexion if not specified
    TYDOM_IP = os.getenv('TYDOM_IP', 'mediation.tydom.com') 
    TYDOM_PASSWORD = os.getenv('TYDOM_PASSWORD') #Tydom password
    TYDOM_ALARM_PIN = os.getenv('TYDOM_ALARM_PIN')
    TYDOM_ALARM_HOME_ZONE = os.getenv('TYDOM_ALARM_HOME_ZONE', 1)
    TYDOM_ALARM_NIGHT_ZONE = os.getenv('TYDOM_ALARM_NIGHT_ZONE', 2)
    
    ####### CREDENTIALS MQTT
    MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
    MQTT_USER = os.getenv('MQTT_USER')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
    MQTT_PORT = os.getenv('MQTT_PORT', 1883) #1883 #1884 for websocket without SSL
    MQTT_SSL = os.getenv('MQTT_SSL', False)

# La liste des devices (dummy mqtt) de domoticz est passée en paramètre au module MQTT

tydom_client = TydomWebSocketClient(mac=TYDOM_MAC, host=TYDOM_IP, password=TYDOM_PASSWORD, alarm_pin=TYDOM_ALARM_PIN)
domo = MQTT_Domo(broker_host=MQTT_HOST, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD, mqtt_ssl=MQTT_SSL, home_zone=TYDOM_ALARM_HOME_ZONE, night_zone=TYDOM_ALARM_NIGHT_ZONE, tydom=tydom_client,devices=devices_list)


def loop_task():
    logger_info.info('Starting main loop_task')

    loop.run_until_complete(domo.connect())

    tasks = [
        listen_tydom_forever(tydom_client)
    ]

    loop.run_until_complete(asyncio.wait(tasks))


async def listen_tydom_forever(tydom_client):
    '''
        Connect, then receive all server messages and pipe them to the handler, and reconnects if needed
    '''

    while True:
        await asyncio.sleep(0)
        n.notify("WATCHDOG=1")
        # # outer loop restarted every time the connection fails
        try:
            await tydom_client.connect()
            logger_info.info("Tydom Client is connected to websocket and ready !")
            await tydom_client.setup()

            while True:
            # listener loop
                try:
                    incoming_bytes_str = await asyncio.wait_for(tydom_client.connection.recv(), timeout=tydom_client.refresh_timeout)
                    #print('<<<<<<<<<< Receiving from tydom_client...')
                    #print(incoming_bytes_str)
                    n.notify("WATCHDOG=1")

                except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
                    logger_info.info("erreur websockets{}".format(e))
                    try:
                        pong = tydom_client.post_refresh()
                        await asyncio.wait_for(pong, timeout=tydom_client.refresh_timeout)
                        # print('Ping OK, keeping connection alive...')
                        continue
                    except Exception as e:
                        logger_info.info('TimeoutError or websocket error - retrying connection in {} seconds...'.format(tydom_client.sleep_time))
                        logger_info.info("erreur websockets{}".format(e))
                        await asyncio.sleep(tydom_client.sleep_time)
                        break
                #print('Server said > {}'.format(incoming_bytes_str))
                #incoming_bytes_str
# La liste des devices (dummy mqtt) de domoticz est passée en paramètre au module TydomMessageHandler                        
                handler = TydomMessageHandler(incoming_bytes=incoming_bytes_str, tydom_client=tydom_client, mqtt_client=domo,devices=devices_list)
                try:
                    await handler.incomingTriage()
                except Exception as e:
                    logger_info.info("Tydom Message Handler exception :{}".format(e))
                                
        except socket.gaierror:
            logger_info.info('Socket error - retrying connection in {} sec (Ctrl-C to quit)'.format(tydom_client.sleep_time))
            await asyncio.sleep(tydom_client.sleep_time)
            continue
        except ConnectionRefusedError:
            logger_info.info('Nobody seems to listen to this endpoint. Please check the URL.')
            logger_info.info('Retrying connection in {} sec (Ctrl-C to quit)'.format(tydom_client.sleep_time))
            await asyncio.sleep(tydom_client.sleep_time)
            continue
        except KeyboardInterrupt:
            logger_info.info('Exiting KeyboardInterrupt')
            sys.exit()


if __name__ == '__main__':
    loop_task()
