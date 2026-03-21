#!/usr/bin/python3
import sys
import json
import os
import subprocess
from datetime import datetime

# --- Autonomous SOC: Progressive Web Defense ---
# Logic: Implements a "Three-Strike" system for web offenders.
# Response: Strike 1 (60s) | Strike 2 (300s) | Strike 3 (3600s/Permanent)
# ----------------------------------------------

LOG_FILE = "/var/ossec/logs/active-responses.log"
DATABASE = "/var/ossec/active-response/web_offenders.json"

def log(msg):
    """Maintains an audit trail in the standard Wazuh AR log."""
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - [WEB-BLOCKER] {msg}\n")

def send_handshake(command):
    """Executes the Wazuh 4.x JSON handshake protocol to maintain session state."""
    payload = {
        "version": 1,
        "origin": {"name": "web-blocker", "module": "active-response"},
        "command": command,
        "parameters": {}
    }
    print(json.dumps(payload))
    sys.stdout.flush()

def main():
    # 1. Ingest alert from Wazuh Manager
    try:
        input_str = sys.stdin.readline()
        if not input_str:
            return
        msg = json.loads(input_str)
    except Exception as e:
        log(f"JSON Parsing Error: {e}")
        return

    # 2. Required 'continue' handshake for Wazuh 4.x integration
    send_handshake("continue")

    # 3. Extract source IP from the nested telemetry object
    alert = msg.get("parameters", {}).get("alert", {})
    src_ip = alert.get("data", {}).get("srcip")

    if not src_ip:
        log("Triage Failed: No source IP identified in alert payload.")
        return

    # 4. State Management: Track offender history via local JSON DB
    if os.path.exists(DATABASE):
        with open(DATABASE, "r") as f:
            try:
                db = json.load(f)
            except:
                db = {}
    else:
        db = {}

    # Update strike count
    count = db.get(src_ip, 0) + 1
    db[src_ip] = count
    with open(DATABASE, "w") as f:
        json.dump(db, f)

    # 5. Progressive Blocking Logic (Timeout in seconds)
    # Strike 1: 1 Min | Strike 2: 5 Mins | Strike 3+: 1 Hour
    timeout = 60 if count == 1 else 300 if count == 2 else 3600

    # 6. Defensive Action: Inject high-priority UFW deny rule
    log(f"THREAT NEUTRALIZED: Blocking {src_ip} for {timeout}s (Strike #{count})")
    subprocess.run(["sudo", "/usr/sbin/ufw", "insert", "1", "deny", "from", src_ip])
    
    # 7. Self-Healing: Automated background unblock after timeout
    unblock_cmd = f"sleep {timeout} && sudo /usr/sbin/ufw delete deny from {src_ip}"
    subprocess.Popen(unblock_cmd, shell=True)

if __name__ == "__main__":
    main()
