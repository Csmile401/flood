from flask import Flask, render_template
from flood_fetcher import fetch_flood_data
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

app = Flask(__name__)

@app.route("/")
def index():
    try:
        data = fetch_flood_data().fillna("Normal")
        data["Keadaan"] = data["Keadaan"].astype(str)  # 确保为字符串
        records = data.to_dict(orient="records")       # 转为列表传到前端
    except Exception as e:
        records = []
    return render_template("index.html", data=records)

def fake_warning_test():
    now = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"🧪 模拟测试推送 @ {now}")
    title = f"🧪 测试警报 - {now}"
    body = "这是一条测试消息（每 10 秒打印一次），请勿恐慌。"
    print(f"🚨 {title} | 内容：{body}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=fake_warning_test, trigger="interval", seconds=10)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)
