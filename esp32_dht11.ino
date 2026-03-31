#include <WiFi.h>
#include <HTTPClient.h>
#include <SimpleDHT.h>   // 你已經裝好的 library

// ─────────────────────────────────────────
// WiFi 設定
// ─────────────────────────────────────────
const char ssid[]     = "YOUR_WIFI_SSID";
const char password[] = "YOUR_WIFI_PASSWORD";

// ─────────────────────────────────────────
// Flask 伺服器位址
// 改成你 Mac 的 WiFi IP（終端機打 ipconfig getifaddr en0）
// ─────────────────────────────────────────
const char* SERVER_URL = "http://192.168.1.195:5000/sensor";

// ─────────────────────────────────────────
// DHT11 設定（用 SimpleDHT，跟你舊 code 一樣）
// ─────────────────────────────────────────
int pinDHT11 = 25;
SimpleDHT11 dht11(pinDHT11);

void setup() {
  Serial.begin(115200);

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("Sending data to: ");
  Serial.println(SERVER_URL);
}

void loop() {
  byte temperature = 0;
  byte humidity    = 0;

  if (dht11.read(&temperature, &humidity, NULL) != SimpleDHTErrSuccess) {
    Serial.println("DHT11 read failed, retrying...");
    delay(1000);
    return;
  }

  Serial.print("Temp: "); Serial.print((int)temperature); Serial.print("C  ");
  Serial.print("Humid: "); Serial.print((int)humidity);   Serial.println("%");

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");

    String ip = WiFi.localIP().toString();
    String payload = "{";
    payload += "\"device_id\":\"ESP32-REAL-001\",";
    payload += "\"ssid\":\"" + String(ssid) + "\",";
    payload += "\"ip_address\":\"" + ip + "\",";
    payload += "\"temperature\":" + String((int)temperature) + ",";
    payload += "\"humidity\":"    + String((int)humidity)    + ",";
    payload += "\"source\":\"real\"";
    payload += "}";

    int httpResponseCode = http.POST(payload);

    if (httpResponseCode == 201) {
      Serial.println("Server response: 201 Created OK");
    } else {
      Serial.print("Error, HTTP code: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi disconnected, skipping...");
  }

  delay(2000);
}
