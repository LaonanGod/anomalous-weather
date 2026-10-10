
import json
import random
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("Asia/Shanghai")

# 34个中国城市及其经纬度
CITIES = [
    ("北京", 39.9042, 116.4074),
    ("上海", 31.2304, 121.4737),
    ("广州", 23.1291, 113.2644),
    ("深圳", 22.5431, 114.0579),
    ("成都", 30.5728, 104.0668),
    ("重庆", 29.5630, 106.5516),
    ("武汉", 30.5928, 114.3055),
    ("西安", 34.3416, 108.9398),
    ("南京", 32.0603, 118.7969),
    ("杭州", 30.2741, 120.1551),
    ("天津", 39.0842, 117.2010),
    ("苏州", 31.2989, 120.5853),
    ("郑州", 34.7466, 113.6254),
    ("长沙", 28.2282, 112.9388),
    ("合肥", 31.8206, 117.2272),
    ("济南", 36.6512, 117.1201),
    ("青岛", 36.0671, 120.3826),
    ("沈阳", 41.8057, 123.4315),
    ("大连", 38.9140, 121.6147),
    ("长春", 43.8171, 125.3235),
    ("哈尔滨", 45.8038, 126.5349),
    ("石家庄", 38.0428, 114.5149),
    ("太原", 37.8706, 112.5489),
    ("呼和浩特", 40.8426, 111.7492),
    ("兰州", 36.0611, 103.8343),
    ("西宁", 36.6171, 101.7782),
    ("银川", 38.4872, 106.2309),
    ("乌鲁木齐", 43.8256, 87.6168),
    ("拉萨", 29.6520, 91.1721),
    ("昆明", 25.0389, 102.7183),
    ("贵阳", 26.6470, 106.6302),
    ("南宁", 22.8170, 108.3665),
    ("福州", 26.0745, 119.2965),
    ("厦门", 24.4798, 118.0894),
]

ANOMALIES = [
    ("空洞云", "hollowCloud"),
    ("逆向降雨", "inverseRain"),
    ("火雨", "fireRain"),
    ("太阳风暴", "solarStorm"),
    ("头颅降雨", "headRain"),
    ("异常深寒", "deepCold"),
    ("酸雨", "acidRain"),
    ("冰晶坠落", "icefall"),
    ("强光天气", "strongLight"),
]

def describe_weather(code):
    if code == 0:
        return "晴", "sun"
    if code == 1:
        return "大致晴朗", "sun"
    if code == 2:
        return "多云间晴", "partly"
    if code == 3:
        return "阴", "cloud"
    if code in (45, 48):
        return "雾", "fog"
    if code in (51, 53, 55, 56, 57):
        return "毛毛雨", "rain"
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "降雨", "rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "降雪", "snow"
    if code in (95, 96, 99):
        return "雷暴", "storm"
    return "多云", "partly"

def distort_name(name):
    if len(name) < 2:
        return name
    # 给异常城市名添加轻微乱码效果
    return name[0] + "\u0338" + name[1:]

def main():
    params = {
        "latitude": ",".join(str(c[1]) for c in CITIES),
        "longitude": ",".join(str(c[2]) for c in CITIES),
        "daily": "weather_code,temperature_2m_min,temperature_2m_max",
        "forecast_days": 1,
        "timezone": "Asia/Shanghai",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url, headers={"User-Agent": "AnomalousWeather/1.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        weather_data = json.loads(response.read().decode("utf-8"))

    # 多城市请求应返回与城市列表对应的结果数组
    if not isinstance(weather_data, list):
        weather_data = [weather_data]
    if len(weather_data) != len(CITIES):
        raise RuntimeError(
            f"天气 API 返回了 {len(weather_data)} 个结果，"
            f"预期 {len(CITIES)} 个；本次不覆盖旧数据。"
        )

    # 每次更新随机选择2至4个异常城市
    anomaly_count = random.randint(2, 4)
    anomaly_indices = set(random.sample(range(len(CITIES)), anomaly_count))
    regions = []

    for i, (name, _, _) in enumerate(CITIES):
        daily = weather_data[i]["daily"]
        low = round(daily["temperature_2m_min"][0])
        high = round(daily["temperature_2m_max"][0])
        code = daily["weather_code"][0]
        weather, icon = describe_weather(code)

        anomaly = i in anomaly_indices
        display_name = name

        if anomaly:
            weather, icon = random.choice(ANOMALIES)
            display_name = distort_name(name)

        regions.append({
            "name": name,
            "displayName": display_name,
            "weather": weather,
            "temp": f"{low}–{high}",
            "icon": icon,
            "anomaly": anomaly,
        })

    now = datetime.now(TIMEZONE)
    result = {
        "generatedAt": now.strftime("%Y-%m-%d %H:%M:%S"),
        "forecastDate": now.strftime("%Y年%m月%d日"),
        "timezone": "Asia/Shanghai",
        "source": "Open-Meteo Forecast API",
        "regions": regions,
    }

    # 数据全部成功后再写入文件
    with open("forecast.json", "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print(f"天气数据更新成功：{len(regions)}个城市，{anomaly_count}个异常城市。")

if __name__ == "__main__":
    main()
