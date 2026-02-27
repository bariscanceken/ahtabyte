import os
import json
import re
import ast
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "db.json")
os.makedirs(DATA_DIR, exist_ok=True)

try:
    pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
    FONT_NAME = "Arial"
except Exception:
    FONT_NAME = "Helvetica"

def format_ai_text(ai_markdown_text):
    ai_markdown_text = re.sub(r"#+ (.*)", r'<b><font size="12">\1</font></b>', ai_markdown_text)
    ai_markdown_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", ai_markdown_text)
    ai_markdown_text = ai_markdown_text.replace("\n", "<br/>")
    ai_markdown_text = (
        ai_markdown_text.replace("Kullan c", "Kullanıcı")
        .replace("çal t", "çalıştı")
        .replace("i leme", "işleme")
    )
    return ai_markdown_text


def _parse_active_windows(raw_value):
    raw_value = (raw_value or "").strip()
    if not raw_value:
        return []
    if raw_value.startswith("[") and raw_value.endswith("]"):
        try:
            parsed = ast.literal_eval(raw_value)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
    return [w.strip(" []'\"") for w in raw_value.split(",") if w.strip(" []'\"")]

def load_day_data(report_date):
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        database = json.load(f)
    activity_entries = []
    for entry_id, entry in database.items():
        meta = entry["metadata"]
        if meta["timestamp_str"][:10] == report_date:
            entry_text = entry.get("text", "")
            keyboard_count, mouse_count, active_windows = 0, 0, []
            for line in entry_text.split("\n"):
                if "KEY_COUNT:" in line or "KEYBOARD_TICKS:" in line:
                    try:
                        keyboard_count = int(line.split(":", 1)[1].strip())
                    except Exception:
                        pass
                elif "MOUSE_COUNT:" in line or "MOUSE_TICKS:" in line:
                    try:
                        mouse_count = int(line.split(":", 1)[1].strip())
                    except Exception:
                        pass
                elif "ACTIVE_WINDOWS:" in line:
                    active_windows = _parse_active_windows(line.split(":", 1)[1])

            activity_entries.append({
                "time": meta["timestamp_str"][11:],
                "keyboard": keyboard_count,
                "mouse": mouse_count,
                "windows": active_windows,
            })
    return sorted(activity_entries, key=lambda x: x["time"])

def create_activity_chart(entries):
    times = [e["time"][:5] for e in entries]
    keyboard_counts = [e["keyboard"] for e in entries]
    mouse_counts = [e["mouse"] for e in entries]
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(times, keyboard_counts, label="Keyboard", color="#4A90D9", linewidth=2)
    ax.plot(times, mouse_counts, label="Mouse", color="#E67E22", linewidth=2)
    ax.set_xlabel("Zaman")
    ax.set_ylabel("Vuruş/Tıklama")
    ax.legend()
    ax.grid(True, alpha=0.3)
    step = max(1, len(times) // 10)
    ax.set_xticks(range(0, len(times), step))
    ax.set_xticklabels(times[::step], rotation=45)
    plt.tight_layout()
    image_buffer = BytesIO()
    plt.savefig(image_buffer, format="png", dpi=150)
    plt.close()
    image_buffer.seek(0)
    return image_buffer

def create_window_chart(entries):
    window_counts = {}
    for e in entries:
        for w in e["windows"]:
            if w:
                window_counts[w] = window_counts.get(w, 0) + 1
    if not window_counts:
        return None
    labels = list(window_counts.keys())[:15]
    values = list(window_counts.values())[:15]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(labels, values, color="#4A90D9")
    ax.set_xlabel("Dakika")
    plt.tight_layout()
    image_buffer = BytesIO()
    plt.savefig(image_buffer, format="png", dpi=150)
    plt.close()
    image_buffer.seek(0)
    return image_buffer

def generate_pdf(date):
    activity_entries = load_day_data(date)
    if not activity_entries:
        print(f"Veri bulunamadı: {date}")
        return
    output_pdf_path = os.path.join(DATA_DIR, f"report_{date}.pdf")
    document = SimpleDocTemplate(output_pdf_path, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    
    custom_normal = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontName=FONT_NAME, fontSize=10, leading=14)
    custom_title = ParagraphStyle('CustomTitle', parent=styles['Title'], fontName=FONT_NAME, fontSize=18, spaceAfter=12)
    custom_heading = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontName=FONT_NAME, fontSize=14, spaceAfter=8)

    story = []
    story.append(Paragraph(f"Aktivite Raporu - {date}", custom_title))
    story.append(Spacer(1, 0.5 * cm))
    
    total_keyboard = sum(e["keyboard"] for e in activity_entries)
    total_mouse = sum(e["mouse"] for e in activity_entries)
    
    summary_data = [
        ["Toplam Klavye Vuruşu", str(total_keyboard)],
        ["Toplam Fare Tıklaması", str(total_mouse)],
        ["Kayıtlı Aktif Dakika", str(len(activity_entries))],
    ]
    summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 1 * cm))
    
    story.append(Paragraph("Zaman Çizelgesi", custom_heading))
    story.append(Image(create_activity_chart(activity_entries), width=16 * cm, height=5 * cm))
    
    windows_chart_buffer = create_window_chart(activity_entries)
    if windows_chart_buffer:
        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph("Uygulama Kullanımı", custom_heading))
        story.append(Image(windows_chart_buffer, width=14 * cm, height=7 * cm))

    try:
        from src.core.rag import RAGPipeline
        pipeline = RAGPipeline()
        analysis_raw = pipeline.generate_report(date + " 00:00:00", date + " 23:59:59")
        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph("AI Analizi", custom_heading))
        story.append(Paragraph(format_ai_text(analysis_raw), custom_normal))
    except Exception as e:
        print(f"AI Analizi eklenemedi: {e}")

    document.build(story)
    print(f"Rapor oluşturuldu: {output_pdf_path}")

if __name__ == "__main__":
    date_input = input("Tarih (Örn: 2026-02-27): ")
    generate_pdf(date_input)