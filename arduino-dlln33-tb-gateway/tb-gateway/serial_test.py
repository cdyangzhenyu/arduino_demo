# -*- coding: utf-8 -*
import serial
import time
import json
import binascii
import paho.mqtt.client as mqtt

# 打开串口
ser = serial.Serial("/dev/ttyAMA0", 9600)
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883

def print_hex_str(str):
    print len(str)
    print str
    str1=binascii.b2a_hex(str)
    print str1

def parse_data(str):
    str=binascii.b2a_hex(str)
    if not str.startswith('fe'):
        return 
    if not str.endswith('ff'):
        return
    data_len = int(str[2:4], 16) - 4
    data = str[6*2:data_len*2+6*2]
    data_pkg = {
            "format": 16,
            "len": str[2:4],
            "src_port": str[4:6],
            "dst_port": str[6:8],
            "addr": str[8:12],
            "data": data,
            "sensor_id": "SN-%s%s-%s" % (str[10:12],str[8:10],str[4:6]),
            }
    print data_pkg
    return data_pkg
    #print type(binascii.a2b_hex(data))

def parse_sensor_data(data):
    sensor_data = {}
    if not data:
        return
    sensor_data['serialNumber'] = data['sensor_id']
    if data['src_port'] == '91':
        sensor_data['model'] = 'DHT11'
        data_str = binascii.a2b_hex(data['data'])
        sensor_data['humidity'] = data_str.split(' ')[1].strip('\x00')
        sensor_data['temperature'] = data_str.split(' ')[2].strip('\x00')
    return sensor_data

def send_mqtt(data):
    if not data:
        return
    client.publish("sensors", json.dumps(data), 0)
    print json.dumps(data)

def on_message(client, userdata, msg):
    print 'Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload)
    data = json.loads(msg.payload)
    
def on_connect(client, userdata, rc, *extra_params):
    print('Connected with result code ' + str(rc))
    # Subscribing to receive RPC requests
    client.subscribe('sensor/SN-0002-91/request/no-reply/+')
    # Sending current GPIO status
    client.publish('sensors/SN-0002-91/response/echo/', json.dumps({"led": True}), 1)

def main():
    while True:
        # 获得接收缓冲区字符
        count = ser.inWaiting()
        if count != 0:
            # 读取内容并回显
            recv = ser.read(count)
            #print(recv)
            send_mqtt(parse_sensor_data(parse_data(recv)))
            ser.write(recv)
        # 清空接收缓冲区
        ser.flushInput()
        # 必要的软件延时
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        client = mqtt.Client()
        # Register connect callback
        client.on_connect = on_connect
        # Registed publish message callback
        client.on_message = on_message
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_forever()
        #main()
    except KeyboardInterrupt:
        if ser != None:
            ser.close()
