from flask import Flask, render_template, request
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
import joblib
import os

app = Flask(__name__)
CORS(app)

# 🔐 Weather API Key
WEATHER_API_KEY = "af23b9fb017f45eba3b72706251204"
model_path = "model/flood_predictor.pkl"
flood_model = joblib.load(model_path) if os.path.exists(model_path) else None

# 📏 Thresholds
ALERT_LEVEL = 3.5
DANGER_LEVEL = 4.2

# 📍 District Coordinates
location_coords = {
    "Kuching": [1.5533, 110.3592],
    "Samarahan": [1.4592, 110.4635],
    "Bintulu": [3.1707, 113.0410],
    "Miri": [4.3963, 113.9916]
}

# 🌊 Keywords to match in iHydro station names
station_keywords = {
    "Kuching": ["sarawak", "batu kawa", "sungai sarawak"],
    "Samarahan": ["sambir", "samarahan"],
    "Bintulu": ["kemena", "bintulu"],
    "Miri": ["miri", "baong"]
}

# 🆘 Response Data
response_data = {
    "Kuching": {"shelter": "Stadium Negeri", "contact": "082-123456", "status": "danger"},
    "Samarahan": {"shelter": "Community Hall", "contact": "082-654321", "status": "safe"},
    "Bintulu": {"shelter": "Bintulu Civic Center", "contact": "086-778899", "status": "alert"},
    "Miri": {"shelter": "Miri Indoor Stadium", "contact": "085-223344", "status": "danger"}
}

# 🌊 Get iHydro Water Level
def get_realtime_water_level(district):
    try:
        url = "https://ihydro.sarawak.gov.my/iHydro/en/datatable/waterlevel/hourly-waterlevel.jsp"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, "html.parser")

        table = soup.find("table")
        rows = table.find_all("tr")
        keywords = station_keywords.get(district, [])

        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) > 4:
                station = cols[0].text.strip().lower()
                level = cols[4].text.strip()
                for keyword in keywords:
                    if keyword in station and level.replace('.', '', 1).isdigit():
                        print(f"✅ Match: {station} | Level: {level}")
                        return float(level)
    except Exception as e:
        print(f"[ERROR] Failed to fetch iHydro data: {e}")
    return 0

# 🏠 Home Page
@app.route("/")
def home():
    return render_template("weather.html", district_list=location_coords.keys())

# 🌦️ Main Weather + Flood Route
@app.route("/weather", methods=["POST"])
def get_weather():
    try:
        query = request.form.get("location", "Kuching")
        alert_level = ALERT_LEVEL
        danger_level = DANGER_LEVEL

        # 📡 WeatherAPI
        weather_url = f"https://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={query}&days=3"
        res = requests.get(weather_url, timeout=5)
        data = res.json()

        forecast_days = data.get("forecast", {}).get("forecastday", [])
        if not forecast_days:
            raise Exception("No forecast data returned.")

        forecast_today = forecast_days[0]
        condition_text = forecast_today["day"]["condition"]["text"]
        date = forecast_today["date"]
        rain_mm = float(forecast_today["day"]["totalprecip_mm"])

        # 🌊 Water Level (iHydro)
        current_water_level = get_realtime_water_level(query)

        # 🚨 Warning Check
        danger_alert = current_water_level >= danger_level

        # 🧠 Flood Risk AI
        flood_risk = False
        if flood_model:
            X_input = [[current_water_level, alert_level, danger_level]]
            flood_risk = bool(flood_model.predict(X_input)[0])

        rain_chart = [{"date": d["date"], "rain": d["day"]["totalprecip_mm"]} for d in forecast_days]
        coords = location_coords.get(query, [1.55, 110.33])
        response_meta = response_data.get(query, {})

        return render_template(
            "weather.html",
            district_list=location_coords.keys(),
            query=query,
            date=date,
            condition=condition_text,
            rainfall=rain_mm,
            water_level=current_water_level,
            alert_level=alert_level,
            danger_level=danger_level,
            flood_risk=flood_risk,
            rain_chart=rain_chart,
            lat=coords[0],
            lng=coords[1],
            response_meta=response_meta,
            danger_alert=danger_alert
        )
    except Exception as e:
        return render_template("weather.html", error=str(e), district_list=location_coords.keys())

# 📄 Evacuation Plan
@app.route("/evacuation-plan")
def evac_plan():
    return render_template("evacuation_plan.html")

# 🙋 Volunteer Form
@app.route("/volunteer")
def volunteer():
    return render_template("volunteer_form.html", district_list=location_coords.keys())

# 🤖 AI Chatbot
@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        question = request.form.get("question")
        dummy_answer = {
            "Where to evacuate?": "Please go to the nearest shelter as per your district plan.",
            "What is alert level?": "Alert level is when water reaches 3.5m.",
            "What is danger level?": "Danger level is when water exceeds 4.2m and flooding is likely."
        }
        answer = dummy_answer.get(question.strip(), "Sorry, I don't have an answer right now.")
        return render_template("ask.html", question=question, answer=answer)
    return render_template("ask.html")

# 📨 Volunteer Submission
@app.route("/submit-volunteer", methods=["POST"])
def submit_volunteer():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    district = request.form.get("district")
    role = request.form.get("role")
    message = request.form.get("message")

    print("\n📥 New Volunteer / Aid Request:")
    print(f"Name: {name}, Email: {email}, Phone: {phone}, District: {district}, Role: {role}")
    print(f"Message: {message}\n")

    return render_template("thank_you.html", name=name, role=role)

# 🚀 Run App
if __name__ == "__main__":
    app.run(debug=True, port=3000)

