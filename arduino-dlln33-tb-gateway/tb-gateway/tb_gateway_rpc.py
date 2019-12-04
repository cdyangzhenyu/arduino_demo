import json
import paho.mqtt.client as mqtt

MQTT_HOST = "TB-SERVER-IP"
MQTT_PORT = 31883
ACCESS_TOKEN = "UvgTskD2dinGvjY74NME"

def on_message(client, userdata, msg):
    print 'Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload)
    data = json.loads(msg.payload)
    if data['method'] == 'setLedStatus':
        print "set led status success!"
        publish_data = json.dumps({"params": False})
        client.publish('v1/devices/me/attributes', json.dumps({"led": False}), 0)
        client.publish(msg.topic.replace('request', 'response'), publish_data, 0)

    elif data['method'] == 'getLedStatus':
        publish_data = json.dumps({"params": True})
        print data
        client.publish(msg.topic.replace('request', 'response'), publish_data, 0)
        print "get led status success!"

def on_connect(client, userdata, rc, *extra_params):
    print('Connected with result code ' + str(rc))
    # Subscribing to receive RPC requests
    #client.subscribe('sensor/SN-0002/request/no-reply/+')
    client.subscribe('v1/devices/me/rpc/request/+')

client = mqtt.Client()
# Register connect callback
client.on_connect = on_connect
# Registed publish message callback
client.on_message = on_message
client.username_pw_set(ACCESS_TOKEN)
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()
