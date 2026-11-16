import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import urllib3
import os
import csv
import time

# SSL Certificate Warnings ????????
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL_FILE = os.path.join(BASE_DIR, "Web_URLs.txt")
STATE_FILE = os.path.join(BASE_DIR, "Web_State.txt")
CSV_FILE = os.path.join(BASE_DIR, "Downtime_Log.csv")
GMAIL_SETTINGS_FILE = os.path.join(BASE_DIR, "GmailSettings.txt")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# =======================================================

def read_gmail_settings():
    try:
        with open(GMAIL_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if len(lines) >= 2: return lines[0], lines[1]
    except Exception:
        pass
    return None, None

def load_previous_states():
    states = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    status = parts[1]
                    down_time = parts[2] if len(parts) > 2 else ""
                    reason = parts[3] if len(parts) > 3 else ""
                    states[parts[0]] = {'status': status, 'down_time': down_time, 'reason': reason}
    return states

def save_current_states(states):
    with open(STATE_FILE, 'w') as f:
        for name, data in states.items():
            f.write(f"{name},{data['status']},{data['down_time']},{data['reason']}\n")

def write_to_csv(name, url, down_time_str, up_time_str, reason):
    file_exists = os.path.exists(CSV_FILE)
    try:
        down_time = datetime.strptime(down_time_str, '%Y-%m-%d %H:%M:%S')
        up_time = datetime.strptime(up_time_str, '%Y-%m-%d %H:%M:%S')
        duration_mins = round((up_time - down_time).total_seconds() / 60.0, 2)
        date_str = down_time.strftime('%Y-%m-%d')
    except Exception:
        return

    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'System_Name', 'URL', 'Down_Time', 'Up_Time', 'Duration_Minutes', 'Reason'])
        writer.writerow([date_str, name, url, down_time_str, up_time_str, duration_mins, reason])

def send_alert(target_url, name, status, reason, emails, sender_email, app_password):
    if not sender_email or not app_password:
        return

    if status == "DOWN":
        subject = f"[ALERT] Web Service Down: {name}"
        status_text = "Service Outage"
    else:
        subject = f"[RESOLVED] Web Service Up: {name}"
        status_text = "Service Recovered"

    body = f"""ALERT TYPE: {status_text}
TARGET: {target_url}
DESCRIPTION: {name}
STATUS: {reason}
TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check.
"""
    msg = MIMEMultipart()
    msg['From'] = f"IT Monitoring System <{sender_email}>"
    msg['To'] = emails
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, app_password)
        email_list = [e.strip() for e in emails.split(',') if e.strip()]
        server.sendmail(sender_email, email_list, msg.as_string())
        server.quit()
        print(f"[{status}] Email sent for {name}")
    except Exception as e:
        print(f"[ERROR] Failed to send email for {name}: {e}")

def main():
    print("=========================================")
    print(f"Web Alert Monitor Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=========================================")
    
    sender_email, app_password = read_gmail_settings()
    if not sender_email or not app_password:
        print(f"[ERROR] Could not read email credentials from {GMAIL_SETTINGS_FILE}")
        return

    try:
        with open(URL_FILE, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"URL File not found: {URL_FILE}")
        return

    previous_states = load_previous_states()
    current_states = {}

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split()
        if len(parts) >= 3:
            url = parts[0]
            name = parts[1]
            
            raw_emails = "".join(parts[2:])
            emails = raw_emails.replace(" ", "").rstrip(',')
            
            if not url.startswith('http'):
                url = 'https://' + url

            status = "UP"
            reason = "200 - OK"
            current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                resp = requests.get(url, timeout=15, verify=False, headers=headers)
                if resp.status_code != 200:
                    status = "DOWN"
                    reason = f"{resp.status_code} - HTTP Error"
            except requests.exceptions.RequestException:
                status = "DOWN"
                reason = "000 - Connection Failed / Timeout"
            
            prev_data = previous_states.get(name, {'status': 'UP', 'down_time': '', 'reason': ''})
            prev_status = prev_data['status']
            
            current_data = {'status': status, 'down_time': prev_data['down_time'], 'reason': prev_data['reason']}
            
            if status != prev_status:
                if status == "DOWN":
                    current_data['down_time'] = current_time_str
                    current_data['reason'] = reason
                    send_alert(url, name, status, reason, emails, sender_email, app_password)
                elif status == "UP":
                    if prev_data['down_time']:
                        write_to_csv(name, url, prev_data['down_time'], current_time_str, prev_data['reason'])
                    current_data['down_time'] = "" 
                    current_data['reason'] = ""
                    send_alert(url, name, status, reason, emails, sender_email, app_password)
            else:
                print(f"No change for {name}: currently {status}")
                
            current_states[name] = current_data

    save_current_states(current_states)
    print("=========================================")
    print("Monitoring Completed.")

if __name__ == "__main__":
    main()