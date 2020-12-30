#from cover import Cover
from light import Light
from electric import Electric
# alarm_control_panel import Alarm
# from sensor import Sensor

from http.server import BaseHTTPRequestHandler
from http.client import HTTPResponse
#

#
import urllib3
from io import BytesIO
import json
import sys
import re
import logging

# Dicts
#deviceLightKeywords = ['thermicLevel','temperature','thermicDefect','battDefect','loadDefect','cmdDefect','onPresenceDetected','onDusk']
deviceElectricKeywords = ['thermicLevel']
logger_info = logging.getLogger('tydmqttdom')

# Device dict for parsing
device_name = dict()
device_endpoint = dict()
device_type = dict()
# Thanks @Max013 !



class TydomMessageHandler():


    def __init__(self, incoming_bytes, tydom_client, mqtt_client,devices):
            # print('New tydom incoming message')
            self.incoming_bytes = incoming_bytes
            self.tydom_client = tydom_client
            self.cmd_prefix = tydom_client.cmd_prefix
            self.mqtt_client = mqtt_client
            self.devices = devices

    async def incomingTriage(self):
        
        bytes_str = self.incoming_bytes   
        if self.mqtt_client == None: #If not MQTT client, return incoming message to use it with anything.
            return bytes_str
        else:
            incoming = None
            message_type = None
            
            # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            # print('RAW INCOMING :')
            # print(bytes_str)
            # print('RAW Décodé  :')
            # print(bytes_str.decode("utf-8"))
            # print('END RAW')
            # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            #    sys.exit() #Exit all to ensure systemd restart
            
            ########################################################
            
            fields = bytes_str.decode("utf-8").split("\r\n")
            end_parsing = False
            uri_found = False
            i = 0
            output = str()
            while not (end_parsing or uri_found):
                field = fields[i]
                if len(field) == 0 or field == '0':
                    end_parsing = True
                else:
                    matchObj = re.match('Uri-Origin: (.*)', field, re.M|re.I) 
                    if matchObj:                        
                        message_type = matchObj.group(1)
                        #print ("Type de message détecté : ",message_type)
                        uri_found = True
                    else:
                        matchObj = re.match('PUT (.*) HTTP/1.1', field, re.M|re.I) 
                        if matchObj:                        
                            message_type = 'PUT' + matchObj.group(1)
                            #print ("PUT Type de message détecté : ",message_type)
                            uri_found = True                        
                    output += field
                    i = i + 1
#            try:
            if message_type == '/refresh/all':
                pass
            elif message_type == '/info':
                pass
            elif message_type == 'PUT/devices/data' or message_type =='/devices/cdata':
                #print('PUT /devices/data message detected !')
                incoming = self.parse_put_response(bytes_str)
                await self.parse_response(incoming)
            elif message_type == '/devices/data' or message_type =='/devices/cdata':
                #print('/devices/data message detected !')
                response = self.response_from_bytes(bytes_str[len(self.cmd_prefix):])
                incoming = response.data.decode("utf-8")
                try:
                    await self.parse_response(incoming)
                except:
                    logger_info.info('RAW INCOMING ...')
                    #print(bytes_str)   
            elif message_type == '/configs/file':
                #pass
                response = self.response_from_bytes(bytes_str[len(self.cmd_prefix):])
                incoming = response.data.decode("utf-8")
                await self.parse_response(incoming)                
            else:
                pass
                #incoming = self.parse_put_response(bytes_str)
                #await self.parse_response(incoming)                
                    

#            try:
#                incoming = self.parse_put_response(bytes_str)
#                await self.parse_response(incoming)
#            except:
#                incoming = self.parse_put_response(bytes_str)
#                await self.parse_response(incoming)

    # Basic response parsing. Typically GET responses + instanciate covers and alarm class for updating data
    async def parse_response(self, incoming):
        data = incoming
        msg_type = None

        first = str(data[:40])
        parsed = json.loads(data)
        #print('parse_response --{}'.format( json.dumps(parsed, indent=2)))
        #print('FIRST : ', first)
        
        # Detect type of incoming data
        if (data != ''):
            if ("groups" in first):
                #logger_info.info('Incoming message type : groups config detected')
                msg_type = 'msg_config'
                parsed = json.loads(data)
                await self.parse_config_data(parsed=parsed)
            elif ("scenarios" in first):
                #logger_info.info('Incoming message type : config detected')
                msg_type = 'msg_config'
            elif ("moments" in first):
                #logger_info.info('Incoming message type : config detected')
                msg_type = 'msg_config'
            elif ("id" in first):
                #logger_info.info('Incoming message type : data detected')
                #print('parse_response on trouve id in first')
                msg_type = 'msg_data'
            elif ("endpoints" in first):
                #logger_info.info('Incoming message type : config detected')
                # une liste de tous les endpoints electric à décoder
                msg_type = 'msg_config'
                #print('parse_response on trouve endpoints in first')
                #pass
            elif ("date" in first):
                #logger_info.info('Incoming message type : config detected')
                msg_type = 'msg_config'
            elif ("doctype" in first):
                #logger_info.info('Incoming message type : html detected (probable 404)')
                msg_type = 'msg_html'
                #print(data)
            elif ("productName" in first):
                #logger_info.info('Incoming message type : Info detected')
                msg_type = 'msg_info'
                # print(data)        
            else:
                logger_info.info('Incoming message type : no type detected')
                #print(first)

            if not (msg_type == None):
                try:                    
                    if (msg_type == 'msg_config'):
                        parsed = json.loads(data)
                        await self.parse_config_data(parsed=parsed)
                        
                    elif (msg_type == 'msg_data'):
                        parsed = json.loads(data)
                        await self.parse_devices_data(parsed=parsed)
                    elif (msg_type == 'msg_html'):
                        logger_info.info("HTML Response ?")
                    elif (msg_type == 'msg_info'):
                        pass
                    else:
                        print()
                except Exception as e:
                    logger_info.info('Cannot parse response !')
                    if (e != 'Expecting value: line 1 column 1 (char 0)'):
                        logger_info.info("Erreur : {}".format(e))
            #logger_info.info('Incoming data parsed successfully !')
            return(0)

    async def parse_config_data(self, parsed):
        #print('Parse Config Data')
        for i in parsed["endpoints"]:
            # Get list of shutter
            # print(i)
            if i["last_usage"] == 'shutter' or i["last_usage"] == 'light' or i["last_usage"] == 'electric':
                #print('{} {} {}'.format(i["id_endpoint"],i["name"],i["last_usage"]))
                device_name[i["id_endpoint"]] = i["name"]
                device_name[i["id_device"]] = i["name"]
                device_type[i["id_device"]] = i["last_usage"]
                device_endpoint[i["id_device"]] = i["id_endpoint"]
                

        #print('Configuration updated')
        
        

    async def parse_devices_data(self, parsed):
        #print('parse_devices_data atteint ...', parsed)
          
        for i in parsed:
            if i["endpoints"][0]["error"] == 0:
                try:
                    attr_alarm = {}
                    attr_alarm_details = {}
                    attr_cover = {}
                    attr_cover_details = {}
                    
                    attr_light = {}
                    attr_light_details = {}
                    
                    attr_electric = {}
                    
                    device_id = i["id"]
                    name_of_id = self.get_name_from_id(device_id)
                    type_of_id = self.get_type_from_id(device_id)
                    #print('id - {} name - {} type - {}'.format(device_id,name_of_id,type_of_id))
                    for elem in i["endpoints"][0]["data"]:
                        endpoint_id = None

                        elementName = None 
                        elementValue = None
                        elementValidity = None

                        # Get full name of this id
                        # endpoint_id = i["endpoints"][0]["id"]

                        # Element name
                        elementName = elem["name"]
                        # Element value
                        elementValue = elem["value"]
                        elementValidity = elem["validity"]
                        print_id = None

                        if len(name_of_id) != 0:
                            print_id = name_of_id
                            endpoint_id = device_endpoint[device_id]
                        else:
                            print_id = device_id
                            endpoint_id = device_endpoint[device_id]
                        if type_of_id == 'electric':
                            #if elementName not in deviceElectricKeywords:
                            #   pass
                            if elementName in deviceElectricKeywords and elementValidity == 'upToDate':  # NEW METHOD
                                
                                for clef,valeur in self.devices.items():
                                    #print('{}-- valeur {} clef  {} '.format(endpoint_id,valeur,clef))
                                    if int(clef) == int(endpoint_id):
                                        attr_electric['idx'] = valeur
                                        
                                attr_electric['device_id'] = device_id
                                attr_electric['endpoint_id'] = endpoint_id
                                attr_electric['id'] = str(device_id) + '_' + str(endpoint_id)
                                attr_electric['electric_name'] = print_id
                                attr_electric['name'] = print_id
                                attr_electric['device_type'] = 'electric'
                                attr_electric[elementName] = elementValue
                                #print(attr_electric)
                except Exception as e:
                    logger_info.info("msg_data error in parsing : {}".format(e))

                if 'device_type' in attr_electric and attr_electric['device_type'] == 'electric':
                    new_electric = "electric_tydom_"+str(endpoint_id)
                    #Instanciation. la valeur du thermicLevel est celle de Tydom 
                    new_electric = Electric(tydom_attributes=attr_electric, mqtt=self.mqtt_client) 
                    await new_electric.update()
                # Get last known state (for alarm) # NEW METHOD
                elif 'device_type' in attr_alarm and attr_alarm['device_type'] == 'alarm_control_panel':
                    # print(attr_alarm)
                    state = None
                    sos_state = False
                    maintenance_mode = False
                    out = None
                    try:
                        logger_info.info('Alarme je passe')
                    except Exception as e:
                        logger_info.info("Error in alarm parsing : {}".format(e))
                        pass
                else:
                    pass


    # PUT response DIRTY parsing
    def parse_put_response(self, bytes_str):
        # TODO : Find a cooler way to parse nicely the PUT HTTP response
        resp = bytes_str[len(self.cmd_prefix):].decode("utf-8")
        fields = resp.split("\r\n")
        fields = fields[6:]  # ignore the PUT / HTTP/1.1
        end_parsing = False
        i = 0
        output = str()
        while not end_parsing:
            field = fields[i]
            if len(field) == 0 or field == '0':
                end_parsing = True
            else:
                output += field
                i = i + 2
        #print('output : ',output)
        parsed = json.loads(output)
        #print('dump de json :', json.dumps(parsed))
        return json.dumps(parsed)

    ######### FUNCTIONS

    def response_from_bytes(self, data):
        sock = BytesIOSocket(data)
        response = HTTPResponse(sock)
        response.begin()
        return urllib3.HTTPResponse.from_httplib(response)

    def put_response_from_bytes(self, data):
        request = HTTPRequest(data)

        return request

    def get_type_from_id(self, id):
        return(device_type[id])

    # Get pretty name for a device id
    def get_name_from_id(self, id):
        name = ""
        if len(device_name) != 0:
            name = device_name[id]
        return(name)
    def get_list_of_id(self):        
        for i in  len(device_name):
            name = device_name[id]
            #print('{} {} {}'.format(device_name[i],device_type[i],device_endpoint[i]))
        return(1)
    

class BytesIOSocket:
    def __init__(self, content):
        self.handle = BytesIO(content)

    def makefile(self, mode):
        return self.handle

class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = request_text
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message




