# TYDMQTTDOM

## Version française 
Petit module  python  permettant d'accéder à une Tydom 1.0 pour la gestion de radiateurs électriques via des RF 6600 FP.
Il ne s'agit pas d'un plugin domoticz mais d'un system service sous linux.


Je me suis plus que largement inspiré de :
 - https://github.com/mrwiwi/tydom2mqtt
 - https://github.com/cth35/tydom_python    


## Features
(voir tydom2mqtt et tydom_python )
 - Communication depuis et vers domoticz via mqtt
 - logging 
 - Watchdog avec sdnotify

## Requis
  - Python >= 3.5
 - websockets
 - logging
 - sdnotify

## Configuration

Utilisation d'un fichier de configuration json comme tydom2mqtt dans lequel on ajoute la traduction d'un "endpoint" tydom en device domoticz (voir devices).


```json
{
    "TYDOM_MAC": "001A25xxxxxx",
    "TYDOM_IP": "192.168.1.xxx",
    "TYDOM_PASSWORD":"xxxxxx",
    "MQTT_HOST": "192.168.1.xxx",
    "MQTT_USER": "",
    "MQTT_PASSWORD": "",
    "MQTT_PORT": 1883,
    "MQTT_SSL": false,
    "log_level": "info",
       "devices":
    { "160xxxxxx":502 ,
     "160xxxxxx":655 ,
     "160xxxxxx":656 }
    }
```

Version 2 de mosquitto, on doit mettre adresse du broker = 127.0.0.1 à moins qu'on utilise un fichier de configuration. 
voir :https://mosquitto.org/blog/2020/12/version-2-0-0-released/

## Utilisation
- associer  chaque  RF 6600 FP dans l'app Delta Dore (Ios ou Android)
- utiliser tydom_python avec get_configs_file (voir plus haut) pour récupérer les endpoint  id de chaque  RF 6600 FP
- Dans Domoticz :
  - créer un  dummy_MQTT (does nothing, use for virtual switches only)
  - créer un virtual sensor (switch type = selector) pour chaque radiateur (RF 6600 FP) avec les niveaux suivants :
	  * 0   = ARRET
      * 10 = HORS  GEL
      * 20 = ECO
      * 30 = CONFORT
- indiquer la traduction endpoint_id:domoticz_idx dans le fichier config.json
- créer le  system service :
<pre><code>
sudo nano /etc/systemd/system/tydmqttdom.service


[Unit]
Description=Python program

[Service]
# Note: setting PYTHONUNBUFFERED is necessary to see the output of this service in the journal
# See https://docs.python.org/2/using/cmdline.html#envvar-PYTHONUNBUFFERED
Environment=PYTHONUNBUFFERED=true

# Adjust this line to the correct path to test.py
ExecStart=/usr/bin/python3 /home/pi/tydmqttdom/main.py

Type=notify
WatchdogSec=30
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

</pre></code>
<pre><code>
systemctl enable tydmqttdom.service
systemctl start tydmqttdom.service

sudo systemctl status tydmqttdom.service
● tydmqttdom.service - Python program
   Loaded: loaded (/etc/systemd/system/tydmqttdom.service; enabled; vendor preset: enabled)
   Active: active (running) since Wed 2020-12-16 09:43:09 CET; 4 days ago
 Main PID: 13762 (python3)
    Tasks: 1 (limit: 2065)
   CGroup: /system.slice/tydmqttdom.service
           └─13762 /usr/bin/python3 /home/pi/tydmqttdom/main.py
 </pre></code>  

## MQTT

Le service écoute sur le topic domoticz/out et  transmet au tydom sur  domoticz/in

domoticz/in {"command": "switchlight", "idx": 656, "switchcmd": "Set Level", "level": 20}

## Logging

Un nouveau log est créé chaque jour:

<pre><code>
ls -l /var/log/tydmqttdom.log*
-rw-r--r-- 1 root root    3276 déc.  20 07:00 /var/log/tydmqttdom.log
-rw-r--r-- 1 root root   22111 déc.   9 07:00 /var/log/tydmqttdom.log.2020-12-08
-rw-r--r-- 1 root root   54037 déc.  10 12:43 /var/log/tydmqttdom.log.2020-12-09
-rw-r--r-- 1 root root  131937 déc.  11 08:58 /var/log/tydmqttdom.log.2020-12-10
-rw-r--r-- 1 root root    2398 déc.  12 13:08 /var/log/tydmqttdom.log.2020-12-11
</pre></code>

## Limitations

- le fichier config.json doit  etre dans  /home/pi/tydmqttdom (voir main.py)
- les logs sont stockés dans /var/log (idem)

## TODO

-  nettoyer le code 
- ajouter la gestion de volets roulants
- ajouter des arguments pour le paramétrage 


# tydmqttdom (english version)
Another simple python implementation to access Tydom gateway and electric heaters using RF 6600 FP.
It's not a domoticz plugin, it's a linux system service.
.

largely inspired by :

 - https://github.com/mrwiwi/tydom2mqtt
 - https://github.com/cth35/tydom_python    


# Features
(see tydom2mqtt and tydom_python)
 - Fully asynchronous (asyncio async/await)
 - Manage tydom push request through callback
 - Optional keep alive through ping command
 - Automatic reconnection on keep alive failure
 - Both ways communication with domoticz via mqtt
 - logging 
 - Watchdog with sdnotify

# Requirements
  - Python >= 3.5
 - websockets
 - logging
 - sdnotify

# Configuration

It  uses a json config file like tydom2mqtt in which I had to translate the tydom enpoint ids to domoticz's idx (devices)

```json
{
    "TYDOM_MAC": "001A25xxxxxx",
    "TYDOM_IP": "192.168.1.xxx",
    "TYDOM_PASSWORD":"xxxxxx",
    "MQTT_HOST": "192.168.1.xxx",
    "MQTT_USER": "",
    "MQTT_PASSWORD": "",
    "MQTT_PORT": 1883,
    "MQTT_SSL": false,
    "log_level": "info",
       "devices":
    { "160xxxxxx":502 ,
     "160xxxxxx":655 ,
     "160xxxxxx":656 }
    }
```
With version 2 of mosquitto, unless using a conf  file, broker address must be 127.0.0.1.
See :https://mosquitto.org/blog/2020/12/version-2-0-0-released/


# Getting started

- create/ associate each RF 6600 FP with the Delta Dore app
- use tydom\_python (use get\_configs_file) to get the endpoint ids.
- in Domoticz :
  - create a dummy_MQTT (does nothing, use for virtual switches only)
  - create a virtual sensor (switch type = selector) for each heater  with the following levels :
     * 0   = STOP
      * 10 = ANTI_FROST
      * 20 = ECO
      * 30 = COMFORT
- modify the devices in the config.json file (endpoint\_id:domoticz\_idx)
- create the system service :
<pre><code>
sudo nano /etc/systemd/system/tydmqttdom.service


[Unit]
Description=Python program

[Service]
# Note: setting PYTHONUNBUFFERED is necessary to see the output of this service in the journal
# See https://docs.python.org/2/using/cmdline.html#envvar-PYTHONUNBUFFERED
Environment=PYTHONUNBUFFERED=true

# Adjust this line to the correct path to test.py
ExecStart=/usr/bin/python3 /home/pi/tydmqttdom/main.py

Type=notify
WatchdogSec=30
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

</pre></code>
<pre><code>
systemctl enable tydmqttdom.service
systemctl start tydmqttdom.service

sudo systemctl status tydmqttdom.service
● tydmqttdom.service - Python program
   Loaded: loaded (/etc/systemd/system/tydmqttdom.service; enabled; vendor preset: enabled)
   Active: active (running) since Wed 2020-12-16 09:43:09 CET; 4 days ago
 Main PID: 13762 (python3)
    Tasks: 1 (limit: 2065)
   CGroup: /system.slice/tydmqttdom.service
           └─13762 /usr/bin/python3 /home/pi/tydmqttdom/main.py
 </pre></code>  

# MQTT

The service is listening on topic domoticz/out and sending to domoticz/in

domoticz/in {"command": "switchlight", "idx": 656, "switchcmd": "Set Level", "level": 20}

# Logging

A new log file  is created every day :

<pre><code>
ls -l /var/log/tydmqttdom.log*
-rw-r--r-- 1 root root    3276 déc.  20 07:00 /var/log/tydmqttdom.log
-rw-r--r-- 1 root root   22111 déc.   9 07:00 /var/log/tydmqttdom.log.2020-12-08
-rw-r--r-- 1 root root   54037 déc.  10 12:43 /var/log/tydmqttdom.log.2020-12-09
-rw-r--r-- 1 root root  131937 déc.  11 08:58 /var/log/tydmqttdom.log.2020-12-10
-rw-r--r-- 1 root root    2398 déc.  12 13:08 /var/log/tydmqttdom.log.2020-12-11
</pre></code>

# Limitations

- config.json is located in /home/pi/tydmqttdom (see main.py)
- logs are located in /var/log (idem)

# TODO

- clean the code
- clean again
- add roller shutters
- add arguments to specify the name and rotation of the log file , where to find the config file ...



