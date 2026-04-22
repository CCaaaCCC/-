#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"

// --------------------------
// User configuration
// --------------------------
const char* WIFI_SSID = "我的手机热点";
const char* WIFI_PASSWORD = "22271000";

// Example: http://47.80.57.231
const char* API_BASE_URL = "http://47.80.57.231";
const char* DEVICE_TOKEN = "2bb0d8225dead4b24f3add842aa31a4a0b87c3ee8d1472d3b745631772986e2c";
const int DEVICE_ID = 1;

const uint32_t CAPTURE_INTERVAL_MS = 1000;
const uint32_t HTTP_TIMEOUT_MS = 8000;

// --------------------------
// ESP32-CAM (AI Thinker) pins
// --------------------------
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

uint32_t lastCaptureAt = 0;

String buildUploadUrl() {
  return String(API_BASE_URL) + "/api/devices/" + String(DEVICE_ID) + "/camera";
}

bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 12;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 15;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return false;
  }

  sensor_t* sensor = esp_camera_sensor_get();
  if (sensor) {
    sensor->set_brightness(sensor, 0);
    sensor->set_saturation(sensor, 0);
  }

  return true;
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi connected, IP: ");
  Serial.println(WiFi.localIP());
}

bool uploadFrame(camera_fb_t* fb) {
  if (!fb || fb->len == 0) {
    return false;
  }

  HTTPClient http;
  http.setTimeout(HTTP_TIMEOUT_MS);

  String url = buildUploadUrl();
  if (!http.begin(url)) {
    Serial.println("HTTP begin failed");
    return false;
  }

  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  int code = http.POST(fb->buf, fb->len);
  bool ok = code >= 200 && code < 300;

  if (ok) {
    Serial.printf("Frame upload success, status=%d, bytes=%u\n", code, fb->len);
  } else {
    Serial.printf("Frame upload failed, status=%d\n", code);
    Serial.println(http.getString());
  }

  http.end();
  return ok;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  connectWiFi();

  if (!initCamera()) {
    Serial.println("Camera init error, reboot in 5s");
    delay(5000);
    ESP.restart();
  }

  Serial.println("ESP32-CAM snapshot uploader started");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    connectWiFi();
  }

  uint32_t now = millis();
  if (now - lastCaptureAt < CAPTURE_INTERVAL_MS) {
    delay(10);
    return;
  }
  lastCaptureAt = now;

  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Capture failed");
    return;
  }

  uploadFrame(fb);
  esp_camera_fb_return(fb);
}
