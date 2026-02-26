import os
import base64
import io
import json
from PIL import Image
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "db.json")

REPORT_TEMPLATE = """
# User Activity Report
**Date:** {date}
**Period:** {start_time} - {end_time}

## Summary
{summary}

## Active Applications
{active_windows}

## Activity Statistics
- Keyboard clicks: {keyboard_ticks}
- Mouse clicks: {mouse_ticks}

## Screen Analysis
{screen_analysis}

## Conclusion
{conclusion}
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

        db[entry_id] = {"text": text, "metadata": metadata}

        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

    def retrieve(self, query, start=None, end=None, n_results=10):
        if not os.path.exists(DB_PATH):
            return [], []

        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)

        docs, metadatas = [], []

        for entry_id, entry in db.items():
            meta = entry["metadata"]

            if start and end:
                start_ts = int(datetime.strptime(start, "%Y-%m-%d %H:%M:%S").timestamp())
                end_ts = int(datetime.strptime(end, "%Y-%m-%d %H:%M:%S").timestamp())
                if not (start_ts <= meta["timestamp"] <= end_ts):
                    continue

            docs.append(entry["text"])
            metadatas.append(meta)

        return docs[:n_results], metadatas[:n_results]

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
                "content": f"Fill in the report below in Turkish using the provided data. Respond in markdown format.\nTemplate:\n{REPORT_TEMPLATE}\nData:\n{context}\nStart time: {start}\nEnd time: {end}"
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