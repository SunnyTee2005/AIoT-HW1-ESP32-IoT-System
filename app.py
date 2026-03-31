from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# ─────────────────────────────────────────
# 資料庫初始化
# 每次 Flask 啟動時呼叫，建立 sensors 資料表
# IF NOT EXISTS → 已存在就跳過，不會重複建
# ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('aiotdb.db')  # 開啟（或建立）DB 檔案
    c = conn.cursor()                    # 建立游標（操作 DB 的指標）
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,  -- 自動編號
            device_id   TEXT,                               -- ESP32 裝置名稱
            ssid        TEXT,                               -- 連接的 WiFi 名稱
            ip_address  TEXT,                               -- ESP32 的 IP 位址
            temperature REAL,                               -- 溫度 (°C)
            humidity    REAL,                               -- 濕度 (%)
            source      TEXT,                               -- "real" 或 "simulated"
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP -- 自動填入時間
        )
    ''')
    conn.commit()   # 確認寫入（像按下儲存）
    conn.close()    # 關閉連線

# ─────────────────────────────────────────
# POST /sensor
# 接收 ESP32（真實或模擬）傳來的 JSON 資料，存進 DB
# 回傳 201 Created 表示成功新增一筆
# ─────────────────────────────────────────
@app.route('/sensor', methods=['POST'])
def receive_data():
    data = request.get_json()  # 把 HTTP body 的 JSON 解析成 Python dict

    if not data:
        return jsonify({"error": "No data received"}), 400  # 400 = Bad Request

    # 從 JSON 取值；如果對方沒傳這個 key，就用預設值
    device_id   = data.get('device_id', 'unknown')
    ssid        = data.get('ssid', 'unknown')
    ip_address  = data.get('ip_address', 'unknown')
    temperature = data.get('temperature', 0.0)
    humidity    = data.get('humidity', 0.0)
    source      = data.get('source', 'unknown')

    # 寫入資料庫
    conn = sqlite3.connect('aiotdb.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO sensors (device_id, ssid, ip_address, temperature, humidity, source) VALUES (?, ?, ?, ?, ?, ?)",
        (device_id, ssid, ip_address, temperature, humidity, source)
        # ? 是佔位符，防止 SQL Injection（避免惡意輸入破壞資料庫）
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": f"Data saved from {source}"}), 201

# ─────────────────────────────────────────
# GET /sensors
# 回傳最近 100 筆資料（JSON 格式）
# 給 Streamlit 或瀏覽器查看用
# ─────────────────────────────────────────
@app.route('/sensors', methods=['GET'])
def get_sensors():
    conn = sqlite3.connect('aiotdb.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sensors ORDER BY timestamp DESC LIMIT 100")
    rows = c.fetchall()  # 把查詢結果全部抓回來（list of tuples）
    conn.close()

    # 把每一筆 tuple 轉成 dict，這樣 jsonify 才能輸出有 key 的 JSON
    columns = ['id', 'device_id', 'ssid', 'ip_address', 'temperature', 'humidity', 'source', 'timestamp']
    result = [dict(zip(columns, row)) for row in rows]
    return jsonify(result), 200

# ─────────────────────────────────────────
# GET /sensors/count
# 回傳資料庫總筆數
# 給 Streamlit 顯示 "Total Readings" KPI 用
# ─────────────────────────────────────────
@app.route('/sensors/count', methods=['GET'])
def get_count():
    conn = sqlite3.connect('aiotdb.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sensors")
    count = c.fetchone()[0]  # fetchone() 回傳一個 tuple，[0] 取第一個值
    conn.close()
    return jsonify({"count": count}), 200

# ─────────────────────────────────────────
# GET /health
# 確認伺服器是否存活
# 用瀏覽器開這個網址，看到 "ok" 就代表 Flask 正常運作
# ─────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "db": "aiotdb.db"}), 200

# ─────────────────────────────────────────
# 程式進入點（等同 C 的 main）
# 只有直接執行 python app.py 才會跑這裡
# host='0.0.0.0' → 允許區網裝置（ESP32）連進來
# ─────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
