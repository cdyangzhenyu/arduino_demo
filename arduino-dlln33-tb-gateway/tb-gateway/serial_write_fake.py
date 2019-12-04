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

def parse_zigbee_data(data):
    data = {
        'device_id': 'SN-0002',
        #'data': True,
        'data': False,
        'ctl_type': 'led'
    }
    dst_port = '90'
    src_port = '91'
    dst_addr = data['device_id'].split('-')[1]
    dst_addr = dst_addr[2:4]+dst_addr[0:2]
    if isinstance(data['data'], bool):
        data['data'] = binascii.b2a_hex(chr(int(data['data'])))
    zb_pkg = src_port+dst_port+dst_addr+data['data']
    pkg_len = binascii.b2a_hex(chr(len(binascii.a2b_hex(zb_pkg))))
    zb_pkg = 'FE%s%sFF'%(pkg_len, zb_pkg)
    return binascii.a2b_hex(zb_pkg)

def main():
    while True:
        # 获得接收缓冲区字符
        data = parse_zigbee_data(2)
        print binascii.b2a_hex(data)
        ser.write(data)
        # 必要的软件延时
        time.sleep(1)

if __name__ == '__main__':
    try:
        #parse_zigbee_data(2)
        main()
    except KeyboardInterrupt:
        if ser != None:
            ser.close()
