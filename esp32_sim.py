import requests  # 發送 HTTP request（like 瀏覽器送出一個表單）
import random    # 產生隨機數，模擬感測器的數值浮動
import time      # 用來 sleep 5 秒

# ─────────────────────────────────────────
# Flask 伺服器位址
# 因為模擬器和 Flask 跑在同一台電腦，用 localhost 就好
# ─────────────────────────────────────────
FLASK_URL = "http://127.0.0.1:5000/sensor"

# 模擬 ESP32 的硬體資訊（假的，但格式跟真實一樣）
DEVICE_ID  = "ESP32-SIM-001"
SSID       = "AIoT-Lab-WiFi"
IP_ADDRESS = "192.168.1.42"

print("ESP32 模擬器啟動，每 5 秒送一筆資料...")
print(f"目標：{FLASK_URL}\n")

while True:  # 無限迴圈，等同 C 的 while(1)

    # 產生隨機溫濕度，模擬 DHT11 的讀數
    # DHT11 量測範圍：溫度 0-50°C，濕度 20-90%
    temperature = round(random.uniform(20.0, 35.0), 1)  # 小數點一位
    humidity    = round(random.uniform(40.0, 80.0), 1)

    # 要送出的 JSON 資料（跟真實 ESP32 送的格式一模一樣）
    payload = {
        "device_id":   DEVICE_ID,
        "ssid":        SSID,
        "ip_address":  IP_ADDRESS,
        "temperature": temperature,
        "humidity":    humidity,
        "source":      "simulated"   # 標記這筆是模擬資料
    }

    try:
        # 發送 HTTP POST（等同 ESP32 用 HTTPClient 送出去）
        response = requests.post(FLASK_URL, json=payload, timeout=3)
        print(f"[送出] temp={temperature}°C  humid={humidity}%  → {response.status_code} {response.json()}")

    except requests.exceptions.ConnectionError:
        # Flask 還沒啟動，或者當掉了
        print("[錯誤] 連不到 Flask，請確認 app.py 是否正在執行")

    time.sleep(2)  # 等 2 秒再送下一筆
