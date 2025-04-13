# rag_helper.py

import pandas as pd
from chromadb import Client
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import ollama

# ✅ 加载 CSV 数据并转换为文档列表
def load_flood_docs(file_path="disaster_reports.csv"):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("❌ disaster_reports.csv 文件未找到，请确保文件存在于项目根目录")
        return []

    docs = []
    for _, row in df.iterrows():
        doc = (
            f"Location: {row.get('Location', '')}\n"
            f"Severity: {row.get('Severity_Label', '')}\n"
            f"Timestamp: {row.get('Timestamp', '')}\n"
            f"Description: {row.get('Description', '')}"
        )
        docs.append(doc)
    return docs

# ✅ 创建 Chroma 向量数据库并嵌入文档
def init_vector_db(docs):
    if not docs:
        print("⚠️ 没有文档可用于向量化，向量数据库初始化跳过")
        return None

    embedding_function = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = Client(Settings(allow_reset=True))
    client.reset()
    collection = client.create_collection(name="flood_data", embedding_function=embedding_function)

    for i, doc in enumerate(docs):
        collection.add(documents=[doc], ids=[str(i)])

    return collection

# ✅ 使用本地 Ollama 模型生成回答
def generate_with_ollama(prompt: str, model="hf.co/Wonghehehe/model:latest"):
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content']
    except Exception as e:
        return f"❌ LLM 回答失败，请检查 Ollama 是否开启。\n错误详情：{str(e)}"
