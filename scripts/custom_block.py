#!/usr/bin/env python3
import sys
import json
import subprocess

# --- Autonomous SOC: Active Response Script ---
# Function: Orchestrates an immediate firewall drop (UFW) based on high-confidence 
# telemetry received from the Wazuh Manager.
# ----------------------------------------------

def main():
    # 1. Ingest raw telemetry from Wazuh via stdin
    input_data = sys.stdin.readline()
    if not input_data:
        return

    try:
        alert = json.loads(input_data)

        # 2. Extract the malicious source IP from the alert data object
        # Target: data.srcip (e.g., from SSH Brute Force alerts)
        src_ip = alert.get("parameters", {}).get("alert", {}).get("data", {}).get("srcip")

        if src_ip:
            # 3. Execute 'The Terminator': Insert a high-priority DENY rule at the edge
            # Using absolute path for system security compliance
            subprocess.run(["/usr/sbin/ufw", "insert", "1", "deny", "from", src_ip])

            # 4. Persistence Logging: Maintain a local audit trail for incident response
            with open("/var/log/custom_terminator.log", "a") as log_file:
                log_file.write(f"[TERMINATOR] Action: DROP | Attacker IP: {src_ip}\n")

    except Exception as e:
        # Prevent script crashes on malformed JSON
        pass

if __name__ == "__main__":
    main()
