# NetSage AI — Applied AI + Network Troubleshooting Helper

**NetSage AI** is an AI-assisted network troubleshooting assistant designed specifically for Cisco Packet Tracer and lab networking problems. It bridges deterministic rule-based checks with Google Gemini AI diagnostics under a mandatory **Human-in-the-Loop (HITL)** review workflow.

---

## 1. Problem Statement

Troubleshooting network issues in lab environments (such as Cisco Packet Tracer) can be challenging for networking students and junior engineers. Common configuration mistakes—such as mismatched VLAN access ports, omitted DHCP default routers, inverted NAT interfaces, or subtle subnet mask typos—often result in broad, non-specific symptoms (e.g., "ping timeout" or "unreachable host"). 

While Generative AI models can assist with troubleshooting, relying purely on raw LLMs introduces significant risks:
- **Hallucinations**: Models may misinterpret locally significant parameters (such as OSPF process IDs) as protocol errors.
- **Dangerous Recommendations**: Models might suggest destructive commands (e.g., wiping running configurations or removing entire firewalls) rather than surgical fixes.
- **Lack of Accountability**: Unchecked AI diagnoses lack human engineering oversight.

---

## 2. Project Objective

NetSage AI addresses these challenges by creating a safe, accountable, and explainable AI troubleshooting helper that:
1. Accepts user symptoms, topology notes, and raw Cisco show-command evidence.
2. Runs **deterministic rule checks** to detect definite configuration flaws before invoking AI.
3. Uses **Google Gemini** (or a built-in **Offline Mock Engine**) to return a strictly structured, evidence-grounded diagnosis.
4. Enforces **Human-in-the-Loop (HITL)** review where a human engineer must inspect, accept, edit, or reject the diagnosis.
5. Maintains a **Responsible AI Audit Log** documenting AI failure modes and lessons learned.
6. Provides an interactive **Analytics Dashboard** tracking issue distributions, severity, and human-AI agreement rates.

---

## 3. Key Features

- **32 Pre-Seeded Cisco Lab Scenarios**: Exactly 4 realistic lab cases across 8 core networking domains (VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, Wireless).
- **6 Deterministic Rule Checking Modules**: Fast regex-based analysis of Cisco CLI outputs to ground the AI and eliminate hallucinations.
- **Strict Pydantic JSON Schema**: Enforces structured diagnosis output containing Root Cause, Confidence Score, Evidence Citations, OSI Layer, Next Command, Fix Steps, Explanation, and Risk Assessment.
- **Dual AI Engine Modes**:
  - `GEMINI_LIVE`: Connects to Google Gemini using the modern `google-genai` SDK.
  - `OFFLINE_MOCK`: 100% functional offline mock engine requiring zero internet or API keys.
- **Mandatory Human-in-the-Loop Review**: Allows reviewers to **Accept**, **Edit** (modify root cause or fix steps), or **Reject** diagnoses with reviewer audit logging.
- **Responsible AI Calibration Log**: 5 curated demonstration case studies illustrating canonical LLM failure modes.
- **Real-Time Analytics Dashboard**: Real-time KPI cards and Altair charts driven directly by SQLite persistence.
- **Interactive Verification Simulator**: Simulated Packet Tracer verification test confirming connectivity resolution without executing commands on the host.

---

## 4. System Architecture

```
+-----------------------------------------------------------------------------------+
|                               Streamlit UI (Frontend)                             |
|  [Live Troubleshooter]  [Case Catalog (32)]  [HITL Review]  [Responsible AI Log]  |
|                             [Analytics Dashboard]                                 |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                Application Layer                                  |
|                                                                                   |
|   +--------------------------+               +--------------------------------+   |
|   | Deterministic Rule Engine|               |       Gemini AI Service        |   |
|   |  - 6 Domain Rule Modules | ------------> |  - google-genai SDK            |   |
|   |  - Regex CLI Text Parser | (Rule Facts)  |  - Pydantic Schema Enforcement |   |
|   |  - Severity Sorter       |               |  - Smart Offline Mock Engine   |   |
|   +--------------------------+               +--------------------------------+   |
|                 \                                    /                            |
|                  \                                  /                             |
|                   v                                v                              |
|   +---------------------------------------------------------------------------+   |
|   |                        Human-in-the-Loop (HITL) Workflow                  |   |
|   |                   [ Accept ]  [ Edit / Correct ]  [ Reject ]              |   |
|   +---------------------------------------------------------------------------+   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           Persistence Layer (SQLite)                              |
|   - cases (32 lab cases)         - diagnoses (AI diagnostic runs)                 |
|   - reviews (Human decisions)    - responsible_ai_logs (5+ calibration logs)      |
+-----------------------------------------------------------------------------------+
```

---

## 5. Technology Stack

- **Core Language**: Python 3.10+ (Tested on Python 3.13)
- **Frontend & Dashboard**: Streamlit (Native Multipage Architecture)
- **AI SDK**: Google GenAI Python SDK (`google-genai`)
- **Data Validation**: Pydantic v2
- **Persistence**: SQLite3 (Embedded, zero-configuration)
- **Data Visualization**: pandas, Altair
- **Automated Testing**: pytest

---

## 6. Folder & File Structure

```text
netsage-ai/
├── .env.example                  # Safe template for environment configuration
├── .gitignore                    # Git ignore file (.env, *.db, .venv, etc.)
├── README.md                     # Comprehensive documentation & evaluation guide
├── requirements.txt              # Project dependencies
├── pytest.ini                    # Pytest path and runner configuration
│
├── app.py                        # Main Streamlit landing page & lifecycle overview
│
├── data/                         # SQLite database & JSON seed datasets
│   ├── netsage.db                # SQLite database (auto-created on startup)
│   ├── seed_cases.json           # 32 Cisco lab scenarios
│   └── seed_responsible_ai.json  # 5 Curated Responsible AI calibration records
│
├── src/
│   ├── __init__.py
│   ├── config.py                 # Configuration constants, paths, and API helpers
│   ├── db.py                     # SQLite initialization, migrations, and CRUD operations
│   ├── models.py                 # Pydantic schemas (Diagnosis, Case, Review, RuleFinding)
│   │
│   ├── rules/                    # 6 Deterministic rule checking modules
│   │   ├── __init__.py
│   │   ├── engine.py             # Master dispatcher, deduplicator, and prompt formatter
│   │   ├── vlan_rules.py         # VLAN access, trunking, and layer 2 checks
│   │   ├── gateway_rules.py      # Default gateway, subnet mask, and HSRP checks
│   │   ├── dhcp_dns_rules.py     # DHCP pool, relay helper, and DNS checks
│   │   ├── routing_rules.py      # Static route, default route, and OSPF checks
│   │   ├── acl_rules.py          # ACL filter, implicit deny, and direction checks
│   │   └── nat_wireless_rules.py # NAT overload, inside/outside roles, and WLAN checks
│   │
│   ├── ai/                       # AI integration & prompts
│   │   ├── __init__.py
│   │   ├── gemini_client.py      # Gemini API integration via google-genai SDK
│   │   ├── prompts.py            # System prompts, few-shot examples, and prompt builder
│   │   └── mock_ai.py            # Smart Offline Mock diagnostic engine
│   │
│   └── utils/
│       ├── __init__.py
│       └── cisco_parser.py       # Regex parser for standard Cisco show commands
│
├── pages/                        # Streamlit Multipage User Interface
│   ├── 1_🔍_Live_Troubleshooter.py # 5-step interactive troubleshooting lab & HITL review
│   ├── 2_📚_Case_Repository.py     # 32-scenario filterable catalog with 1-click loader
│   ├── 3_⚖️_Responsible_AI_Log.py  # Calibration records, failure taxonomy, and live review audit
│   ├── 4_📊_Analytics_Dashboard.py # Real-time SQLite KPIs and Altair distribution charts
│   └── 5_⚙️_Settings.py            # AI mode switcher, API tester, and DB reseed tool
│
└── tests/                        # Comprehensive Automated Test Suite (61 tests)
    ├── __init__.py
    ├── test_phase1.py            # Foundation, config, and schema tests
    ├── test_db.py                # SQLite schema, CRUD, seed loading, and idempotency tests
    ├── test_cisco_parser.py      # Regex CLI text parsing tests
    ├── test_rules.py             # 6 deterministic rule engine tests
    ├── test_ai_integration.py    # AI prompts, mock engine, and Gemini mocking tests
    ├── test_ui_workflow.py       # Streamlit AppTest page rendering tests
    └── test_e2e_workflow.py      # Full lifecycle tests across all 8 networking domains
```

---

## 7. Installation & Setup

### Step 1: Clone Repository
```bash
git clone <repository_url>
cd netsage-ai
```

### Step 2: Create & Activate Virtual Environment
```bash
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 8. How to Run Locally

Start the Streamlit application:
```bash
streamlit run app.py
```
Open your browser and navigate to: **`http://localhost:8501`**

---

## 9. Configuring Google Gemini API (Optional)

1. Obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and set your key:
   ```ini
   GEMINI_API_KEY=AIzaSyYourActualApiKeyHere
   NETSAGE_MODE=GEMINI_LIVE
   ```
4. Alternatively, you can enter your API key directly in the **Settings** page (`pages/5_⚙️_Settings.py`) during a live demo session. The key is stored in volatile session memory only.

---

## 10. How Offline Mock Mode Works

If you do not have an API key or an active internet connection (e.g. during a college viva presentation), NetSage AI operates completely seamlessly in **Offline Mock Mode**:
- Set `NETSAGE_MODE=OFFLINE_MOCK` in `.env` (the default) or toggle to `OFFLINE_MOCK` in the Settings page.
- The smart mock engine uses deterministic heuristic pattern matching across the 8 domains to return complete, typed `DiagnosisResponse` objects.
- All UI workflows, rule checks, human reviews, and database analytics function identically.

---

## 11. How to Use the Application (Step-by-Step)

1. **Explore the Scenarios**: Navigate to **`2 📚 Case Repository`**, search for a topic (e.g. `VLAN` or `NAT`), and click **`Load into Troubleshooter ➡️`**.
2. **Run Deterministic Checks**: On **`1 🔍 Live Troubleshooter`**, click **`1. Run Deterministic Rule Checks`** to see instant color-coded pre-check findings.
3. **Generate AI Diagnosis**: Click **`2. Run AI Diagnosis`** to view the structured root cause analysis, evidence citations, OSI layer, and fix commands.
4. **Perform Human Review**:
   - Click **`Accept Diagnosis`** if the diagnosis is accurate.
   - Click **`Edit & Correct`** to adjust root cause or fix commands.
   - Click **`Reject Diagnosis`** to log an AI failure with reviewer notes into the Responsible AI audit table.
5. **Simulated Verification**: Click **`Simulate Packet Tracer Verification Test`** to view the simulated terminal ping test confirming resolution.
6. **Inspect Analytics**: Navigate to **`4 📊 Analytics Dashboard`** to see real-time agreement metrics and category charts update automatically.

---

## 12. Deterministic Rule Engine Overview

The deterministic rule engine executes **6 domain modules** before calling the AI:
1. [`src/rules/vlan_rules.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/rules/vlan_rules.py): Access port VLAN mismatches, trunk allowed list omissions, native VLAN mismatches, inactive VLAN database omissions, shutdown interfaces.
2. [`src/rules/gateway_rules.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/rules/gateway_rules.py): Subnet mask mismatches (/25 vs /24), missing switch management `ip default-gateway`, host static gateway typos, HSRP VIP mismatches.
3. [`src/rules/dhcp_dns_rules.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/rules/dhcp_dns_rules.py): APIPA missing pools, missing excluded address IP conflicts, missing `ip helper-address` relays, DHCP default-router typos, unreachable DNS servers, disabled domain lookup.
4. [`src/rules/routing_rules.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/rules/routing_rules.py): Missing default static route (`0.0.0.0/0`), static route unresolvable next-hop IPs, OSPF Hello/Dead timer mismatches, OSPF `passive-interface` on transit links.
5. [`src/rules/acl_rules.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/rules/acl_rules.py): Standard ACL destination filtering misuse, implicit deny-all drops, inverted direction (`in` vs `out`), wrong interface bindings.
6. [`src/rules/nat_wireless_rules.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/rules/nat_wireless_rules.py): Missing dynamic PAT `overload` keyword, inverted inside/outside roles, NAT ACL subnet exclusions, static NAT typos, SSID case mismatches, WPA2-PSK key errors, AP on wrong VLAN.

---

## 13. Human-in-the-Loop (HITL) Workflow

AI models should never be given autonomous write access to production or lab network configurations. NetSage AI enforces a strict 3-way human review gate:
- **Accept**: Validates the diagnosis as accurate and logs an agreement score of 1.
- **Edit**: Allows human engineers to adjust the root cause or surgical fix steps, logging the human modification with an agreement score of 0.
- **Reject**: Captures reviewer reasoning, logs an agreement score of 0, and automatically files an entry into the Responsible AI audit table.

---

## 14. Responsible AI & Calibration Dataset

NetSage AI includes **5 curated demonstration case studies** (`RAI-01` to `RAI-05`) representing real-world failure categories:
1. **RAI-01 (Routing — Hallucination)**: AI claimed OSPF Process IDs must match; corrected to Hello/Dead timer mismatch.
2. **RAI-02 (VLAN — Dangerous Fix Command)**: AI proposed destructive full-router reconfiguration; corrected to 1-line sub-interface encapsulation command.
3. **RAI-03 (DHCP — Incomplete Evidence)**: AI assumed DHCP server was down; corrected to missing `ip helper-address` across routed boundary.
4. **RAI-04 (NAT — Wrong OSI Layer)**: AI misdiagnosed NAT table exhaustion as Layer 7 DNS failure; corrected to missing `overload` keyword.
5. **RAI-05 (ACL — Security Violation)**: AI suggested removing the firewall completely (`no ip access-group`); corrected to inserting a targeted permit ACE.

---

## 15. Testing Instructions

NetSage AI includes a comprehensive test suite of **61 automated tests** covering database schemas, CRUD operations, Cisco CLI parsing, 6 rule modules, AI prompt generation, mock engine across 8 domains, AppTest UI rendering, and end-to-end domain pipelines.

Run the test suite:
```bash
pytest -v
```

Expected output:
```text
============================= test session starts =============================
collected 61 items
============================= 61 passed in 5.07s ==============================
```

---

## 16. Project Requirements Coverage (Traceability Matrix)

| Requirement | Specification | Implementation Location |
|---|---|---|
| **1. Ingest Symptom** | Accept user-reported symptom text | [`pages/1_🔍_Live_Troubleshooter.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/pages/1_%F0%9F%94%8D_Live_Troubleshooter.py#L86-L95) |
| **2. Ingest Topology** | Accept topology notes & IP scheme | [`pages/1_🔍_Live_Troubleshooter.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/pages/1_%F0%9F%94%8D_Live_Troubleshooter.py#L97-L105) |
| **3. Ingest Show Output** | Accept raw Cisco CLI show commands | [`pages/1_🔍_Live_Troubleshooter.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/pages/1_%F0%9F%94%8D_Live_Troubleshooter.py#L107-L113), [`src/utils/cisco_parser.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/utils/cisco_parser.py) |
| **4. Deterministic Checks** | Deterministic Python checks for config faults | [`src/rules/`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/rules/) (6 modules), [`src/rules/engine.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/rules/engine.py) |
| **5. Send to AI Model** | Gemini API integration via `google-genai` | [`src/ai/gemini_client.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/ai/gemini_client.py), [`src/ai/prompts.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/ai/prompts.py) |
| **6. Structured Diagnosis** | Root cause, confidence, evidence, OSI layer, next cmd, fix | [`src/models.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/models.py#L21-L50) (`DiagnosisResponse`) |
| **7. Mandatory Review** | Require human review before acceptance | [`pages/1_🔍_Live_Troubleshooter.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/pages/1_%F0%9F%94%8D_Live_Troubleshooter.py#L260-L345) |
| **8. Review Actions** | Allow reviewer to Accept, Edit, or Reject | [`pages/1_🔍_Live_Troubleshooter.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/pages/1_%F0%9F%94%8D_Live_Troubleshooter.py#L273-L345), [`src/db.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/db.py#L354-L390) |
| **9. Persist Decisions** | Store diagnosis and human decisions in SQLite | [`src/db.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/db.py#L271-L390) (`diagnoses` & `reviews` tables) |
| **10. Responsible AI Log** | Maintain audit log with 5+ correction cases | [`data/seed_responsible_ai.json`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/data/seed_responsible_ai.json), [`pages/3_⚖️_Responsible_AI_Log.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/pages/3_%E2%9A%96%EF%B8%8F_Responsible_AI_Log.py) |
| **11. 30+ Lab Cases** | 32 cases across 8 required networking categories | [`data/seed_cases.json`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/data/seed_cases.json), [`pages/2_📚_Case_Repository.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/pages/2_%F0%9F%93%9A_Case_Repository.py) |
| **12. Analytics Dashboard** | Issue types, severity, counts, agreement, decisions | [`pages/4_📊_Analytics_Dashboard.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/pages/4_%F0%9F%93%8A_Analytics_Dashboard.py), [`src/db.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/src/db.py#L484-L545) |
| **13. Demo Workflow** | Case → Evidence → Rules → AI → Review → Fix → Test | [`pages/1_🔍_Live_Troubleshooter.py`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/pages/1_%F0%9F%94%8D_Live_Troubleshooter.py) (5-step workflow) |

---

## 17. Canonical Demo Walkthrough for Viva / Evaluation

Use **`CASE-VLAN-01`** for the canonical college demonstration:
1. **Navigate**: Go to **`2 📚 Case Repository`**, locate `[CASE-VLAN-01] Host Assigned to Default VLAN Instead of Department VLAN`, and click **`Load into Troubleshooter ➡️`**.
2. **Review Evidence**: Observe the symptom (*PC-1 cannot ping Finance gateway 192.168.10.1*) and the raw show-command output showing port `Fa0/1` in Default VLAN 1.
3. **Step 1 (Deterministic Check)**: Click **`1. Run Deterministic Rule Checks`**. Observe the `[High] VLAN_ACCESS_MISMATCH` finding immediately flagged with matched evidence.
4. **Step 2 (AI Diagnosis)**: Click **`2. Run AI Diagnosis`**. Observe the structured response card:
   - *Root Cause*: Switchport Fa0/1 is assigned to Default VLAN 1 instead of VLAN 10 (Finance).
   - *Confidence*: `96.0%`
   - *OSI Layer*: `Layer 2 - Data Link`
   - *Remediation Commands*: `interface FastEthernet0/1` -> `switchport mode access` -> `switchport access vlan 10`
   - *Next Command*: `show vlan brief`
5. **Step 3 (Human Review)**: Enter reviewer name `Aditya` and click **`Confirm & Accept Diagnosis`**. Observe the confirmation stored in SQLite.
6. **Step 4 (Verification)**: Click **`Simulate Packet Tracer Verification Test`** to view the simulated terminal ping output verifying connectivity.
7. **Step 5 (Dashboard)**: Navigate to **`4 📊 Analytics Dashboard`** to show the live agreement rate and case metrics updated in real-time.

---

## 18. Security & Safety Audit Notes

- **Zero Command Execution on Host**: Cisco CLI text is strictly parsed as data. No commands (`ping`, `ssh`, or shell commands) are ever executed on the host operating system.
- **No Hardcoded Secrets**: Zero API keys are hardcoded in source code or committed to Git.
- **Volatile Session Keys**: Custom API keys entered in the UI are held strictly in memory and are never written to disk, git, or SQLite.
- **Safe Evaluation**: Pure Python regex parsing without dangerous `eval()` or `exec()` statements.
- **Git Tracking Safeguards**: `.env`, `.venv`, and `*.db` are explicitly excluded in [`.gitignore`](file:///c:/Users/adity/OneDrive/Documents/netsage-ai/.gitignore).

---

## 19. Limitations & Future Improvements

- **Instructional Simulation**: Verification tests in the UI are simulated demonstrations. In real lab sessions, students must manually paste configuration commands into Cisco Packet Tracer.
- **CLI Syntax Scope**: The regex parser is tailored for Cisco IOS show commands relevant to CCNA lab topologies; expanding to Juniper JunOS or Arista EOS would require additional parser grammar modules.
- **Future Enhancements**: Direct integration with Cisco Packet Tracer IPC/PT-API or GNS3/EVE-NG REST APIs for automated lab state extraction.
