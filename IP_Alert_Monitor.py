import os
import subprocess
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IP_FILE = os.path.join(BASE_DIR, "ips.txt")
GMAIL_SETTINGS_FILE = os.path.join(BASE_DIR, "GmailSettings.txt")
STATE_FILE = os.path.join(BASE_DIR, "IP_State.txt")

def read_gmail_settings():
    try:
        with open(GMAIL_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if len(lines) >= 2:
                return lines[0], lines[1]
    except Exception:
        pass
    return None, None

def read_targets():
    targets = []
    try:
        with open(IP_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    ip = parts[0]
                    name = parts[1]
                    raw_emails = "".join(parts[2:]).split(',') if len(parts) > 2 else []
                    emails = [e.strip() for e in raw_emails if e.strip()]
                    targets.append({'ip': ip, 'name': name, 'emails': emails})
    except Exception as e:
        print(f"Error reading {IP_FILE}: {e}")
    return targets

def send_alert(subject, body, email_list):
    if not email_list:
        return
    sender_email, app_password = read_gmail_settings()
    if not sender_email or not app_password:
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"IT Monitoring System <{sender_email}>"
    
    # ???? ????? ?????? To ?????, ????? ??? ?????? Cc ????? ?????
    msg['To'] = email_list[0]
    if len(email_list) > 1:
        msg['Cc'] = ", ".join(email_list[1:])
        
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

def load_state():
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    state[parts[0]] = {'status': parts[1], 'time': parts[2]}
    return state

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        for ip, data in state.items():
            f.write(f"{ip},{data['status']},{data['time']}\n")

def check_ips():
    targets = read_targets()
    state = load_state()
    
    for t in targets:
        ip = t['ip']
        name = t['name']
        emails = t['emails']
        
        current_time = datetime.now()
        current_time_str = current_time.strftime('%H:%M:%S')
        today_date = current_time.strftime('%Y-%m-%d')
        
        response = subprocess.run(['ping', '-c', '1', '-W', '2', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = "UP" if response.returncode == 0 else "DOWN"
        
        prev_state = state.get(ip, {'status': 'UP', 'time': current_time_str})
        
        if status == "DOWN" and prev_state['status'] == "UP":
            subject = f"[ALERT] Network Device Down: {name}"
            body = f"ALERT TYPE: Device Offline\nTARGET: {ip}\nDESCRIPTION: {name}\nTIMESTAMP: {today_date} {current_time_str}\n\nPlease check immediately."
            send_alert(subject, body, emails)
            state[ip] = {'status': 'DOWN', 'time': current_time_str}
            
        elif status == "UP" and prev_state['status'] == "DOWN":
            down_time_str = prev_state['time']
            down_time_obj = datetime.strptime(down_time_str, '%H:%M:%S')
            duration = (current_time - current_time.replace(hour=down_time_obj.hour, minute=down_time_obj.minute, second=down_time_obj.second)).total_seconds() / 60.0
            
            subject = f"[RESOLVED] Network Device Up: {name}"
            body = f"ALERT TYPE: Device Restored\nTARGET: {ip}\nDESCRIPTION: {name}\nDOWNTIME DURATION: {round(duration, 2)} Minutes\nRESTORED AT: {today_date} {current_time_str}"
            send_alert(subject, body, emails)
            state[ip] = {'status': 'UP', 'time': current_time_str}

    save_state(state)

if __name__ == "__main__":
    check_ips()