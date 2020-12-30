import json
import time
from datetime import datetime


light_command_topic = "electric/tydom/{id}/set_levelCmd"
light_config_topic = "electric/tydom/{id}/config"
light_level_topic = "electric/tydom/{id}/current_level"


light_set_level_topic = "electric/tydom/{id}/set_level"
light_attributes_topic = "electric/tydom/{id}/attributes"


class Light:
    def __init__(self, tydom_attributes, set_level=None, mqtt=None):
        
        self.attributes = tydom_attributes
        self.device_id = self.attributes['device_id']
        self.endpoint_id = self.attributes['endpoint_id']
        self.id = self.attributes['id']
        self.name = self.attributes['light_name']
        try:
            self.current_level = self.attributes['thermicLevel']
        except Exception as e:
            print(e)
            self.current_level = None
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
        self.device['model'] = 'Lumiere'
        self.device['name'] = self.name
        self.device['identifiers'] = self.id

        self.config_topic = light_config_topic.format(id=self.id)
        self.config = {}
        self.config['name'] = self.name        
        self.config['state_topic'] = light_level_topic.format(id=self.id)
        self.config['json_attributes_topic'] = light_attributes_topic.format(id=self.id)
        self.config['device'] = self.device
        print(self.config)

        if (self.mqtt != None):
            self.mqtt.mqtt_client.publish(self.config_topic, json.dumps(self.config), qos=0)

    async def update(self):
        await self.setup()
###############################################
        #try:
        #    await self.update_sensors()
        #except Exception as e:
        #    print("light sensors Error :")
        #    print(e)
###############################################

        self.level_topic = light_level_topic.format(id=self.id, current_level=self.current_level)
        
        if (self.mqtt != None):
            ###############################################
            self.mqtt.mqtt_client.publish(self.level_topic, self.current_level, qos=0, retain=True)
            self.mqtt.mqtt_client.publish(self.config['json_attributes_topic'], self.attributes, qos=0)
            ################################################
        print("light created / updated : ", self.name, self.id, self.current_level)

       

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
        print(light_id, 'level', level)
        if not (level == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'level', level)

    async def put_levelCmd(tydom_client, device_id, light_id, levelCmd):
        print(device_id, ' ',light_id, ' levelCmd ', levelCmd)
        if not (levelCmd == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'levelCmd', levelCmd)
    async def put_thermicLevel(tydom_client, device_id, light_id, thermiclevel):
        print(device_id, ' ',light_id, ' thermiclevel ', thermiclevel)
        if not (thermiclevel == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'thermicLevel', thermiclevel)
