import asyncio
import time
import json
import socket
import sys
import logging
from datetime import datetime
from gmqtt import Client as MQTTClient


# Globals
####################################### MQTT
from light import Light
from electric import Electric

tydom_topic = "domoticz/out"
logger_info = logging.getLogger('tydmqttdom')
hostname = socket.gethostname()

# STOP = asyncio.Event()
class MQTT_Domo():

    def __init__(self, broker_host, port, user, password, mqtt_ssl, home_zone=1, night_zone=2, tydom = None, tydom_alarm_pin = None, devices = None):
        self.broker_host = broker_host
        self.port = port
        self.user = user
        self.password = password
        self.ssl = mqtt_ssl
        self.tydom = tydom
        self.tydom_alarm_pin = tydom_alarm_pin
        self.mqtt_client = None
        self.home_zone = home_zone
        self.night_zone = night_zone
        self.devices = {value : key for (key, value) in devices.items()}

    async def connect(self):

        try:
            
            logger_info.info('Attempting MQTT connection...')
            logger_info.info('MQTT host : %s', self.broker_host)
            logger_info.info('MQTT user : %s', self.user)
            adress = hostname+str(datetime.fromtimestamp(time.time()))
            # print(adress)

            client = MQTTClient(adress)
            # print(client)

            client.on_connect = self.on_connect
            client.on_message = self.on_message
            client.on_disconnect = self.on_disconnect
            # client.on_subscribe = self.on_subscribe

            client.set_auth_credentials(self.user, self.password)
            await client.connect(self.broker_host, self.port, self.ssl)

            self.mqtt_client = client
            return self.mqtt_client

        except Exception as e:
            logger_info.info("MQTT connection Error : {}".format(e))
            logger_info.info('MQTT error, restarting in 8s...')
            await asyncio.sleep(8)
            await self.connect()


    def on_connect(self, client, flags, rc, properties):
        
        try:
            logger_info.info("Subscribing to : {}".format(tydom_topic))
            # client.subscribe('homeassistant/#', qos=0)
            client.subscribe(tydom_topic, qos=0)
        except Exception as e:
            logger_info.info("Error on connect : {}".format(e))
            

    async def on_message(self, client, topic, payload, qos, properties):

        # Message MQTT en provenance de domoticz        
        if ('domoticz') in str(topic):
            value = json.loads(payload)          
            if "switchType" in value and value["switchType"] == "Selector":
                if (value["idx"] in self.devices):
                        device_id = self.devices[value["idx"]]
                        endpoint_id = self.devices[value["idx"]]
                        thermicLevel = value["svalue1"]
                        #logger_info.info('MQTT client debug  -- idxc {} value["idx"]  {} '.format(value["idx"],device_id))
                        logger_info.info("ThermicLevel {} for id : {}".format( thermicLevel,device_id))
                        # laisser le travail de traduction du thermiclevel à Electric
                        await Electric.put_thermicLevel(tydom_client=self.tydom, device_id=device_id, light_id=endpoint_id, thermiclevel=value["svalue1"])
                                
        elif ('update' in str(topic)):
#        if "update" in topic:
            #logger_info.info('Incoming MQTT update request : ', topic, payload)
            await self.tydom.get_data()
        elif ('kill' in str(topic)):
#        if "update" in topic:
            logger_info.info("Incoming MQTT kill request : {}".format( topic, payload))
            logger_info.info('Exiting...')
            sys.exit()
        elif (topic == "/tydom/init"):
            #logger_info.info('Incoming MQTT init request : ', topic, payload)
            await self.tydom.connect()
        elif 'set_levelCmd' in str(topic):
            #logger_info.info('Incoming MQTT set_positionCmd request : ', topic, payload)
            value = str(payload).strip('b').strip("'")

            get_id = (topic.split("/"))[2]  # extract ids from mqtt
            device_id = (get_id.split("_"))[0]  # extract id from mqtt
            endpoint_id = (get_id.split("_"))[1]  # extract id from mqtt

            #logger_info.info(str(get_id), 'levelCmd', value)
            await Light.put_levelCmd(tydom_client=self.tydom, device_id=device_id, light_id=endpoint_id,
                                        levelCmd=str(value))


        elif ('set_level' in str(topic)) and not ('set_levelCmd' in str(topic)):

            #logger_info.info('Incoming MQTT set_position request : ', topic, json.loads(payload))
            value = json.loads(payload)
            # print(value)
            get_id = (topic.split("/"))[2]  # extract ids from mqtt
            device_id = (get_id.split("_"))[0]  # extract id from mqtt
            endpoint_id = (get_id.split("_"))[1]  # extract id from mqtt

            await Light.put_level(tydom_client=self.tydom, device_id=device_id, light_id=endpoint_id,
                                     level=str(value))
        else:
            pass

    def on_disconnect(self, client, packet, exc=None):
        logger_info.info('MQTT Disconnected !')
        logger_info.info("##################################")
        # self.connect()
        

    def on_subscribe(self, client, mid, qos):
        logger_info.info("MQTT is connected and suscribed ! =)", client)
        try:
            pyld = str(datetime.fromtimestamp(time.time()))
            client.publish('domoticz/in/tydom/last_clean_startup', pyld, qos=1, retain=True)
        except Exception as e:
            logger_info.info("on subscribe error : ", e)


