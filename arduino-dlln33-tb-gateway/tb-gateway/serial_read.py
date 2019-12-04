# -*- coding: utf-8 -*
import serial
import time
import json
import binascii
import paho.mqtt.client as mqtt
import logging

logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("/data/log/serial_read.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
            "sensor_id": "SN-%s%s" % (str[10:12],str[8:10]),
            }
    logger.info(data_pkg)
    return data_pkg

def parse_sensor_data(data):
    sensor_data = {}
    if not data:
        return
    sensor_data['serialNumber'] = data['sensor_id']
    sensor_data['model'] = 'ARDUINO UNO'
    data_str = binascii.a2b_hex(data['data'])
    logger.info(data_str)
    try:
        if data['src_port'] == '91':
            items = data_str.split('&')
            sensor_data['humidity'] = items[0].split(' ')[1].strip('\x00')
            sensor_data['temperature'] = items[0].split(' ')[2].strip('\x00')
            sensor_data['led'] = True if binascii.hexlify(items[1].strip('\x00')) else False
            soil = items[2].strip('\x00').strip(' ')
            if float(soil) > 100:
                sensor_data['soil'] = '0'
            else:
                sensor_data['soil'] = soil
            sensor_data['distance'] = items[3].strip('\x00').strip(' ')
            sensor_data['ndir'] = True if binascii.hexlify(items[4].strip('\x00')) else False
    except Exception, e:
        logger.error("parse sensor data error!")
        logger.error(e)
        return
    return sensor_data

def send_mqtt(data):
    if not data:
        return
    res = client.publish("sensors", json.dumps(data), 0)
    logger.info("mqtt publish result: %s, publish data: %s" % (res, json.dumps(data)))

def main():
    while True:
        # 获得接收缓冲区字符
        count = ser.inWaiting()
        if count != 0:
            # 读取内容并回显
            recv = ser.read(count)
            #print(recv)
            send_mqtt(parse_sensor_data(parse_data(recv)))
            #ser.write(recv)
        # 清空接收缓冲区
        ser.flushInput()
        # 必要的软件延时
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        client = mqtt.Client()
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        main()
    except KeyboardInterrupt:
        if ser != None:
            ser.close()
