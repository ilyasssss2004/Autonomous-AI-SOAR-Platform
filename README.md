# 🛡️ Autonomous-AI-SOAR-Platform

### *End-to-End Threat Detection, AI-Contextualization, and Active Response*

![Project Architecture](docs/architecture-diagram.png)

## 📌 Project Overview
This repository hosts a fully containerized, autonomous Security Operations Center (SOC) pipeline. It bridges the gap between raw telemetry and intelligent response by integrating **Wazuh (SIEM)**, **n8n (SOAR)**, and **Google Gemini (LLM)**.

The platform doesn't just detect threats; it triages them using real-time threat intelligence (**VirusTotal/AbuseIPDB**), generates human-readable executive and tactical reports via AI, and executes **Active Response** Python scripts to neutralize attackers at the edge.

---

## 🏗️ Technical Architecture
The entire core stack is deployed via **Docker**, ensuring high availability and modularity.

*   **SIEM:** Wazuh (Manager & Indexer)
*   **SOAR Orchestrator:** n8n (Self-hosted)
*   **Case Management:** TheHive 5
*   **Target Environment:** Ubuntu 24.04 (Hardened with `auditd` and `UFW`)
*   **Attack Vector:** Kali Linux (Attack Emulation)

---

## 🧠 The SOAR Logic (Hub & Spoke Model)
The automation engine is built on a **1+3 Modular Workflow** design in n8n, optimized for scalability and "Alert Fatigue" reduction.

### 1. Master Alert Dispatcher
Acts as the central router. It ingests Wazuh JSON webhooks, triages the alert based on the `rule.id` or `group`, and dispatches the payload to the correct specialized Playbook.
<img width="1847" height="656" alt="image" src="https://github.com/user-attachments/assets/77fa80c1-a8f1-471c-8abd-351a575c1869" />

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
*   **Mechanism:** Performs a "Secret Handshake" with Wazuh 4.x and executes `UFW` commands to insert deny rules.

### 2. `custom_block.py` (The Terminator)
*   **Logic:** Designed for high-confidence SSH brute-force attacks.
*   **Behavior:** Instantly triggers a `UFW` block upon a specific alert ID and logs actions to `/var/log/custom_terminator.log`.

---

## 🤖 AI Contextualization: Google Gemini
This platform solves the "Context Gap" by using two distinct LLM prompts to translate technical data for different stakeholders:

*   **Tactical Alert (Slack):** Provides the SOC analyst with the exact MITRE ATT&CK technique, enriched IoC data, and recommended next steps.
*   **Executive Brief (Email):** Automatically translates technical telemetry into a high-level business impact summary for management.

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
