import os
import csv
import smtplib
from datetime import datetime
from email.message import EmailMessage
import matplotlib.pyplot as plt

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "Downtime_Log.csv")
URL_FILE = os.path.join(BASE_DIR, "Web_URLs.txt")
GMAIL_SETTINGS_FILE = os.path.join(BASE_DIR, "GmailSettings.txt")
GRAPH_FILE = os.path.join(BASE_DIR, "Daily_Outage_Graph.png")

def read_gmail_settings():
    try:
        with open(GMAIL_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if len(lines) >= 2: return lines[0], lines[1]
    except Exception:
        pass
    return None, None

def get_admin_emails():
    emails = set()
    try:
        with open(URL_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                parts = line.split()
                if len(parts) > 2:
                    raw_emails = "".join(parts[2:]).split(',')
                    for e in raw_emails:
                        if e.strip(): emails.add(e.strip())
    except Exception as e:
        print(f"Error reading emails: {e}")
    return list(emails)

def generate_daily_report():
    report_date = datetime.now().strftime('%Y-%m-%d')
    
    if not os.path.exists(CSV_FILE):
        print("No downtime data found.")
        return

    downtime_summary = {}
    detailed_logs = []
    
    with open(CSV_FILE, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Date"] == report_date:
                system_name = row["System_Name"]
                duration = float(row["Duration_Minutes"])
                
                if system_name in downtime_summary:
                    downtime_summary[system_name] += duration
                else:
                    downtime_summary[system_name] = duration
                
                detailed_logs.append(row)

    if not downtime_summary:
        print(f"No outages recorded for {report_date}.")
        return

    # --- 1. Graph Generation ---
    systems = list(downtime_summary.keys())
    durations = list(downtime_summary.values())
    
    plt.figure(figsize=(10, 6))
    plt.barh(systems, durations, color='lightcoral')
    plt.xlabel('Downtime (Minutes)')
    plt.title(f'Daily Outages - {report_date}')
    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    # --- 2. Email Body Generation ---
    body_text = f"Please find attached the daily SLA downtime report for all monitored web services and portals on {report_date}.\n\n"
    
    body_text += "=== TOTAL DOWNTIME SUMMARY ===\n"
    for sys_name, total_time in downtime_summary.items():
        body_text += f"{sys_name}: {round(total_time, 2)} Minutes\n"
    body_text += "==============================\n\n"
    
    body_text += "=== DETAILED OUTAGE LOGS (EVIDENCE) ===\n"
    for log in detailed_logs:
        body_text += f"System    : {log['System_Name']}\n"
        body_text += f"URL       : {log['URL']}\n"
        body_text += f"Down Time : {log['Down_Time']}\n"
        body_text += f"Up Time   : {log['Up_Time']}\n"
        body_text += f"Duration  : {log['Duration_Minutes']} Mins\n"
        body_text += f"Error     : {log['Reason']}\n"
        body_text += "-" * 40 + "\n"
        
    body_text += "\nSee the attached graph for a visual breakdown of today's outages."

    # --- 3. Send Email ---
    sender_email, app_password = read_gmail_settings()
    email_list = get_admin_emails()
    
    if not sender_email or not app_password or not email_list:
        return

    msg = EmailMessage()
    msg['Subject'] = f"[ATTENTION] Daily Web Services SLA Downtime Report - {report_date}"
    msg['From'] = f"IT Monitoring System <{sender_email}>"
    
    msg['To'] = email_list[0]
    if len(email_list) > 1:
        msg['Cc'] = ", ".join(email_list[1:])
        
    msg.set_content(body_text)

    if os.path.exists(GRAPH_FILE):
        with open(GRAPH_FILE, 'rb') as img:
            img_data = img.read()
            msg.add_attachment(img_data, maintype='image', subtype='png', filename=f"Outage_Graph_{report_date}.png")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        print("SLA Report sent successfully.")
    except Exception as e:
        print(f"Failed to send SLA report: {e}")

if __name__ == "__main__":
    generate_daily_report()