# Autonomous AI-SOAR Platform

### End-to-End Threat Detection, AI-Contextualization, and Active Response

<img width="1130" height="639" alt="soc-automation-architecture" src="https://github.com/user-attachments/assets/02bd3cb4-6f63-4a2e-a8a1-b83ae6f4b404" />

---

## Project Overview

This repository hosts a fully containerized, autonomous Security Operations Center (SOC) pipeline that bridges the gap between raw telemetry and intelligent response. The platform integrates **Wazuh (SIEM)**, **n8n (SOAR)**, and **Google Gemini (LLM)** into a cohesive, production-grade defense architecture.

The platform does not simply detect threats — it triages them using real-time threat intelligence from **VirusTotal** and **AbuseIPDB**, generates human-readable executive and tactical reports via AI, and executes **Active Response** Python scripts to neutralize attackers at the network edge autonomously.

---

## Technical Architecture

The platform is distributed across three primary logical nodes, simulating a real-world enterprise environment.

**1. Defensive Core (Ubuntu Server)**
- **SIEM:** Wazuh (Manager & Indexer) — Centralized log analysis, security monitoring, and endpoint telemetry.
- **SOAR Orchestrator:** n8n (Self-hosted) — The automation brain; a modular workflow engine for incident response.
- **Case Management:** TheHive 5 — Centralized dashboard for incident tracking, forensic analysis, and audit compliance.

**2. Target Node (Ubuntu 24.04 Victim)**
- **Web Stack:** Apache2 HTTP Server protected by **ModSecurity 3.0**.
- **WAF Integration:** Configured with the **OWASP Core Rule Set (CRS)** to detect and block SQL Injection (SQLi) and other OWASP Top 10 threats in real-time.
- **Telemetry:** Hardened with `auditd` and the **Wazuh Agent** for File Integrity Monitoring (FIM) and log shipping.

**3. Attack Node (Kali Linux)**
- Dedicated environment for generating adversarial telemetry and validating playbook triggers.

---

### Service Access

| Service | URL | Port |
| :--- | :--- | :--- |
| Wazuh Dashboard | `https://localhost:443` | 443 |
| n8n Automation | `http://localhost:5678` | 5678 |
| TheHive | `http://localhost:9000` | 9000 |

---

## Endpoint Visibility & SIEM (Wazuh)

Before automation can occur, high-fidelity telemetry is required. The Wazuh Manager acts as the central ingestion point, providing real-time visibility into the target environment.

<img width="1853" height="804" alt="image" src="https://github.com/user-attachments/assets/fa17add6-1658-44b8-95ca-9f0a720b579a" />

**Key Telemetry Capabilities:**
- **MITRE ATT&CK Mapping:** Automatically maps system events to adversarial tactics and techniques.
- **Vulnerability Detection:** Continuous scanning of installed packages against global CVE databases.
- **Security Configuration Assessment (SCA):** Audits the target node against CIS benchmarks to ensure baseline hardening.

---

## SOAR Logic — Hub & Spoke Model

The automation engine is built on a **1+3 Modular Workflow** design in n8n, optimized for scalability and alert fatigue reduction.

### Master Alert Dispatcher

Acts as the central router. It ingests Wazuh JSON webhooks, triages each alert based on `rule.id` or `group`, and dispatches the payload to the correct specialized playbook.

<img width="1850" height="766" alt="Master Alert Router Logic" src="https://github.com/user-attachments/assets/9b416242-72c7-4622-ae7b-4597376caaed" />

---

### Specialized Playbooks

**Auth Defense & Credential Access**

Handles SSH Brute Force (T1110), enriches IP reputation via AbuseIPDB, utilizes Google Gemini to draft context-rich Slack and Email alerts, and auto-provisions a tracking case in TheHive.

**Engineering Note — Alert Fatigue Reduction:** To prevent notification spam and API rate-limiting during high-volume attacks, a custom JavaScript node was engineered to track offending IPs in n8n's static workflow memory, enforcing a strict 2-minute cooldown window before allowing a duplicate alert to proceed to the AI engine and SOC dashboards.

<details>
<summary><b>Click to view the Custom JS Rate-Limiting Logic</b></summary>
```javascript
const staticData = $getWorkflowStaticData('global');
const items = $input.all();
const validItems = [];

const now = Date.now();
const cooldown = 120000; // 120 seconds (2 minutes)

for (const item of items) {
    // Extract the attacker IP from Wazuh's JSON payload
    const ip = item.json.body?.data?.srcip || "unknown_ip";
    const lastSeen = staticData[ip] || 0;

    // If the cooldown has passed, allow the alert and reset the timer
    if (now - lastSeen >= cooldown) {
        staticData[ip] = now;
        validItems.push(item);
    }
}

// Return only net-new alerts, dropping the spam
return validItems;```

</details>

<img width="1847" height="793" alt="Auth Defense Workflow" src="https://github.com/user-attachments/assets/5d06e34f-8a8c-4316-ab34-809525f1c54a" />

---

**File Integrity & Malware Defense**

Real-time FIM across critical system paths (`/var/www/html`, `/etc/apache2`, `/etc/modsecurity`, `/tmp`).

**Engineering Note — Automated Malware Triage:** To eliminate manual hash lookups, this playbook extracts SHA256 file hashes directly from Wazuh `syscheck` payload alerts and queries the VirusTotal API. A dynamic logic gate based on the `$ThreatScore` then routes the alert: benign modifications (Score = 0) are silently logged as audit cases in TheHive, while confirmed malicious files (Score > 0) are immediately passed to the AI engine to generate actionable threat reports — broadcast to analysts via Slack and to management via Email — and trigger a High-Severity incident in TheHive with the hash attached as an IoC observable.

<img width="1852" height="800" alt="Malware Defense Workflow" src="https://github.com/user-attachments/assets/2c9b6224-b6c3-4b01-96cd-db18b904d129" />

---

**Web Application Defense**

Triages Apache/ModSecurity WAF logs to identify and mitigate OWASP Top 10 attacks including SQL Injection and Directory Traversal.

**Engineering Note — Dual-Stream AI Contextualization:** WAF logs are notoriously dense and prone to alert fatigue. This playbook solves the readability problem by enriching the attacker's IP via AbuseIPDB, then routing the payload through two parallel AI nodes simultaneously — translating the raw HTTP attack vector into a technical Slack alert for SOC analysts and a business-risk Email for executives. A centralized case is automatically created in TheHive with the enriched IP attached as a forensic observable.

<img width="1850" height="799" alt="Web Defense Workflow" src="https://github.com/user-attachments/assets/5ff80443-1fdf-4302-82ae-92e640ae8fdc" />

---

## Custom Active Response (Python)

Specialized Python scripts move the platform from passive monitoring to active defense. These scripts reside on the Ubuntu victim agent and are triggered remotely by the Wazuh Manager.

### `web-blocker.py` — Progressive Defense
- **Logic:** Maintains a local JSON state file (`web_offenders.json`) to track strikes per offending IP.
- **Behavior:** Strike 1 → 60s block. Strike 2 → 300s block. Strike 3 → Permanent block (1 hour).
- **Mechanism:** Performs the Wazuh 4.x active response handshake and executes `UFW` commands to insert deny rules at the firewall level.

### `custom_block.py` — Immediate Termination
- **Logic:** Designed for high-confidence SSH brute-force detections.
- **Behavior:** Instantly triggers a `UFW` block upon a specific Wazuh alert ID and logs all actions to `/var/log/custom_terminator.log`.

---

## AI-Powered Contextualization & Alerting

This platform solves the "Context Gap" by using **Google Gemini** to translate raw JSON telemetry into actionable intelligence. A dual-prompting strategy runs two parallel LLM instances per playbook, each tailored for a different audience.

### Tactical Alert (Slack)

**Audience:** SOC Analysts and Incident Responders
**Content:** MITRE ATT&CK mapping, enriched IoCs from VirusTotal/AbuseIPDB, and threat intent summary.

**Implementation Details:**
- **Targeted Channel Routing:** Alerts are routed dynamically to specialized operational channels (`#soc-auth-alerts`, `#soc-malware-alerts`, `#soc-web-alerts`) using a custom Wazuh Bot webhook integration — not dumped into a single noisy channel.
- **Resilient API Delivery:** Routing is hardcoded via Channel IDs (e.g., `C0AL634F4HX`) rather than display names, ensuring the automation does not break if a channel is renamed.
- **UX-Optimized Prompting:** The Gemini prompt is strictly instructed to output structured Markdown with bulleted lists, creating highly scannable alerts that reduce cognitive load during high-stress triage.

<img width="1919" height="859" alt="Slack Tactical Alert" src="https://github.com/user-attachments/assets/2097079a-d0a6-429e-a49b-4eb3e1511ae7" />

---

### Executive Brief (Email)

**Audience:** CISOs and Management
**Content:** Risk-based business impact summary, plain-English incident description, and automated resolution status.

**Implementation Details:**
- **Audience-Specific Prompting:** The LLM prompt for the email node strips all raw JSON, CLI commands, and technical jargon — focusing exclusively on business risk and mitigation confirmation.
- **Native SMTP Integration:** Dispatched directly to management inboxes via n8n's native SMTP node.
- **Dynamic HTML Injection:** The n8n node parses Gemini's output and injects it as formatted HTML (`{{ $json.output }}`), ensuring the email arrives with clean formatting and structure rather than a raw wall of text.

<img width="1919" height="891" alt="Executive Email Report" src="https://github.com/user-attachments/assets/a7cbd280-1947-4734-961e-fc2630427280" />

---

## Incident Case Management — TheHive 5

Every triaged alert is automatically logged into TheHive, serving as the deterministic single pane of glass for incident responders and ensuring full auditability and compliance.

<img width="1854" height="803" alt="TheHive Case Management Dashboard" src="https://github.com/user-attachments/assets/d9d7125a-e74c-4d1c-8d78-d710cf8e90c2" />

**Key Case Management Features:**

- **Deterministic Case Formatting (No AI Hallucinations):** To preserve strict forensic integrity, the core case description explicitly bypasses the LLM. The pipeline uses n8n's expression engine to directly map raw JSON telemetry from Wazuh and threat intel APIs into a structured, heavily formatted template — ensuring analysts see 100% accurate source data at all times.

- **Dynamic IoC Extraction (Observables):** Critical indicators are extracted and attached as structured Observables rather than plain text:
  - *Web & Auth Defense:* Automatically parses and attaches the attacker's IP address enriched with its AbuseIPDB confidence score.
  - *Malware Defense:* Extracts the SHA256 hash from the `syscheck` payload and attaches it alongside its VirusTotal threat score.

- **Automated Threat Correlation:** By injecting standardized Observables, TheHive's graph engine automatically surfaces related cases. If an IP that triggered a web attack yesterday attempts an SSH brute force today, TheHive correlates the Observables automatically — allowing analysts to instantly pivot from isolated alerts to hunting persistent attack campaigns.

- **Intelligent Triage Logic (Malware Playbook):** A conditional logic gate based on the VirusTotal `$ThreatScore` drives two distinct response paths:
  - **SOC Incident (Score > 0):** High/Medium severity case. Flagged for immediate human response with full AI-generated context.
  - **SOC Audit (Score = 0):** Silent audit case. Benign system modifications are logged for forensic record-keeping but bypass all AI-alerting channels to keep analyst queues clean.

<img width="1850" height="797" alt="Malware Incident Flow" src="https://github.com/user-attachments/assets/a51ea94a-383c-4345-a834-729cd8ab02a4" />
<img width="1848" height="793" alt="Malware Analysis View" src="https://github.com/user-attachments/assets/cf85a2b7-e1ff-4382-9847-f004b967206d" />

---

## Attack Emulation & Playbook Validation

Each playbook was validated using real-world adversarial techniques executed from an external Kali Linux node.

### 1. Auth Defense (MITRE T1110)
*   **Attack:** SSH Brute Force using Hydra.
```bash
hydra -l victim_user -P /path/to/wordlist.txt ssh://192.168.1.X
```

*   **Response:** Wazuh detects 4+ failures. n8n triggers the **Auth Defense Playbook**, executing a UFW block via `custom_block.py`.

---

### 2. Web Application Defense (OWASP Top 10)
*   **Attack:** SQL Injection (SQLi) payload delivery.
```bash
curl "http://192.168.1.X/?id=1'+UNION+SELECT+username,password+FROM+users--"
```

*   **Response:** ModSecurity (WAF) identifies the anomaly (Score 23+). n8n triggers the **Web Defense Playbook** to block the attacker IP.

---

### 3. File Integrity & Malware Defense (MITRE T1565)
*   **Attack:** Remote Payload Push via SSH.
```bash
echo 'EICAR-ANTIVIRUS-TEST-STRING' | ssh 192.168.1.X "cat > /tmp/eicar.com"
```

*   **Response:** Wazuh `syscheck` detects the file modification. n8n performs a VirusTotal hash lookup. EICAR strings return a high threat score, triggering a high-priority incident in TheHive.

---

### 4. Threat Intelligence & Triage Defense (MITRE T1105)
*   **Attack:** Simulated file drop on the compromised Ubuntu victim — one known malicious sample and one benign file — to validate the full VirusTotal triage and SOAR routing logic.

**Malicious sample — EICAR test file:**
```bash
cd /tmp && wget -O eicar_test_sample.com https://secure.eicar.org/eicar.com.txt
```

**Benign sample — normal file:**
```bash
echo "This is a normal configuration file for my website." > /tmp/normal_file.txt
```

*   **Response:** Wazuh `syscheck` detects both file creation events and extracts their hashes. n8n submits each hash to VirusTotal:
    *   **`eicar_test_sample.com` (VT Score > 0 / known malicious):** Triggers an immediate high-priority alert routed to both Slack and Email, and an incident is automatically created in TheHive.
    *   **`normal_file.txt` (VT Score = 0 / unique or unknown hash):** Flagged as an audit case in TheHive for analyst review, ensuring unknown files are never silently dropped.

---

> **Note:** All API keys and public-facing IPs have been replaced with `{{PLACEHOLDERS}}`.

---

### Connect

- **LinkedIn:** https://www.linkedin.com/in/ilyas-wadgattait-96551624b
