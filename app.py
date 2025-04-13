from flask import Flask, render_template, request, jsonify
from flood_fetcher import fetch_flood_data
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import logging
from rag_helper import load_flood_docs, init_vector_db, generate_with_ollama

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 初始化文档向量数据库
docs = load_flood_docs("disaster_reports.csv")
vector_db = init_vector_db(docs)

# 首页（原始 index）
@app.route("/")
def index():
    try:
        data = fetch_flood_data().fillna("Normal")
        data["Keadaan"] = data["Keadaan"].astype(str)
        records = data.to_dict(orient="records")
    except Exception as e:
        logging.error("❌ 获取洪水数据失败：", exc_info=True)
        records = []
    return render_template("index.html", data=records)

# Chat 页面
@app.route("/ask", methods=["GET", "POST"])
def ask():
    question = ""
    answer = ""
    if request.method == "POST":
        question = request.form.get("question")
        results = vector_db.query(query_texts=[question], n_results=3)
        context = "\n\n".join(results["documents"][0])
        prompt = f"Based on the context below, answer the question:\n\n{context}\n\nQuestion: {question}\nAnswer:"
        answer = generate_with_ollama(prompt)
    return render_template("ask.html", question=question, answer=answer)

# ✅ Flood 预警系统页面（包含 AI 按钮）
@app.route("/flood")
def flood_with_ai():
    try:
        data = fetch_flood_data().fillna("Normal")
        data["Keadaan"] = data["Keadaan"].astype(str)
        records = data.to_dict(orient="records")
    except Exception as e:
        logging.error("❌ 获取洪水数据失败：", exc_info=True)
        records = []
    return render_template("flood_with_ai_suggestion.html", data=records)

# ✅ AI suggestion API（给 JS 使用）
@app.route("/ask-ai", methods=["POST"])
def ask_ai():
    data = request.get_json()
    question = data.get("question", "")
    if not question:
        return jsonify({"answer": "No question provided."})
    try:
        answer = generate_with_ollama(question)
    except Exception as e:
        logging.error("❌ AI 回答失败", exc_info=True)
        answer = f"Error: {str(e)}"
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(debug=True)
