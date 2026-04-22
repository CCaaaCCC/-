#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_NeoPixel.h>

// ===================== 网络与后端配置 =====================
static const char* WIFI_SSID = "我的个人热点";
static const char* WIFI_PASSWORD = "22271000";
// 云端入口（通过 Nginx 反向代理到后端 /api）
static const char* SERVER_URL = "http://47.80.57.231/api/telemetry";
static const char* DEVICE_TOKEN = "2bb0d8225dead4b24f3add842aa31a4a0b87c3ee8d1472d3b745631772986e2c";
static const int DEVICE_ID = 1;

// ===================== 传感器引脚 =====================
static const int PIN_DHT = 4;
static const int PIN_SOIL = 34;
static const int PIN_LIGHT = 35;

// ===================== 执行器引脚 =====================
// 水泵控制引脚（必须通过继电器/MOS 驱动，不能直连水泵）
static const int PIN_PUMP = 26;
// 风扇 PWM 控制引脚（PC 四线风扇蓝线 PWM）
static const int PIN_FAN_PWM = 25;
// WS2812 灯带数据引脚（黄线）
static const int PIN_LIGHT_STRIP = 27;

// WS2812 灯珠数量（按实际修改）
static const int LIGHT_PIXEL_COUNT = 8;

// ===================== 设备配置 =====================
static const uint32_t DEBUG_BAUD = 115200;
static const uint32_t SAMPLE_INTERVAL_MS = 3000;
static const uint32_t HTTP_TIMEOUT_MS = 8000;
static const int ADC_SAMPLES = 12;

// DHT11 配置
static const uint8_t DHT_TYPE = DHT11;
DHT dht(PIN_DHT, DHT_TYPE);

// LCD1602 I2C 配置（地址通常是 0x27 或 0x3F）
LiquidCrystal_I2C lcd(0x27, 16, 2);

// WS2812 灯带对象（GRB 常见）
Adafruit_NeoPixel strip(LIGHT_PIXEL_COUNT, PIN_LIGHT_STRIP, NEO_GRB + NEO_KHZ800);

// 风扇 PWM 参数（PC 四线风扇常用 25kHz）
static const int FAN_PWM_CHANNEL = 0;
static const int FAN_PWM_FREQ = 25000;
static const int FAN_PWM_RESOLUTION = 8;

// 执行器电平兼容配置
// 若继电器是低电平触发，请改为 LOW
static const uint8_t PUMP_ACTIVE_LEVEL = HIGH;
// 若风扇驱动板对 PWM 做了反相，可改为 true
static const bool FAN_PWM_INVERT = false;

// ===================== 校准（根据你的硬件调整） =====================
static int SOIL_RAW_AT_0 = 3000;
static int SOIL_RAW_AT_100 = 1300;
static int LIGHT_RAW_AT_0 = 3800;
static int LIGHT_RAW_AT_100 = 800;

// 报警阈值
static const float SOIL_DRY_ALERT = 25.0f;
static const float SOIL_WET_ALERT = 85.0f;
static const float TEMP_HIGH_ALERT = 35.0f;
static const float TEMP_LOW_ALERT = 5.0f;
static const float LIGHT_LOW_ALERT = 10.0f;
static const float LIGHT_HIGH_ALERT = 90.0f;

struct ActuatorCommand {
  int pump = 0;
  int fan = 0;
  int fanSpeed = 100;
  int light = 0;
  int lightBrightness = 100;
};

static ActuatorCommand currentCmd;
static unsigned long lastSampleTs = 0;
static float lastTemp = 0.0f;
static float lastHum = 0.0f;
static bool hasValidDht = false;

int clampPercent(int value) {
  if (value < 0) return 0;
  if (value > 100) return 100;
  return value;
}

int readAnalogAverage(int pin, int samples) {
  long sum = 0;
  for (int i = 0; i < samples; ++i) {
    sum += analogRead(pin);
    delay(3);
  }
  return static_cast<int>(sum / samples);
}

float twoPointToPercent(int raw, int valueAt0, int valueAt100) {
  if (valueAt0 == valueAt100) {
    return 0.0f;
  }
  float pct = (raw - valueAt0) * 100.0f / (valueAt100 - valueAt0);
  if (pct < 0.0f) pct = 0.0f;
  if (pct > 100.0f) pct = 100.0f;
  return pct;
}

String makeAlert(float tempC, float soilPct, float lightPct) {
  if (soilPct < SOIL_DRY_ALERT) return "需要浇水";
  if (soilPct > SOIL_WET_ALERT) return "土壤过湿";
  if (tempC > TEMP_HIGH_ALERT) return "温度过高";
  if (tempC < TEMP_LOW_ALERT) return "温度过低";
  if (lightPct < LIGHT_LOW_ALERT) return "光照不足";
  if (lightPct > LIGHT_HIGH_ALERT) return "光照过强";
  return "正常";
}

void ensureWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.println("WiFi 断开，尝试重连...");
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  const unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 12000) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi 已连接，IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi 重连失败，本轮将跳过上报");
  }
}

void applyActuatorCommand(const ActuatorCommand& cmd) {
  // 水泵开关
  const uint8_t pumpOnLevel = PUMP_ACTIVE_LEVEL;
  const uint8_t pumpOffLevel = (PUMP_ACTIVE_LEVEL == HIGH) ? LOW : HIGH;
  digitalWrite(PIN_PUMP, cmd.pump == 1 ? pumpOnLevel : pumpOffLevel);

  // 风扇 PWM：只有开关打开时才输出占空比
  const int fanDuty = (cmd.fan == 1)
                      ? map(clampPercent(cmd.fanSpeed), 0, 100, 0, 255)
                      : 0;
  const int outputDuty = FAN_PWM_INVERT ? (255 - fanDuty) : fanDuty;
  ledcWrite(FAN_PWM_CHANNEL, outputDuty);

  // 补光灯亮度：只做白光补光（不做彩色控制）
  const int lightLevel = (cmd.light == 1)
                         ? map(clampPercent(cmd.lightBrightness), 0, 100, 0, 255)
                         : 0;
  for (int i = 0; i < LIGHT_PIXEL_COUNT; ++i) {
    strip.setPixelColor(i, strip.Color(lightLevel, lightLevel, lightLevel));
  }
  strip.show();
}

bool postTelemetryAndPullCommand(float tempC, float hum, float soilPct, float lightPct) {
  if (WiFi.status() != WL_CONNECTED) {
    return false;
  }

  StaticJsonDocument<256> reqDoc;
  reqDoc["device_id"] = DEVICE_ID;
  reqDoc["temp"] = tempC;
  reqDoc["humidity"] = hum;
  reqDoc["soil_moisture"] = soilPct;
  reqDoc["light"] = lightPct;

  String reqBody;
  serializeJson(reqDoc, reqBody);

  HTTPClient http;
  http.setTimeout(HTTP_TIMEOUT_MS);
  if (!http.begin(SERVER_URL)) {
    Serial.println("HTTP begin 失败");
    return false;
  }
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  int httpCode = http.POST(reqBody);
  if (httpCode <= 0) {
    Serial.printf("上报失败，HTTP 错误码=%d\n", httpCode);
    http.end();
    return false;
  }

  String response = http.getString();
  http.end();

  if (httpCode != 200) {
    Serial.printf("上报返回异常状态码=%d, body=%s\n", httpCode, response.c_str());
    return false;
  }

  StaticJsonDocument<384> respDoc;
  DeserializationError err = deserializeJson(respDoc, response);
  if (err) {
    Serial.print("解析控制指令失败: ");
    Serial.println(err.c_str());
    return false;
  }

  JsonVariant commands = respDoc["commands"];
  if (commands.isNull()) {
    return true;
  }

  currentCmd.pump = commands["pump"] | currentCmd.pump;
  currentCmd.fan = commands["fan"] | currentCmd.fan;
  currentCmd.fanSpeed = clampPercent(commands["fan_speed"] | currentCmd.fanSpeed);
  currentCmd.light = commands["light"] | currentCmd.light;
  currentCmd.lightBrightness = clampPercent(commands["light_brightness"] | currentCmd.lightBrightness);

  applyActuatorCommand(currentCmd);
  return true;
}

void updateLCD(float tempC, float hum, float soilPct, float lightPct, const String& alert) {
  lcd.clear();

  char line1[17];
  snprintf(line1, sizeof(line1), "T:%04.1f H:%04.1f", tempC, hum);
  lcd.setCursor(0, 0);
  lcd.print(line1);

  if (alert != "正常") {
    lcd.setCursor(0, 1);
    lcd.print(alert.substring(0, 16));
  } else {
    char line2[17];
    snprintf(line2, sizeof(line2), "S:%03.0f L:%03.0f", soilPct, lightPct);
    lcd.setCursor(0, 1);
    lcd.print(line2);
  }
}

void setup() {
  Serial.begin(DEBUG_BAUD);
  delay(200);

  analogReadResolution(12);
  analogSetPinAttenuation(PIN_SOIL, ADC_11db);
  analogSetPinAttenuation(PIN_LIGHT, ADC_11db);

  pinMode(PIN_PUMP, OUTPUT);
  const uint8_t pumpOffLevel = (PUMP_ACTIVE_LEVEL == HIGH) ? LOW : HIGH;
  digitalWrite(PIN_PUMP, pumpOffLevel);

  ledcSetup(FAN_PWM_CHANNEL, FAN_PWM_FREQ, FAN_PWM_RESOLUTION);
  ledcAttachPin(PIN_FAN_PWM, FAN_PWM_CHANNEL);
  ledcWrite(FAN_PWM_CHANNEL, 0);

  strip.begin();
  strip.clear();
  strip.show();

  dht.begin();

  Wire.begin();
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Plant Monitor");
  lcd.setCursor(0, 1);
  lcd.print("WiFi Connecting");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  ensureWifi();

  Serial.println("ESP32 植物监测+控制系统已启动");
  Serial.println("功能: 传感器上报 + 水泵/风扇/补光灯远程控制");
}

void loop() {
  const unsigned long now = millis();
  if (now - lastSampleTs < SAMPLE_INTERVAL_MS) {
    return;
  }
  lastSampleTs = now;

  ensureWifi();

  float tempC = dht.readTemperature();
  float hum = dht.readHumidity();
  if (!isnan(tempC) && !isnan(hum)) {
    lastTemp = tempC;
    lastHum = hum;
    hasValidDht = true;
  } else if (hasValidDht) {
    tempC = lastTemp;
    hum = lastHum;
  } else {
    tempC = 0.0f;
    hum = 0.0f;
  }

  int rawSoil = readAnalogAverage(PIN_SOIL, ADC_SAMPLES);
  int rawLight = readAnalogAverage(PIN_LIGHT, ADC_SAMPLES);

  float soilPct = twoPointToPercent(rawSoil, SOIL_RAW_AT_0, SOIL_RAW_AT_100);
  float lightPct = twoPointToPercent(rawLight, LIGHT_RAW_AT_0, LIGHT_RAW_AT_100);

  String alert = makeAlert(tempC, soilPct, lightPct);

  Serial.printf("温度=%.1f℃ 湿度=%.1f%% 土壤=%.0f%% 光照=%.0f%% 报警=%s\n",
                tempC, hum, soilPct, lightPct, alert.c_str());

  bool ok = postTelemetryAndPullCommand(tempC, hum, soilPct, lightPct);
  if (ok) {
    Serial.printf("控制: pump=%d fan=%d fanSpeed=%d light=%d lightBrightness=%d\n",
                  currentCmd.pump,
                  currentCmd.fan,
                  currentCmd.fanSpeed,
                  currentCmd.light,
                  currentCmd.lightBrightness);
  }

  updateLCD(tempC, hum, soilPct, lightPct, alert);
}