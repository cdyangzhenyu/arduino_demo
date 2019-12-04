#include "DHT.h"
#include "SoftwareSerial.h"

// DHT
#define DHTPIN 3
#define DHTTYPE DHT11

// Distance

#define Trig 11 //引脚Tring 连接 IO D2
#define Echo 6 //引脚Echo 连接 IO D3 
 
float cm; //距离变量
float temp; // 

// Initialize DHT sensor.
DHT dht(DHTPIN, DHTTYPE);

SoftwareSerial soft(8, 9); // RX, TX

int ledPin = 7;
int soilPin = A0;
int pirPin = 4;

int ledStatus = 1; 
int pirValue = 0; //hongwai
float soilHumidity = 0.0; 

unsigned int DLLN3X_PREFIX_LEN = 6;
unsigned char SRC_PORT = 0x91;
unsigned char DST_PORT = 0x90;
unsigned char GATEWAY_ADDR_1 = 0x01;
unsigned char GATEWAY_ADDR_2 = 0x00;
unsigned char queue[100] = {};
int queue_offset = 0;
bool write_lock = false;
unsigned long lastSend;

void setup() {
  Serial.begin(9600); //USB serial port
  dht.begin();
  soft.begin(9600); //RX TX serial port
  pinMode(ledPin, OUTPUT);
  pinMode(soilPin, INPUT);
  pinMode(Trig, OUTPUT);  //ceju
  pinMode(Echo, INPUT);   //ceju
  pinMode(pirPin, INPUT); //hongwai
}

void loop() {
  // put your main code here, to run repeatedly:
  if ( millis() - lastSend > 1000 ) { // Update and send only after 1 seconds
    send_wrap_pkg();
    lastSend = millis();
  }
  
  if(ledStatus == 1){
    digitalWrite(ledPin, HIGH); 
  }
  else {
    digitalWrite(ledPin, LOW); 
  }
  unpackDataAndControl();
}

void unpackDataAndControl()
{
  while(soft.available()){
    unsigned char data = soft.read();
    Serial.println(data, HEX);
    if(data == 0xfe) {
      Serial.println("begin record data!");
      write_lock = true;
      queue_offset = 0;
      queue[100] = {};
     }
     if(write_lock) {
        memcpy(queue+queue_offset, &data, 1);
        queue_offset++;
        /*
        for(int j=0; j<sizeof(queue); j++){
          Serial.print(queue[j], HEX);
          Serial.print(" ");
        }
        Serial.println(" ");*/
      }
     if(data == 0xff) {
      Serial.println("end record data!");
      write_lock = false;
      //controll logic
      controlAction();
     }
  }
}

void controlAction()
{
  if(queue[3] == 0x90) {
    // led control
    Serial.print("ledStatus: ");
    Serial.println(int(queue[DLLN3X_PREFIX_LEN]));
    setLedData(int(queue[DLLN3X_PREFIX_LEN]));
  }
}

void getDistanceData(unsigned char *data_buff, unsigned int buff_len){
   //给Trig发送一个低高低的短时间脉冲,触发测距
  digitalWrite(Trig, LOW); //给Trig发送一个低电平
  delayMicroseconds(2);    //等待 2微妙
  digitalWrite(Trig,HIGH); //给Trig发送一个高电平
  delayMicroseconds(10);    //等待 10微妙
  digitalWrite(Trig, LOW); //给Trig发送一个低电平
  
  temp = float(pulseIn(Echo, HIGH)); //存储回波等待时间,
  //pulseIn函数会等待引脚变为HIGH,开始计算时间,再等待变为LOW并停止计时
  //返回脉冲的长度
  
  //声速是:340m/1s 换算成 34000cm / 1000000μs => 34 / 1000
  //因为发送到接收,实际是相同距离走了2回,所以要除以2
  //距离(厘米)  =  (回波时间 * (34 / 1000)) / 2
  //简化后的计算公式为 (回波时间 * 17)/ 1000
  
  cm = (temp * 17 )/1000; //把回波时间换算成cm
  if(cm > 1000) {
    cm = 0.00;
  }
  Serial.print("Echo =");
  Serial.print(temp);//串口输出等待时间的原始数据
  Serial.print(" | | Distance = ");
  Serial.print(cm);//串口输出距离换算成cm的结果
  Serial.println("cm");
  dtostrf(cm, 6, 2, data_buff);
}

void getSoilHumidityData(unsigned char *data_buff, unsigned int buff_len)
{
  soilHumidity = analogRead(soilPin);
  Serial.print("soilHumidity: ");
  Serial.println(soilHumidity);
  if (soilHumidity >= 1000) {
    soilHumidity = 0.0;
  }
  dtostrf(soilHumidity, 6, 2, data_buff);
}

unsigned char getLedData()
{
  return ledStatus;
}

unsigned char getHongwaiData()
{
  return digitalRead(pirPin);
}

void setLedData(int s)
{
  ledStatus = s;
}

void send_wrap_pkg()
{
  unsigned char dht_data[16]={};
  unsigned char soil_data[8]={};
  unsigned char distance_data[8]={};
  getAndSendTemperatureAndHumidityData(dht_data, 16);
  unsigned char led_data = getLedData();
  getSoilHumidityData(soil_data, 8);
  getDistanceData(distance_data, 8);
  unsigned char pri_data = getHongwaiData();
  
  unsigned char buff[40]={};
  int buff_offset = 0;
  memcpy(buff + buff_offset, dht_data, sizeof(dht_data));
  buff_offset += sizeof(dht_data);
  buff[buff_offset] = 0x26;
  buff_offset += 1;
  memcpy(buff + buff_offset, &led_data, sizeof(led_data));
  buff_offset += sizeof(led_data);
  buff[buff_offset] = 0x26; 
  buff_offset += 1;
  memcpy(buff + buff_offset, soil_data, sizeof(soil_data));
  buff_offset += sizeof(soil_data);
  buff[buff_offset] = 0x26; 
  buff_offset += 1;
  memcpy(buff + buff_offset, distance_data, sizeof(distance_data));
  buff_offset += sizeof(distance_data);
  buff[buff_offset] = 0x26; 
  buff_offset += 1;
  memcpy(buff + buff_offset, &pri_data, sizeof(pri_data));
  send_buff(buff, sizeof(buff), SRC_PORT);
}

void getAndSendTemperatureAndHumidityData(unsigned char *data_buff, unsigned int buff_len)
{
  Serial.println("Collecting temperature data.");

  // Reading temperature or humidity takes about 250 milliseconds!
  float h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  float t = dht.readTemperature();

  // Check if any reads failed and exit early (to try again).
  if (isnan(h) || isnan(t)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  Serial.print("Humidity: ");
  Serial.print(h);
  Serial.print(" %\t");
  Serial.print("Temperature: ");
  Serial.print(t);
  Serial.print(" *C \n");

  //unsigned char data_buff[16]={};
  unsigned char y[8]={};
  dtostrf(h, 6, 2, data_buff);
  dtostrf(t, 6, 2, y);
  memcpy(data_buff + 8, y, sizeof(y));
}

void send_buff(unsigned char *data_buff, unsigned int data_len, unsigned char src_port)
{
  unsigned char buff[100]={};
  buff[0] = 0xFE;
  buff[1] = 4 + data_len;
  buff[2] = src_port;
  buff[3] = DST_PORT;
  buff[4] = GATEWAY_ADDR_1;
  buff[5] = GATEWAY_ADDR_2;
  
  Serial.println(data_len);
  for(int j=0; j<data_len; j++){
    Serial.print(data_buff[j], HEX);
    Serial.print(" ");
  }
  Serial.println("");
  
  memcpy(buff + DLLN3X_PREFIX_LEN, data_buff, data_len);
  int end_index = int(DLLN3X_PREFIX_LEN + data_len); 
  buff[end_index] = 0xFF;
  /*
  for(int j=0; j<=sizeof(buff); j++){
    Serial.print(buff[j], HEX);
    Serial.print(" ");
  }
  Serial.println("");
  Serial.println(sizeof(buff));
  */
  soft.write(buff, sizeof(buff));
}

void myPtHex(int g){ // 把 g 最右邊 byte 印成 Hex 倆位
   int a = g& 0xf0;  // 左邊 4 bits
   a = a >> 4;  // 右移 4 bits
   int b = g& 0x0f;  // 右邊 4 bits
   char c = a < 10 ? a + '0' : a + 'A' - 10;
   Serial.print(c);
   c = b < 10 ? b + '0' : b + 'A' - 10;
   Serial.print(c);
}

/*
  计算校验和
*/
uint16_t calcCRC(char *p, int len)
{
  uint16_t t = 0;
  int i = 0;
  for (i = 0; i < len; i++)
  {
    t += p;
  }
  return t;
}

/*
  校验和检测
*/
bool checkCRC(unsigned char *p, int len)
{
  int i = 0;
  uint16_t t = 0;
  for (i = 0; i < len - 2; i++)
  {
    t += p;
  }
  if ((uint8_t)(t / 256) == p[len - 2] && (uint8_t)(t % 256) == p[len - 1])
  {
    return true;
  }
  else return false;
}

void parseUartPackage(char *p , int len) {
  Serial.print(F("[UART Read]:"));
  Serial.println(p);
 
  if(checkCRC(p,len) ==false){
      Serial.println("check crc error!");
      return;
  }
}
