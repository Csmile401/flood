import requests
import pandas as pd
import time

# 设置 pandas 显示完整行
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

def fetch_flood_data():
    url = "https://publicinfobanjir.water.gov.my/waterleveldata/Sarawak"
    response = requests.get(url)
    tables = pd.read_html(response.text)

    for i, table in enumerate(tables):
        if "Nama Stesen" in table.columns:
            df = table.copy()
            break
    else:
        raise Exception("❌ 没有找到包含 'Nama Stesen' 的表格")

    df.columns = [
        "No", "ID Stesen", "Nama Stesen", "Daerah", "Lembangan", "Sub Lembangan",
        "Kemaskini Terakhir", "Aras Air (m) (Graf)", "Normal", "Waspada", "Amaran", "Bahaya"
    ]
def fetch_flood_data():
    url = "https://publicinfobanjir.water.gov.my/waterleveldata/Sarawak"
    response = requests.get(url)
    tables = pd.read_html(response.text)

    for i, table in enumerate(tables):
        if "Nama Stesen" in table.columns:
            df = table.copy()
            break
    else:
        raise Exception("❌ 没有找到包含 'Nama Stesen' 的表格")

    # 指定列名（不含 Sub Lembangan）
    df.columns = [
        "No", "ID Stesen", "Nama Stesen", "Daerah", "Lembangan", "Sub Lembangan",
        "Kemaskini Terakhir", "Aras Air (m) (Graf)", "Normal", "Waspada", "Amaran", "Bahaya"
    ]

    # 移除 Sub Lembangan 列
    df = df.drop(columns=["Sub Lembangan"])

    # 等级判断函数
    def classify_level(current, normal, waspada, amaran, bahaya):
        try:
            current = float(current)
            normal = float(normal)
            waspada = float(waspada)
            amaran = float(amaran)
            bahaya = float(bahaya)
        except:
            return "Tidak Sah"  # 无效数据

        if current >= bahaya:
            return "Bahaya"
        elif current >= amaran:
            return "Amaran"
        elif current >= waspada:
            return "Waspada"
        else:
            return "Normal"

    # 添加 Keadaan 列
    df["Keadaan"] = df.apply(lambda row: classify_level(
        row["Aras Air (m) (Graf)"],
        row["Normal"],
        row["Waspada"],
        row["Amaran"],
        row["Bahaya"]
    ), axis=1)

    return df


def realtime_loop(interval_seconds=60):
    print("⏳ 正在启动实时洪水数据抓取器...")
    while True:
        try:
            flood_data = fetch_flood_data()
            print("\n📥 最新水位数据（{}）:".format(time.strftime("%Y-%m-%d %H:%M:%S")))
            print(flood_data.to_string(index=False))
        except Exception as e:
            print(f"❌ 抓取失败: {e}")

        print(f"\n🕒 等待 {interval_seconds} 秒...\n")
        time.sleep(interval_seconds)

# 启动实时抓取循环
if __name__ == "__main__":
    realtime_loop()
