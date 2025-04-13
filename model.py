from flask import Flask, request, jsonify
import joblib
import numpy as np
from collections import Counter
import pandas as pd
import requests

app = Flask(__name__)

# === 模型加载 ===
rf_model = joblib.load("random_forest_flood_model.pkl")
svm_model = joblib.load("svm_flood_model.pkl")
knn_model = joblib.load("knn_flood_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# === AI 预测函数 ===
def predict_with_voting(features):
    features_array = np.array(features).reshape(1, -1)
    rf_pred = rf_model.predict(features_array)[0]
    svm_pred = svm_model.predict(features_array)[0]
    knn_pred = knn_model.predict(features_array)[0]

    votes = [rf_pred, svm_pred, knn_pred]
    vote_count = Counter(votes)

    final = rf_pred if len(vote_count) == 3 else vote_count.most_common(1)[0][0]

    return {
        "RandomForest": label_encoder.inverse_transform([rf_pred])[0],
        "SVM": label_encoder.inverse_transform([svm_pred])[0],
        "KNN": label_encoder.inverse_transform([knn_pred])[0],
        "FinalPrediction": label_encoder.inverse_transform([final])[0]
    }

# === 预测 API ===
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    try:
        features = [
            data["Water Level (m)"],
            data["Normal Level (m)"],
            data["Alert Level (m)"],
            data["Warning Level (m)"],
            data["Danger Level (m)"]
        ]
        result = predict_with_voting(features)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# === 网页抓取 API ===
@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    try:
        url = "https://publicinfobanjir.water.gov.my/waterleveldata/Sarawak"
        response = requests.get(url)
        tables = pd.read_html(response.text)
        df = tables[0]

        # 重命名列（确保兼容性）
        df.columns = [
            "No", "ID Stesen", "Nama Stesen", "Daerah", "Lembangan", "Sub Lembangan",
            "Kemaskini Terakhir", "Aras Air (m) (Graf)",
            "Normal", "Waspada", "Amaran", "Bahaya"
        ]

        df = df.drop(columns=["No", "ID Stesen"])  # 可以根据需要保留 ID

        # 返回 JSON 格式
        result = df.to_dict(orient='records')
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === 启动应用 ===
if __name__ == '__main__':
    app.run(debug=True)
