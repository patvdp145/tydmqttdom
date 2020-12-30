import json
import time
import logging
from datetime import datetime



electric_config_topic = "domoticz/in"
electric_level_topic = "domoticz/in"
logger_info = logging.getLogger('tydmqttdom')
tydom_to_domoticz = {"STOP":0,"ANTI_FROST":10,"ECO":20,"COMFORT":30}
domoticz_to_tydom = {str(value) : key for (key, value) in tydom_to_domoticz.items()}

class Electric:
    def __init__(self, tydom_attributes, set_level=None, mqtt=None):
        
        self.attributes = tydom_attributes
        self.device_id = self.attributes['device_id']
        self.endpoint_id = self.attributes['endpoint_id']
        self.id = self.attributes['id']
        self.idx = self.attributes['idx'] # idx de domoticz
        self.name = self.attributes['electric_name']
        self.current_level = tydom_to_domoticz[self.attributes['thermicLevel']]
        self.current_tydom_level = self.attributes['thermicLevel']
        
        
          
        self.set_level = set_level
        self.mqtt = mqtt

    # def id(self):
    #     return self.id

    # def name(self):
    #     return self.name

    # def current_level(self):
    #     return self.current_level

    # def set_level(self):
    #     return self.set_level

    # def attributes(self):
    #     return self.attributes

    async def setup(self):
        self.device = {}
        self.device['manufacturer'] = 'Delta Dore'
        self.device['model'] = 'Radiateur'
        self.device['name'] = self.name
        self.device['identifiers'] = self.id
        self.config_topic = electric_config_topic
        self.config = {}
        self.config['command'] = 'switchlight'
        self.config['idx'] = self.idx
        self.config['switchcmd'] = 'Set Level'        
        self.config['level'] = self.current_level
        
        # source du doublement des messages MQTT quand la commande vient de Tydom. Double emploi avec le
        # message publié par update ci-dessous car le canal domoticz est le même. Voir pour publier des infos différentes  dans les 2 canaux. 
        
#        if (self.mqtt != None):
#            self.mqtt.mqtt_client.publish(self.config_topic, json.dumps(self.config), qos=0)

    async def update(self):
        await self.setup()
        # canal de publication mqtt. Ici: domoticz/in
        self.level_topic = electric_level_topic
        if (self.mqtt != None):
            self.mqtt.mqtt_client.publish(self.level_topic, json.dumps(self.config), qos=0, retain=True)
        logger_info.info("electric created / updated :{} : {}: {} :{}".format(self.name, self.id, self.current_level,self.current_tydom_level))

       

    async def update_sensors(self):
        # print('test sensors !')
        for i, j in self.attributes.items():

            if not i == 'device_type' or not i == 'id':
                new_sensor = None
####################################################
#                new_sensor = sensor(elem_name=i, tydom_attributes_payload=self.attributes, attributes_topic_from_device=self.config['json_attributes_topic'], mqtt=self.mqtt)
#                await new_sensor.update()
#################################################### 

    async def put_level(tydom_client, device_id, light_id, level):
        #print(light_id, 'level', level)
        if not (level == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'level', level)

    async def put_levelCmd(tydom_client, device_id, light_id, levelCmd):
        #print(device_id, ' ',light_id, ' levelCmd ', levelCmd)
        if not (levelCmd == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'levelCmd', levelCmd)
    
    # put_thermicLevel n'est appelé que par mqtt_client.py qui a traduit la valeur du thermicLevelde       domoticz en valeur attendue par Tydom
    
    async def put_thermicLevel(tydom_client, device_id, light_id, thermiclevel):
        #print(device_id, ' ',light_id, ' thermiclevel ', thermiclevel)
        if not (thermiclevel == ''):
            thermicLevel = domoticz_to_tydom[thermiclevel]
            await tydom_client.put_devices_data(device_id, light_id, 'thermicLevel', thermicLevel)
