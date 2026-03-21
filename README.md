# 🛡️ Autonomous-AI-SOAR-Platform

### *End-to-End Threat Detection, AI-Contextualization, and Active Response*

<img width="1130" height="639" alt="soc-automation-architecture" src="https://github.com/user-attachments/assets/02bd3cb4-6f63-4a2e-a8a1-b83ae6f4b404" />


## 📌 Project Overview
This repository hosts a fully containerized, autonomous Security Operations Center (SOC) pipeline. It bridges the gap between raw telemetry and intelligent response by integrating **Wazuh (SIEM)**, **n8n (SOAR)**, and **Google Gemini (LLM)**.

The platform doesn't just detect threats; it triages them using real-time threat intelligence (**VirusTotal/AbuseIPDB**), generates human-readable executive and tactical reports via AI, and executes **Active Response** Python scripts to neutralize attackers at the edge.

---

## 🏗️ Technical Architecture
The entire core stack is deployed via **Docker**, ensuring high availability and modularity across the defensive pipeline.

*   **SIEM:** **Wazuh (Manager & Indexer)** — Centralized log analysis, security monitoring, and endpoint telemetry.
*   **SOAR Orchestrator:** **n8n (Self-hosted)** — The "Brain" of the operation; a modular workflow engine for automated incident response.
*   **Case Management:** **TheHive 5** — A centralized dashboard for incident tracking, forensic analysis, and audit compliance.
*   **Target Node (Ubuntu 24.04):** 
    *   **Web Stack:** Apache2 HTTP Server protected by **ModSecurity 3.0**.
    *   **WAF Integration:** Configured with the **OWASP Core Rule Set (CRS)** to detect and block SQL Injection (SQLi) and other OWASP Top 10 threats in real-time.
    *   **Telemetry:** Hardened with `auditd` (System Auditing) and the **Wazuh Agent** for File Integrity Monitoring (FIM) and log shipping.
*   **Attack Node:** **Kali Linux** — Dedicated environment for generating adversarial telemetry and testing playbook triggers.

---

## 🧠 The SOAR Logic (Hub & Spoke Model)
The automation engine is built on a **1+3 Modular Workflow** design in n8n, optimized for scalability and "Alert Fatigue" reduction.

### 1. Master Alert Dispatcher
Acts as the central router. It ingests Wazuh JSON webhooks, triages the alert based on the `rule.id` or `group`, and dispatches the payload to the correct specialized Playbook.

<img width="1850" height="766" alt="image" src="https://github.com/user-attachments/assets/9b416242-72c7-4622-ae7b-4597376caaed" />

### 2. Specialized Playbooks
*   **Auth Defense & Credential Access:** Handles SSH Brute Force (T1110). Includes a caching node to "Drop Duplicates" and enriches IP reputation via AbuseIPDB.

<img width="1847" height="793" alt="image" src="https://github.com/user-attachments/assets/8a2eaa31-8121-4898-afa5-c813d57b6904" />

*   **File Integrity & Malware Defense:** Monitors critical directories (`/var/www/html`, `/etc`). Uses a conditional logic gate ($ThreatScore > 0$) to trigger VirusTotal API lookups.

<img width="1852" height="800" alt="image" src="https://github.com/user-attachments/assets/92155bcc-1cb7-4d82-aaed-1ef3825dfef4" />

*   **Web Application Defense:** Triages Apache/ModSecurity logs to identify and block directory traversal and SQLi attempts

<img width="1850" height="799" alt="image" src="https://github.com/user-attachments/assets/5e7368bd-c7df-40ce-9342-ca39fce00fae" />

---

## 🐍 Custom Active Response (Python)
I developed specialized Python scripts to move the platform from "Passive Monitoring" to "Active Defense." These scripts reside on the **Ubuntu Victim** agent and are triggered by the Wazuh Manager.

### 1. `web-blocker.py` (Progressive Defense)
*   **Logic:** Maintains a local JSON state (`web_offenders.json`) to track "Strikes."
*   **Behavior:** Strike 1 (60s block) → Strike 2 (300s) → Strike 3 (Permanent/1hr).
*   **Mechanism:** Performs a "Secret Handshake" with Wazuh 4.x and executes `UFW` commands to insert deny rules.

### 2. `custom_block.py` (The Terminator)
*   **Logic:** Designed for high-confidence SSH brute-force attacks.
*   **Behavior:** Instantly triggers a `UFW` block upon a specific alert ID and logs actions to `/var/log/custom_terminator.log`.

---

---

## 🤖 AI-Powered Contextualization & Alerting
This platform solves the "Context Gap" by using **Google Gemini** to translate raw technical JSON telemetry into actionable intelligence for different stakeholders. 

### 🕵️ Tactical Alert (Slack)
**Audience:** SOC Analysts / Incident Responders  
**Content:** MITRE ATT&CK Mapping, Enriched IoCs (VirusTotal/AbuseIPDB), and "Next Step" commands for immediate triage.

<img width="1919" height="859" alt="image" src="https://github.com/user-attachments/assets/2097079a-d0a6-429e-a49b-4eb3e1511ae7" />

---

### 📈 Executive Brief (Email)
**Audience:** CISOs / Management  
**Content:** Risk-based business impact summary, plain-English incident description, and resolution status.

<img width="1919" height="891" alt="image" src="https://github.com/user-attachments/assets/a7cbd280-1947-4734-961e-fc2630427280" />

---

## 📂 Incident Case Management: TheHive 5
To ensure full auditability and compliance, the SOAR pipeline automatically logs every triaged alert into **TheHive**. This removes the manual burden of case creation and ensures that incident responders have a centralized dashboard for investigation.

![TheHive Dashboard](docs/thehive-dashboard.png)

### 🛠️ Key Case Management Features:
*   **Automated Case Creation:** n8n dynamically generates cases with standardized naming conventions (e.g., `SOC Incident: Malware Detected`).
*   **Categorization & Tagging:** Alerts are automatically tagged by threat type (`brute-force`, `web`, `syscheck`, `malware`) and mapped to MITRE ATT&CK TTPs (e.g., `T1565.001`).
*   **Observable Attachment:** Malicious IPs and file hashes are attached as "Observables," allowing for rapid pivoting during forensic analysis.
*   **Intelligent Triage (Incident vs. Audit):** To prevent alert fatigue, the pipeline uses a Logic Gate ($ThreatScore > 0$) to differentiate the logging path:
    *   **SOC Incident (High/Medium Severity):** Triggered by confirmed malicious hashes. Launches the full AI-reporting and multi-channel alerting chain.
    *   **SOC Audit (Low Severity):** Triggered when a hash is **unique or unknown**. The system creates a "Silent" Audit Case for forensic record-keeping without firing intrusive Slack/Email alerts.

![Malware Triage Logic](docs/malware-playbook-logic.png)

---

## ⚔️ Attack Emulation & Playbook Validation
I executed a range of adversarial techniques—both from external nodes (Kali) and simulated internal compromises—to validate the end-to-end detection-to-response loop for each specialized playbook.

### 1. Auth Defense & Credential Access (MITRE T1110)
*   **External Attack:** SSH Brute Force using Hydra.
    `hydra -l ubuntu-victim -P /usr/share/wordlists/rockyou.txt ssh://192.168.68.113`
*   **🛡️ Response:** Wazuh `Rule 100050` detects 4+ failures within 120s. n8n triggers the **Auth Defense Playbook**, executing a permanent UFW block via `custom_block.py` and alerting the SOC via Slack.

### 2. Web Application Defense (Apache + ModSecurity)
*   **External Attack:** SQL Injection (SQLi) payload delivery.
    `curl "http://192.168.68.113/?id=1'+UNION+SELECT+username,password+FROM+users--"`
*   **🛡️ Response:** ModSecurity identifies the critical anomaly (Score 23). Wazuh generates a high-severity alert. n8n triggers the **Web Defense Playbook**, executing the `web-blocker.py` script.
*   **Active Defense:** The attacker's IP is dynamically added to the `UFW` (Uncomplicated Firewall) drop list, effectively "killing" the session before the injection reaches the database logic.

### 3. File Integrity & Malware Defense (MITRE T1565)
*   **Malicious Ingress (External Download):** 
    `wget -O /tmp/eicar.com https://secure.eicar.org/eicar.com.txt`
*   **Remote Payload Push (via SSH):** 
    `echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' | ssh 192.168.68.107 "cat > /tmp/eicar_push.com"`
*   **Benign File Creation (Audit Test):** 
    `echo "Normal website configuration." > /tmp/normal_file.txt`
*   **🛡️ Response:** Wazuh `syscheck` (FIM) detects the file modification. n8n performs a VirusTotal hash lookup. **EICAR strings** return a high threat score, triggering an **Incident** in TheHive. **Benign files** (Threat Score = 0) are silently logged as **Audits** for forensic record-keeping.

## 🚀 How to Explore this Project
I have included all technical logic files in this repo for community exploration:

1.  **/n8n:** Import the `.json` files into your n8n instance to view the workflow logic.
2.  **/scripts:** Review the Python logic for the Active Response scripts.
3.  **/wazuh:** Contains the custom `ossec.conf` and Wazuh XML rules.
4.  **/docker:** Use the `docker-compose.yml` to spin up the core stack.

> **Note:** For security, all API keys and private IPs have been replaced with `{{PLACEHOLDERS}}`.

---

### 🤝 Connect with me
*   **LinkedIn:** [Your Link Here]
*   **GitHub:** [Your Link Here]
