import requests
import time
import random

# --- 配置 ---
SERVER_URL = "http://localhost:8000/api/telemetry"
DEVICE_ID = 1

# 初始数据
data = {
    "device_id": DEVICE_ID,
    "temp": 25.0,
    "humidity": 55.0,
    "soil_moisture": 40.0,
    "light": 500.0
}

print(f"🚀 开始模拟 ESP32 数据发送 (Device ID: {DEVICE_ID})...")
print("按下 Ctrl+C 停止模拟\n")

try:
    while True:
        # 1. 模拟数据小幅波动
        data["temp"] += round(random.uniform(-0.5, 0.5), 2)
        data["humidity"] += round(random.uniform(-1.0, 1.0), 2)
        data["soil_moisture"] += round(random.uniform(-0.5, 0.5), 2)
        data["light"] += round(random.uniform(-20, 20), 0)

        # 限制范围
        data["temp"] = max(15, min(35, data["temp"]))
        data["humidity"] = max(30, min(90, data["humidity"]))
        data["soil_moisture"] = max(10, min(80, data["soil_moisture"]))
        data["light"] = max(0, min(1000, data["light"]))

        # 2. 发送 POST 请求到后端
        try:
            response = requests.post(SERVER_URL, json=data, timeout=5)
            if response.status_code == 200:
                res_json = response.json()
                commands = res_json.get("commands", {})
                
                # 3. 打印当前状态和收到的指令
                print(f"[{time.strftime('%H:%M:%S')}] 数据已送达:")
                print(f"   温度: {data['temp']:.1f}°C | 湿度: {data['humidity']:.1f}% | 土壤: {data['soil_moisture']:.1f}%")
                print(f"   收到指令 -> 水泵: {'开' if commands.get('pump') else '关'} | 风扇: {'开' if commands.get('fan') else '关'} | 补光: {'开' if commands.get('light') else '关'}")
            else:
                print(f"鈸 鍙戦€佸け璐: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"鈸 杩炴帴鍚庣澶辫触: {e}")

        # 4. 每5秒发送一次
        time.sleep(5)

except KeyboardInterrupt:
    print("\n鉁 模拟已停止")
