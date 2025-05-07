import os
import json
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
from fpdf import FPDF

# Use home directory to avoid WSL permissions issues
BASE_DIR = os.path.expanduser('~/blackhole_reports')
REPORT_DIR = os.path.join(BASE_DIR, 'reports')
GRAPH_DIR = os.path.join(BASE_DIR, 'graphs')
LOG_FILE = os.path.expanduser(
    '~/blackhole_nexus/honeypots/webdav/logs/upload_log.json'
)

# Ensure directories exist
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

# Load honeypot log data
def load_log_data():
    try:
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Log file not found: {LOG_FILE}")
        return []
    except json.JSONDecodeError:
        print(f"Malformed JSON in: {LOG_FILE}")
        return []

# Analyse data
def analyse_data(data):
    uploads = Counter()
    ips = Counter()
    timestamps = []

    for entry in data:
        filename = entry.get("filename")
        ip = entry.get("ip")
        timestamp = entry.get("timestamp")

        if filename:
            uploads[filename] += 1
        if ip:
            ips[ip] += 1
        if timestamp:
            timestamps.append(timestamp)

    return uploads, ips, timestamps

# Generate plots
def generate_graphs(uploads, ips):
    upload_chart_path = os.path.join(GRAPH_DIR, 'uploads.png')
    ip_chart_path = os.path.join(GRAPH_DIR, 'ips.png')

    if uploads:
        plt.figure(figsize=(6, 4))
        plt.bar(uploads.keys(), uploads.values(), color='goldenrod')
        plt.title('File Uploads')
        plt.xlabel('Filename')
        plt.ylabel('Upload Count')
        plt.tight_layout()
        plt.savefig(upload_chart_path)
        plt.close()

    if ips:
        plt.figure(figsize=(6, 4))
        plt.bar(ips.keys(), ips.values(), color='darkorange')
        plt.title('Uploader IPs')
        plt.xlabel('IP Address')
        plt.ylabel('Upload Count')
        plt.tight_layout()
        plt.savefig(ip_chart_path)
        plt.close()

    return upload_chart_path, ip_chart_path

# Create PDF report
def create_pdf_report(uploads, ips, timestamps, chart1, chart2):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f'report_{now}.pdf'
    filepath = os.path.join(REPORT_DIR, filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Blackhole Nexus Honeypot Report", ln=True, align='C')

    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Author: Sandyn B", ln=True)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Overview", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10,
        "This report summarises file upload activity detected by the WebDAV honeypot "
        "as part of the Blackhole Nexus system. It includes analysis of uploaded filenames, "
        "source IP addresses, and observed attack patterns."
    )

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Upload Summary", ln=True)
    pdf.set_font("Arial", '', 12)
    for fname, count in uploads.items():
        pdf.cell(0, 10, f"{fname}: {count} uploads", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Attacker IP Summary", ln=True)
    pdf.set_font("Arial", '', 12)
    for ip, count in ips.items():
        pdf.cell(0, 10, f"{ip}: {count} times", ln=True)

    if chart1 and os.path.exists(chart1):
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "File Upload Graph", ln=True)
        pdf.image(chart1, x=10, w=180)

    if chart2 and os.path.exists(chart2):
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "IP Upload Frequency", ln=True)
        pdf.image(chart2, x=10, w=180)

    pdf.output(filepath)
    print(f"\n✅ Report saved: {filepath}")

# Main
if __name__ == '__main__':
    print("🔍 Loading honeypot logs...")
    logs = load_log_data()
    if not logs:
        print("❌ No data found to generate report.")
    else:
        print("📊 Analysing data...")
        upload_stats, ip_stats, timestamps = analyse_data(logs)

        print("📈 Generating charts...")
        chart1_path, chart2_path = generate_graphs(upload_stats, ip_stats)

        print("📝 Creating PDF report...")
        create_pdf_report(upload_stats, ip_stats, timestamps, chart1_path, chart2_path)
