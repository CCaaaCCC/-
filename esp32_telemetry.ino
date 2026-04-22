#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- 配置区域 ---
const char* ssid = "我的手机热点";
const char* password = "22271000";
// 云端入口（通过 Nginx 反向代理到后端 /api）
const char* serverUrl = "http://47.80.57.231/api/telemetry";
const char* deviceToken = "2bb0d8225dead4b24f3add842aa31a4a0b87c3ee8d1472d3b745631772986e2c";
const int deviceId = 1;

// --- 全局变量 (用于模拟平滑波动) ---
float last_temp = 25.0;
float last_hum = 50.0;
float last_soil = 40.0;
float last_light = 500.0;

unsigned long lastTime = 0;
const unsigned long timerDelay = 5000; // 5秒间隔

void setup() {
  Serial.begin(115200);

  // 连接 WiFi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());
}

// 模拟传感器数据生成函数 (带波动的随机数)
void updateSensorData() {
  // 温度 22-28C, 每次波动 +/- 0.5C
  last_temp += random(-50, 51) / 100.0;
  last_temp = constrain(last_temp, 22.0, 28.0);

  // 湿度 40-60%, 每次波动 +/- 1%
  last_hum += random(-100, 101) / 100.0;
  last_hum = constrain(last_hum, 40.0, 60.0);

  // 土壤水分 30-50%, 每次波动 +/- 0.5%
  last_soil += random(-50, 51) / 100.0;
  last_soil = constrain(last_soil, 30.0, 50.0);

  // 光照 200-800lux, 每次波动 +/- 10
  last_light += random(-10, 11);
  last_light = constrain(last_light, 200.0, 800.0);
}

void loop() {
  // 每隔 timerDelay 秒发送一次
  if ((millis() - lastTime) > timerDelay) {
    if (WiFi.status() == WL_CONNECTED) {
      
      updateSensorData();
      
      // 创建 JSON 对象
      StaticJsonDocument<200> doc;
      doc["device_id"] = deviceId;
      doc["temp"] = last_temp;
      doc["humidity"] = last_hum;
      doc["soil_moisture"] = last_soil;
      doc["light"] = last_light;

      String jsonOutput;
      serializeJson(doc, jsonOutput);

      // 发送 HTTP POST 请求
      HTTPClient http;
      if (!http.begin(serverUrl)) {
        Serial.println("HTTP begin failed");
        lastTime = millis();
        return;
      }
      http.addHeader("Content-Type", "application/json");
      http.addHeader("X-Device-Token", deviceToken);
      Serial.print("Sending Data: ");
      Serial.println(jsonOutput);

      int httpResponseCode = http.POST(jsonOutput);

      if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);
        Serial.print("Server Response: ");
        Serial.println(response);
      } else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
        Serial.println("Check if your server is running and accessible.");
      }

      http.end();
    } else {
      Serial.println("WiFi Disconnected");
    }
    lastTime = millis();
  }
}
