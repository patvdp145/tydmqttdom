# tydmqttdom
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
# Getting started

- create/ associate each RF 6600 FP with the Delta Dore app
- use tydom_python (use get_configs_file) to get the endpoint ids.
- in Domoticz :
  - create a dummy_MQTT (does nothing, use for virtual switches only)
  - create a virtual sensor (switch type = selector) for each heater  with the following levels :
     * 0   = STOP
      * 10 = ANTI_FROST
      * 20 = ECO
      * 30 = COMFORT
- modify the devices in the config.json file (endpoint_id:domoticz_idx)
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
- add arguments to specify log's names and rotation, config file ...




