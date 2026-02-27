import os
import json
from flask import Flask, jsonify, send_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "db.json")

app = Flask(__name__)


def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/data", methods=["GET"])
def get_data():
    db = load_db()
    return jsonify(db)


@app.route("/report/<date>", methods=["GET"])
def get_report(date):
    pdf_path = os.path.join(BASE_DIR, "data", f"report_{date}.pdf")
    if not os.path.exists(pdf_path):
        return jsonify({"error": "Report not found"}), 404
    return send_file(pdf_path, mimetype="application/pdf")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)