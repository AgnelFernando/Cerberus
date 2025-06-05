import lcm
import paho.mqtt.client as mqtt
from lcm_msgs.ultrasonic_data import ultrasonic_data  
import json

mqtt_client = mqtt.Client()

def connect_mqtt():
    try:
        mqtt_client.connect("localhost", 1883, 60)  
        print("Connected to MQTT broker at localhost:1883")
    except Exception as e:
        print("Failed to connect to MQTT broker: {}".format(e))
        exit(1)

def ultrasonic_handler(channel, data):
    msg = ultrasonic_data.decode(data)

    # Build a dictionary of the ultrasonic data
    ultrasonic_data_dict = {
        "timestamp": msg.stamp,
        "front": round(msg.range[0], 2),
        "right": round(msg.range[1], 2),
        "left": round(msg.range[2], 2),
        "back": round(msg.range[3], 2)
    }

    # Convert to JSON and publish to MQTT
    mqtt_payload = json.dumps(ultrasonic_data_dict)
    mqtt_client.publish("robot/ultrasonic", mqtt_payload)

def main():
    # Connect to MQTT broker
    connect_mqtt()

    # Setup LCM
    lc = lcm.LCM()
    _ = lc.subscribe("/unitree/ultrasonic", ultrasonic_handler)

    print("Listening to ultrasonic data and publishing to MQTT...")

    try:
        while True:
            lc.handle()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
