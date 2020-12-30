import json
from devices import Devices




devices_list = dict()
try:
    with open('config.json') as f:
        print('config.json detected !  : parsing config.json....')
        try:
            data = json.load(f)
            ####### CREDENTIALS TYDOM            
            TYDOM_MAC = data['TYDOM_MAC'] #MAC Address of Tydom Box
            if data['TYDOM_IP'] != '':
                TYDOM_IP = data['TYDOM_IP'] #, 'mediation.tydom.com') # Local ip address, default to mediation.tydom.com for remote connexion if not specified

            TYDOM_PASSWORD = data['TYDOM_PASSWORD'] #Tydom password

            ####### CREDENTIALS MQTT
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
                print("traduction de {} : {}".format(id,devices_list[id]))
    

        except Exception as e:
            print('Parsing error', e)

except FileNotFoundError :
    print("No config.json..")