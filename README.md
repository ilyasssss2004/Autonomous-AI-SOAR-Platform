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

<img width="1850" height="766" alt="Master Alert Router Logic" src="https://github.com/user-attachments/assets/9b416242-72c7-4622-ae7b-4597376caaed" />

### 2. Specialized Playbooks
*   **Auth Defense & Credential Access:** Handles SSH Brute Force (T1110). Includes a caching node to "Drop Duplicates" and enriches IP reputation via AbuseIPDB.
*   **File Integrity & Malware Defense:** Monitors critical directories (`/var/www/html`, `/etc`). Uses a conditional logic gate ($ThreatScore > 0$) to trigger VirusTotal API lookups.
*   **Web Application Defense:** Triages Apache/ModSecurity logs to identify and block directory traversal and SQLi attempts.

---

## 🐍 Custom Active Response (Python)
I developed specialized Python scripts to move the platform from "Passive Monitoring" to "Active Defense." These scripts reside on the **Ubuntu Victim** agent and are triggered by the Wazuh Manager.

### 1. `web-blocker.py` (Progressive Defense)
*   **Logic:** Maintains a local JSON state (`web_offenders.json`) to track "Strikes."
*   **Behavior:** Strike 1 (60s block) → Strike 2 (300s) → Strike 3 (Permanent/1hr).
*   **Mechanism:** Performs a "Secret Handshake" with Wazuh 4.x and executes `UFW` (Uncomplicated Firewall) commands to insert deny rules.

### 2. `custom_block.py` (The Terminator)
*   **Logic:** Designed for high-confidence SSH brute-force attacks.
*   **Behavior:** Instantly triggers a `UFW` block upon a specific alert ID and logs actions to `/var/log/custom_terminator.log`.

---

## 🤖 AI-Powered Contextualization & Alerting
This platform solves the "Context Gap" by using **Google Gemini** to translate raw technical JSON telemetry into actionable intelligence for different stakeholders. 

### 🕵️ Tactical Alert (Slack)
**Audience:** SOC Analysts / Incident Responders  
**Content:** MITRE ATT&CK Mapping, Enriched IoCs (VirusTotal/AbuseIPDB), and "Next Step" commands for immediate triage.

<img width="1919" height="859" alt="Slack Tactical Alert" src="https://github.com/user-attachments/assets/2097079a-d0a6-429e-a49b-4eb3e1511ae7" />

---

### 📈 Executive Brief (Email)
**Audience:** CISOs / Management  
**Content:** Risk-based business impact summary, plain-English incident description, and resolution status.

<img width="1919" height="891" alt="Executive Email Report" src="https://github.com/user-attachments/assets/a7cbd280-1947-4734-961e-fc2630427280" />

---

## 📂 Incident Case Management: TheHive 5
To ensure full auditability and compliance, the SOAR pipeline automatically logs every triaged alert into **TheHive**.

<img width="1854" height="803" alt="TheHive Case Management Dashboard" src="https://github.com/user-attachments/assets/d9d7125a-e74c-4d1c-8d78-d710cf8e90c2" />

### 🛠️ Key Case Management Features:
*   **Automated Case Creation:** n8n dynamically generates cases with standardized naming conventions (e.g., `SOC Incident: Malware Detected`).
*   **Intelligent Triage Logic:** Within the **File Integrity & Malware Defense Sub-workflow**, the pipeline utilizes a conditional Logic Gate based on the $ThreatScore$ derived from VirusTotal API responses:
    *   **SOC Incident (Score > 0):** High/Medium severity. Launches the full AI-reporting chain and multi-channel alerting.
    *   **SOC Audit (Score = 0):** Creates a "Silent" Audit Case for forensic record-keeping without firing intrusive notifications.

<img width="1850" height="797" alt="Malware Incident Flow" src="https://github.com/user-attachments/assets/a51ea94a-383c-4345-a834-729cd8ab02a4" />

---

## ⚔️ Attack Emulation & Playbook Validation
Each playbook was validated using real-world adversarial techniques from an external Kali Linux node.

### 1. Auth Defense (MITRE T1110)
*   **Attack:** SSH Brute Force using Hydra.
    `hydra -l victim_user -P /path/to/wordlist.txt ssh://192.168.1.X`
*   **🛡️ Response:** Wazuh detects 4+ failures. n8n triggers the **Auth Defense Playbook**, executing a UFW block via `custom_block.py`.

### 2. Web Application Defense (OWASP Top 10)
*   **Attack:** SQL Injection (SQLi) payload delivery.
    `curl "http://192.168.1.X/?id=1'+UNION+SELECT+username,password+FROM+users--"`
*   **🛡️ Response:** ModSecurity (WAF) identifies the anomaly (Score 23+). n8n triggers the **Web Defense Playbook** to block the attacker IP.

### 3. File Integrity & Malware Defense (MITRE T1565)
*   **Attack:** Remote Payload Push via SSH.
    `echo 'EICAR-ANTIVIRUS-TEST-STRING' | ssh 192.168.1.X "cat > /tmp/eicar.com"`
*   **🛡️ Response:** Wazuh `syscheck` detects the file modification. n8n performs a VirusTotal hash lookup. EICAR strings return a high threat score, triggering a high-priority incident in TheHive.

---

## 🚀 How to Explore this Project
The infrastructure is organized into modular deployment directories:

*   **/docker:** 
    *   `/core-stack`: Contains the `docker-compose.yml` for **Wazuh** and **n8n**.
    *   `/case-management`: Contains the standalone `docker-compose.yml` for **TheHive 5** and its dependencies (Cassandra/Elasticsearch).
*   **/n8n:** Exported JSON workflow files for the Master Router and specialized playbooks.
*   **/scripts:** Custom Python Active Response logic (`web-blocker.py`, `custom_block.py`).
*   **/wazuh:** Custom XML detection rules and agent configuration snippets.

> **Note:** All API keys and public-facing IPs have been replaced with `{{PLACEHOLDERS}}`.

---

### 🤝 Connect with me
*   **LinkedIn:** [Your LinkedIn Profile Link]
*   **GitHub:** [Your GitHub Profile Link]
