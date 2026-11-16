# 🚀 Custom Automated IT Monitoring & SLA Reporting System

Welcome to the **Automated IT Monitoring System**! This is a lightweight, fully automated, and highly efficient solution built with Python. It monitors both Network Devices (via ICMP Ping) and Web Services (via HTTP status), sends real-time email alerts only upon state changes (to prevent spam), logs exact downtime durations, and automatically generates a daily graphical SLA report.

මෙය Python භාවිතයෙන් මුල සිටම නිර්මාණය කළ සැහැල්ලු හා කාර්යක්ෂම IT Monitoring පද්ධතියකි. මින් Network Devices සහ Web Services ස්වයංක්‍රීයව නිරීක්ෂණය කර, බිඳවැටීම් (Outages) වලදී තත්‍ය කාලීන ඊමේල් දැනුම්දීම් සිදුකරන අතර (අනවශ්‍ය Spam ඊමේල් වළක්වමින්), දිනපතා SLA වාර්තාවක්ද ග්‍රාෆ් එකක් සමඟ ස්වයංක්‍රීයව ජෙනරේට් කරනු ලබයි.

---

## 📂 1. Directory Structure (ෆෝල්ඩර් සහ ෆයිල් සැකැස්ම)

Keep all the files in a single directory (e.g., `/etc/NWCHK/IP_Monitor/` or any folder in Windows).
සියලුම ෆයිල් පහත පරිදි එකම ෆෝල්ඩරයක් ඇතුළත තබා ගන්න.

```text
IP_Monitor/
│
├── Web_Alert_Monitor.py       # (Script) Monitors Web URLs
├── IP_Alert_Monitor.py        # (Script) Monitors Network/LAN IPs
├── Daily_SLA_Report.py        # (Script) Generates Daily SLA Report
│
├── GmailSettings.txt          # (Config) Contains Sender Email Credentials
├── Web_URLs.txt               # (Config) Target URLs and notification emails
├── ips.txt                    # (Config) Target IPs and notification emails
│
└── (Auto-generated files / ස්වයංක්‍රීයව හැදෙන ෆයිල්)
    ├── Web_State.txt          # Tracks Web URL up/down states
    ├── IP_State.txt           # Tracks Network IP up/down states
    ├── Downtime_Log.csv       # Database logging all outages
    └── Daily_Outage_Graph.png # Generated graph for SLA report
```

---

## ⚙️ 2. Configuration Files Setup (සැකසුම් ගොනු සෑදීම)

You must create these three text files before running the scripts.
ස්ක්‍රිප්ට් ධාවනය කිරීමට පෙර මෙම ෆයිල් 3 අනිවාර්යයෙන්ම නිර්මාණය කරගත යුතුය.

### 2.1 `GmailSettings.txt`
Put your sender email and App Password here. **Do not use your regular Gmail password.** Generate a 16-digit App Password from Google Account Security settings.
අලර්ට් යැවීමට භාවිතා කරන ඊමේල් ලිපිනය සහ එහි App Password එක මෙහි ලබාදෙන්න. (සාමාන්‍ය පාස්වර්ඩ් එක නොව App Password එකක් සාදාගත යුතුය).

```text
your_monitoring_email@gmail.com
abcd1234efgh5678
```

### 2.2 `Web_URLs.txt`
List of websites to monitor. Format: `[URL]  [System_Name]  [Emails]`
මොනිටර් කළ යුතු වෙබ් අඩවි මෙහි ඇතුලත් කරන්න. හිස්තැන් (Spaces) සහිත නම් භාවිතා නොකරන්න.

```text
# --- VIP Web Systems ---
https://erp.yourcompany.com      Company_ERP            admin1@domain.com, manager@domain.com
https://www.yourwebsite.com      Public_Website         admin1@domain.com
```

### 2.3 `ips.txt`
List of IPs (Servers/Routers/Firewalls) to monitor. Format: `[IP]  [Device_Name]  [Emails]`
මොනිටර් කළ යුතු Network Devices වල IP ලිපින මෙහි ඇතුලත් කරන්න.

```text
# --- Core Network Devices ---
192.168.1.1       Main_Firewall          admin@domain.com
124.43.x.x        Main_Branch_Router     admin@domain.com, tech@domain.com
```

---

## 💻 3. The Source Code (පයිතන් කේතයන්)

Here are the complete Python scripts with detailed bilingual comments.
මෙන්න සියලුම පයිතන් කෝඩ්, පැහැදිලි සිංහල සහ ඉංග්‍රීසි අදහස් (Comments) සමඟින්.

### 3.1 `Web_Alert_Monitor.py`
Monitors web applications and logs exact downtime.

```python
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import urllib3
import os
import csv

# Disable SSL Certificate Warnings / SSL Warnings මඟහරින්න
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- File Paths / ෆයිල් තියෙන ස්ථාන ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL_FILE = os.path.join(BASE_DIR, "Web_URLs.txt")
STATE_FILE = os.path.join(BASE_DIR, "Web_State.txt")
CSV_FILE = os.path.join(BASE_DIR, "Downtime_Log.csv")
GMAIL_SETTINGS_FILE = os.path.join(BASE_DIR, "GmailSettings.txt")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def read_gmail_settings():
    # Read sender email and password / ඊමේල් සැකසුම් කියවීම
    try:
        with open(GMAIL_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if len(lines) >= 2: return lines[0], lines[1]
    except Exception:
        pass
    return None, None

def load_previous_states():
    # Load previous UP/DOWN states from file / කලින් තිබූ තත්ත්වය කියවීම
    states = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    states[parts[0]] = {
                        'status': parts[1], 
                        'down_time': parts[2] if len(parts) > 2 else "", 
                        'reason': parts[3] if len(parts) > 3 else ""
                    }
    return states

def save_current_states(states):
    # Save the updated states / අලුත් තත්ත්වය සේව් කිරීම
    with open(STATE_FILE, 'w') as f:
        for name, data in states.items():
            f.write(f"{name},{data['status']},{data['down_time']},{data['reason']}\n")

def write_to_csv(name, url, down_time_str, up_time_str, reason):
    # Log the exact outage duration to CSV / බිඳවැටුණු කාලය CSV එකට ලිවීම
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
    # Send Email Alerts via Gmail SMTP / ඊමේල් අලර්ට් යැවීම
    if not sender_email or not app_password: return

    if status == "DOWN":
        subject = f"[ALERT] Web Service Down: {name}"
        status_text = "Service Outage"
    else:
        subject = f"[RESOLVED] Web Service Restored: {name}"
        status_text = "Service Recovered"

    body = f"ALERT TYPE: {status_text}\nTARGET: {target_url}\nDESCRIPTION: {name}\nSTATUS: {reason}\nTIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nPlease check."
    
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
    except Exception as e:
        print(f"Email failed for {name}: {e}")

def main():
    sender_email, app_password = read_gmail_settings()
    if not sender_email or not app_password: return

    try:
        with open(URL_FILE, 'r') as f: lines = f.readlines()
    except FileNotFoundError: return

    previous_states = load_previous_states()
    current_states = {}

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'): continue
        
        parts = line.split()
        if len(parts) >= 3:
            url, name = parts[0], parts[1]
            emails = "".join(parts[2:]).replace(" ", "").rstrip(',')
            if not url.startswith('http'): url = 'https://' + url

            status, reason = "UP", "200 - OK"
            current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 1. Check Website HTTP Status / වෙබ් අඩවිය වැඩදැයි පරීක්ෂා කිරීම
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                resp = requests.get(url, timeout=15, verify=False, headers=headers)
                if resp.status_code != 200:
                    status, reason = "DOWN", f"{resp.status_code} - HTTP Error"
            except:
                status, reason = "DOWN", "000 - Connection Failed / Timeout"
            
            prev_data = previous_states.get(name, {'status': 'UP', 'down_time': '', 'reason': ''})
            
            # 2. Smart State Tracking - Alert ONLY if state changes / තත්ත්වය වෙනස් වුවහොත් පමණක් ක්‍රියාත්මක වීම
            current_data = {'status': status, 'down_time': prev_data['down_time'], 'reason': prev_data['reason']}
            
            if status != prev_data['status']:
                if status == "DOWN":
                    current_data['down_time'], current_data['reason'] = current_time_str, reason
                    send_alert(url, name, status, reason, emails, sender_email, app_password)
                elif status == "UP":
                    # If recovered, write to CSV / යථා තත්ත්වයට පත්වූ පසු CSV එකට ලිවීම
                    if prev_data['down_time']:
                        write_to_csv(name, url, prev_data['down_time'], current_time_str, prev_data['reason'])
                    current_data['down_time'], current_data['reason'] = "", ""
                    send_alert(url, name, status, reason, emails, sender_email, app_password)
                    
            current_states[name] = current_data

    # Save final states / අවසාන තත්ත්වය සුරැකීම
    save_current_states(current_states)

if __name__ == "__main__":
    main()
```

### 3.2 `IP_Alert_Monitor.py`
Monitors ICMP Ping for local and public IP addresses.

```python
import os
import subprocess
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- File Paths / ෆයිල් තියෙන ස්ථාන ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IP_FILE = os.path.join(BASE_DIR, "ips.txt")
GMAIL_SETTINGS_FILE = os.path.join(BASE_DIR, "GmailSettings.txt")
STATE_FILE = os.path.join(BASE_DIR, "IP_State.txt")

def read_gmail_settings():
    # Read credentials / සැකසුම් කියවීම
    try:
        with open(GMAIL_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if len(lines) >= 2: return lines[0], lines[1]
    except: pass
    return None, None

def send_alert(subject, body, email_list):
    # Send alerts / අලර්ට් යැවීම
    if not email_list: return
    sender_email, app_password = read_gmail_settings()
    if not sender_email or not app_password: return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"IT Monitoring System <{sender_email}>"
    msg['To'] = email_list[0]
    if len(email_list) > 1: msg['Cc'] = ", ".join(email_list[1:])
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
    except: pass

def check_ips():
    # Load targets and previous state / අයිපී ලිපින සහ පරණ තත්ත්වය කියවීම
    targets, state = [], {}
    try:
        with open(IP_FILE, 'r') as f:
            for line in f:
                if not line.strip() or line.startswith('#'): continue
                parts = line.split()
                if len(parts) >= 2:
                    emails = [e.strip() for e in "".join(parts[2:]).split(',') if e.strip()] if len(parts) > 2 else []
                    targets.append({'ip': parts[0], 'name': parts[1], 'emails': emails})
    except: return

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3: state[parts[0]] = {'status': parts[1], 'time': parts[2]}
    
    # 1. Process PING / Ping කිරීම
    for t in targets:
        ip, name, emails = t['ip'], t['name'], t['emails']
        current_time = datetime.now()
        current_time_str = current_time.strftime('%H:%M:%S')
        today_date = current_time.strftime('%Y-%m-%d')
        
        # Ping Command (Works for Linux. For windows change -c to -n and -W to -w)
        response = subprocess.run(['ping', '-c', '1', '-W', '2', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = "UP" if response.returncode == 0 else "DOWN"
        prev_state = state.get(ip, {'status': 'UP', 'time': current_time_str})
        
        # 2. Trigger Alerts on change / වෙනසක් වුවහොත් අලර්ට් යැවීම
        if status == "DOWN" and prev_state['status'] == "UP":
            send_alert(f"[ALERT] Device Down: {name}", f"TARGET: {ip}\nSTATUS: Offline", emails)
            state[ip] = {'status': 'DOWN', 'time': current_time_str}
            
        elif status == "UP" and prev_state['status'] == "DOWN":
            send_alert(f"[RESOLVED] Device Up: {name}", f"TARGET: {ip}\nSTATUS: Restored", emails)
            state[ip] = {'status': 'UP', 'time': current_time_str}

    # Save State / තත්ත්වය සේව් කිරීම
    with open(STATE_FILE, 'w') as f:
        for ip, data in state.items(): f.write(f"{ip},{data['status']},{data['time']}\n")

if __name__ == "__main__":
    check_ips()
```

### 3.3 `Daily_SLA_Report.py`
Reads the `Downtime_Log.csv`, generates a bar chart via `matplotlib`, and emails the management. 
*(Prerequisite: `pip install matplotlib`)*

```python
import os, csv, smtplib
from datetime import datetime
from email.message import EmailMessage
import matplotlib.pyplot as plt

# --- File Paths / ෆයිල් තියෙන ස්ථාන ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "Downtime_Log.csv")
URL_FILE = os.path.join(BASE_DIR, "Web_URLs.txt")
GMAIL_SETTINGS_FILE = os.path.join(BASE_DIR, "GmailSettings.txt")
GRAPH_FILE = os.path.join(BASE_DIR, "Daily_Outage_Graph.png")

def get_admin_emails():
    # Extract all recipient emails from URL config / සියලුම ඊමේල් ලබා ගැනීම
    emails = set()
    try:
        with open(URL_FILE, 'r') as f:
            for line in f:
                if not line.strip() or line.startswith('#'): continue
                parts = line.split()
                if len(parts) > 2:
                    for e in "".join(parts[2:]).split(','):
                        if e.strip(): emails.add(e.strip())
    except: pass
    return list(emails)

def generate_daily_report():
    report_date = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(CSV_FILE): return

    # 1. Calculate Total Downtimes from CSV / බිඳවැටුණු සම්පූර්ණ කාලය ගණනය කිරීම
    downtime_summary, detailed_logs = {}, []
    with open(CSV_FILE, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Date"] == report_date:
                sys_name, dur = row["System_Name"], float(row["Duration_Minutes"])
                downtime_summary[sys_name] = downtime_summary.get(sys_name, 0) + dur
                detailed_logs.append(row)

    if not downtime_summary: return

    # 2. Generate Bar Chart Graph / ග්‍රාෆ් එක නිර්මාණය කිරීම
    plt.figure(figsize=(10, 6))
    plt.barh(list(downtime_summary.keys()), list(downtime_summary.values()), color='lightcoral')
    plt.xlabel('Downtime (Minutes)')
    plt.title(f'Daily Outages - {report_date}')
    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    # 3. Create Email Body / ඊමේල් පණිවිඩය සැකසීම
    body_text = f"SLA Downtime Report for {report_date}.\n\n=== SUMMARY ===\n"
    for sys, time in downtime_summary.items(): body_text += f"{sys}: {round(time, 2)} Mins\n"
    body_text += "\n=== DETAILS ===\n"
    for log in detailed_logs:
        body_text += f"{log['System_Name']} | Duration: {log['Duration_Minutes']} Mins | Error: {log['Reason']}\n"

    # 4. Send Email with Attachment / ග්‍රාෆ් එක සමඟ ඊමේල් යැවීම
    with open(GMAIL_SETTINGS_FILE, 'r') as f:
        sender, pwd = [l.strip() for l in f.readlines()[:2]]
    email_list = get_admin_emails()
    
    msg = EmailMessage()
    msg['Subject'] = f"Daily SLA Downtime Report - {report_date}"
    msg['From'], msg['To'] = sender, email_list[0]
    if len(email_list) > 1: msg['Cc'] = ", ".join(email_list[1:])
    msg.set_content(body_text)

    with open(GRAPH_FILE, 'rb') as img:
        msg.add_attachment(img.read(), maintype='image', subtype='png', filename="SLA_Graph.png")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, pwd)
        server.send_message(msg)

if __name__ == "__main__":
    generate_daily_report()
```

---

## ⏱️ 4. Deployment (ක්‍රියාත්මක කිරීම)

### 4.1 On Linux Server (Cron Jobs)
Open terminal and edit crontab: `crontab -e` (ලිනක්ස් සර්වර් එකක නම් Cron Jobs මගින්)

```bash
# Run Web Monitor every 5 minutes (විනාඩි 5න් 5ට ධාවනය වේ)
*/5 * * * * cd /etc/NWCHK/IP_Monitor && /usr/bin/python3 Web_Alert_Monitor.py

# Run Network Monitor every 5 minutes (විනාඩි 5න් 5ට ධාවනය වේ)
*/5 * * * * cd /etc/NWCHK/IP_Monitor && /usr/bin/python3 IP_Alert_Monitor.py

# Send SLA Report at 11:55 PM daily (දිනපතා රාත්‍රී 11:55 ට ධාවනය වේ)
55 23 * * * cd /etc/NWCHK/IP_Monitor && /usr/bin/python3 Daily_SLA_Report.py
```

### 4.2 On Windows Machine
You can use the **Windows Task Scheduler** to trigger these Python scripts at the same intervals. Or convert them to `.exe` files using `PyInstaller`.
(Windows පරිගණකයක නම් Windows Task Scheduler භාවිතා කරන්න, නැතහොත් `pyinstaller --onefile` මගින් `.exe` බවට පත්කර ධාවනය කළ හැක).