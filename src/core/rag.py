import os
import base64
import io
import json
from PIL import Image
from datetime import datetime
from math import sqrt
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "db.json")
EMBEDDING_MODEL = "text-embedding-3-small"

REPORT_TEMPLATE = """
## Genel Özet
{summary}

## Zaman Çizelgesi ve Uygulamalar
{timeline}

## Ekran Analizi
{screen_analysis}

## Odak ve Verimlilik
{focus}

## Öneriler
{recommendations}
"""


class RAGPipeline:

    def analyze(self, img_path):
        img = Image.open(img_path)
        img.thumbnail((1024, 768))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}},
                    {"type": "text", "text": "What do you see in this screenshot? Briefly explain."}
                ]
            }]
        )
        return response.choices[0].message.content

    def embed(self, entry_id, text, metadata):
        db = {}
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "r", encoding="utf-8") as f:
                db = json.load(f)

        # Metni embedding'e çevir ve metadata ile birlikte kaydet
        emb_response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        embedding = emb_response.data[0].embedding

        db[entry_id] = {
            "text": text,
            "metadata": metadata,
            "embedding": embedding,
        }

        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _cosine_similarity(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sqrt(sum(x * x for x in a))
        norm_b = sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def retrieve(self, query=None, start=None, end=None, n_results=10):
        if not os.path.exists(DB_PATH):
            return [], []

        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)

        # Zaman filtresine göre süz
        filtered_entries = []
        for entry in db.values():
            meta = entry["metadata"]

            if start and end:
                start_ts = int(datetime.strptime(start, "%Y-%m-%d %H:%M:%S").timestamp())
                end_ts = int(datetime.strptime(end, "%Y-%m-%d %H:%M:%S").timestamp())
                if not (start_ts <= meta["timestamp"] <= end_ts):
                    continue

            filtered_entries.append(entry)

        if not filtered_entries:
            return [], []

        # Eski kayıtlar için veya query yoksa: basitçe ilk N kaydı dön
        has_any_embedding = any("embedding" in e for e in filtered_entries)
        if not query or not has_any_embedding:
            docs = [e["text"] for e in filtered_entries[:n_results]]
            metadatas = [e["metadata"] for e in filtered_entries[:n_results]]
            return docs, metadatas

        # Soru embedding'i ile entry embedding'leri arasında kosinüs benzerliği hesapla
        q_emb_resp = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query,
        )
        q_emb = q_emb_resp.data[0].embedding

        scored = []
        for entry in filtered_entries:
            if "embedding" not in entry:
                continue
            score = self._cosine_similarity(q_emb, entry["embedding"])
            scored.append((score, entry))

        if not scored:
            return [], []

        scored.sort(key=lambda x: x[0], reverse=True)
        top_entries = [e for _, e in scored[:n_results]]

        docs = [e["text"] for e in top_entries]
        metadatas = [e["metadata"] for e in top_entries]
        return docs, metadatas

    def generate(self, question, docs, metadatas):
        context = "\n---\n".join(docs)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}]
        )
        return response.choices[0].message.content

    def report(self, docs, metadatas, start, end):
        context = "\n---\n".join(docs)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": (
                    "Aşağıdaki verileri kullanarak odaklı ve kısa bir günlük/çalışma raporu üret. "
                    "Yanıtı TÜRKÇE ve markdown formatında ver. "
                    "Verilerde geçen 'TIME:', 'ACTIVE_WINDOWS:', 'KEY_COUNT:', 'MOUSE_COUNT:' ve "
                    "'SCREEN ANALYSIS:' kısımlarını özellikle kullan.\n\n"
                    "Kurallar:\n"
                    "- Gereksiz tekrar yapma, mümkün olduğunca öz ve net ol.\n"
                    "- 'Verilerde ekran analizi yoktur' gibi cümleleri sadece gerçekten hiç SCREEN ANALYSIS yoksa yaz.\n"
                    "- Aynı uygulamanın tekrarlarını grupla (örneğin sık kullanılan uygulamaları tek başlık altında özetle).\n\n"
                    f"Şablon:\n{REPORT_TEMPLATE}\n\n"
                    f"Veri:\n{context}\n"
                    f"Başlangıç zamanı: {start}\n"
                    f"Bitiş zamanı: {end}"
                )
            }]
        )
        return response.choices[0].message.content

    def ingest(self, text, timestamp, img_path=None):
        screen_analysis = self.analyze(img_path) if img_path else "N/A"
        full_text = text + "\nSCREEN ANALYSIS: " + screen_analysis

        entry_id = f"entry_{timestamp.replace(' ', '_').replace(':', '-')}"
        metadata = {
            "timestamp": int(datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").timestamp()),
            "timestamp_str": timestamp,
            "screenshot_path": img_path or ""
        }

        self.embed(entry_id, full_text, metadata)
        print(f"[{timestamp}] Saved.")

    def query(self, question):
        docs, metadatas = self.retrieve(question)
        return self.generate(question, docs, metadatas)

    def generate_report(self, start, end):
        question = f"Summarize activities between {start} and {end}"
        docs, metadatas = self.retrieve(question, start=start, end=end)
        return self.report(docs, metadatas, start, end)


if __name__ == "__main__":
    pipeline = RAGPipeline()

    print("Time range? (e.g: 2026-02-26 09:00:00)")
    start = input("Start: ")
    end = input("End: ")

    report = pipeline.generate_report(start, end)

    filename = os.path.join(BASE_DIR, "data", f"report_{start[:10]}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report generated: {filename}")