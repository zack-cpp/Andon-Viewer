import webbrowser
import paho.mqtt.client as mqtt
import json
import time
import pyautogui
import csv
import argparse

MQTT_URL = ""
COUNTER_IDS = []
MQTT_TOPIC_VIEW = "test/view"

def open_browser_tab(link):
  try:
    path="C:/Program Files/Google/Chrome/Application/chrome.exe %s"
    webbrowser.get(path).open(link)
  except Exception as e:
    print(f"Error: {e}")

def on_subscribe(client, userdata, mid, reason_code_list, properties):
  # Since we subscribed only for a single channel, reason_code_list contains
  # a single entry
  if reason_code_list[0].is_failure:
    print(f"Broker rejected you subscription: {reason_code_list[0]}")
  else:
    print(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
  # Be careful, the reason_code_list is only present in MQTTv5.
  # In MQTTv3 it will always be empty
  if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
    print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
  else:
    print(f"Broker replied with failure: {reason_code_list[0]}")
  client.disconnect()

def on_message(client, userdata, msg):
  try:    
    json_payload = json.loads(msg.payload.decode('utf-8'))
    print(f"Received JSON message on topic {msg.topic}:")
    mesin_id = json_payload.get("MESIN_ID", "Unknown")
    print(f"Mesin ID: {mesin_id}")
    if msg.topic == MQTT_TOPIC_VIEW:
      if mesin_id in COUNTER_IDS:
        id = str(json_payload.get("ID", "Unknown"))
        url = MQTT_URL + "/runtime/" + id + "/detail"
        open_browser_tab(url)
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'tab', 'ctrl', 'w')
  except json.JSONDecodeError:
    print(f"Failed to decode JSON from topic {msg.topic}: {msg.payload.decode('utf-8')}")
    print(f"Message: {msg.payload.decode()}")

def on_connect(client, userdata, flags, reason_code, properties):
  if reason_code.is_failure:
    print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
  else:
    client.subscribe(MQTT_TOPIC_VIEW, qos=2)

def connect_mqtt(url):
  client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
  client.username_pw_set("andon", "andon")

  client.on_connect = on_connect
  client.on_message = on_message

  client.on_subscribe = on_subscribe
  client.on_unsubscribe = on_unsubscribe

  client.connect(url, 1883, 60)
  return client

with open("device_list.csv", newline='') as csvFile:
  reader = csv.reader(csvFile, delimiter=' ', quotechar='|')
  count = 0
  for array in reader:
    for element in array:
      COUNTER_IDS.append(element)
      count += 1

print(f"Counter List: {COUNTER_IDS}")

parser = argparse.ArgumentParser(description="Runtime auto view")
parser.add_argument("-u", "--url", type=str, required=True, help="Server URL")

args = parser.parse_args()
MQTT_URL = args.url
print(f"URL: {MQTT_URL}")

client = connect_mqtt(MQTT_URL)
client.publish("publish/test", "Running", qos=2)
while True:
  client.loop()