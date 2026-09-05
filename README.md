# Merchant Intelligence OS

### AI-Powered Financial Operating System for Digital Merchants

> **Razorpay AI Buildathon 2026 — Open Track**

**One AI system. Four financial specialists. One governed decision layer.**

Merchant Intelligence OS is an AI-powered financial operating system designed to help digital merchants understand what is happening across their business, identify revenue leakage and financial risk, and take governed actions through a single intelligent workflow.

Instead of building four disconnected AI agents, Merchant Intelligence OS uses a **Supervisor Orchestrator** that dynamically determines which specialists are required, coordinates their work, synthesizes their findings, applies deterministic financial policies, and controls execution.

---

## 🚀 Why Merchant Intelligence OS?

Modern merchants do not experience financial problems in isolated categories.

A revenue problem may simultaneously involve:

* failed payments
* settlement discrepancies
* fraud or chargeback risk
* declining product conversion
* recoverable payment attempts
* cash-flow issues

Traditional dashboards show these signals separately.

Merchant Intelligence OS connects them.

A merchant can ask:

> **"Why is my revenue changing, what is causing the problem, and what can I safely do about it?"**

The system dynamically decomposes the question and coordinates the required financial specialists.

---

# 🎯 Problem Statement

Merchant financial operations are fragmented across payment data, settlements, failed transactions, risk signals, customer behavior and recovery workflows.

A merchant may know that revenue is changing, but identifying **why**, determining **which signals actually matter**, and deciding **what action is safe** often requires multiple dashboards and manual investigation.

This creates three major problems:

### 1. Fragmented intelligence

Finance, risk, growth and recovery teams operate on separate data and workflows.

### 2. Slow decision making

Important revenue-impacting signals may require manual investigation before an action can be taken.

### 3. Unsafe automation

Giving an LLM unrestricted access to financial operations creates unacceptable risks around hallucination, duplicate execution, incorrect amounts and unauthorized actions.

Merchant Intelligence OS addresses these problems by combining AI reasoning with deterministic financial computation and policy-controlled execution.

---

# 💡 The Solution

Merchant Intelligence OS follows a simple principle:

> **LLM decides what to investigate and explains the result. Deterministic systems calculate financial truth. Policy controls what can happen. APIs execute. Audit records everything.**

The platform contains:

* **Supervisor Orchestrator**
* **Finance Specialist**
* **Risk Specialist**
* **Growth Specialist**
* **Recovery Specialist**
* **Deterministic Financial Engines**
* **Policy Engine**
* **Execution Engine**
* **Idempotency Layer**
* **Audit Trail**
* **Real-time SSE Telemetry**
* **Merchant/Tenant Isolation**

---

# 🧠 Core Architecture

```text
                         Merchant Query
                              │
                              ▼
                  ┌──────────────────────┐
                  │ Supervisor           │
                  │ Orchestrator         │
                  └──────────┬───────────┘
                             │
                Dynamic task decomposition
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
     ┌─────────┐        ┌─────────┐       ┌─────────┐
     │ Finance │        │  Risk   │       │ Growth  │
     │ Agent   │        │ Agent   │       │ Agent   │
     └────┬────┘        └────┬────┘       └────┬────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Recovery Engine │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Multi-Agent     │
                    │ Synthesis       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Policy Engine   │
                    │ Hard Guards     │
                    └────────┬────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
          Auto Execution          Human Approval
                 │                       │
                 └───────────┬───────────┘
                             ▼
                    ┌─────────────────┐
                    │ Execution       │
                    │ Engine          │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Audit +         │
                    │ Telemetry       │
                    └─────────────────┘
```

---

# 🤖 The Four Specialists

## 1. Finance Specialist

Analyzes financial operations including:

* revenue trends
* settlements
* reconciliation
* cash forecasting
* settlement discrepancies

Example finding:

> A settlement discrepancy of ₹78,000 was identified and requires investigation.

---

## 2. Risk Specialist

Analyzes:

* high-risk transactions
* chargebacks
* suspicious transaction patterns
* gateway degradation signals
* model-based risk indicators

Risk decisions are governed by deterministic policy boundaries.

The risk model is currently validated on synthetic data and is explicitly treated as a development/staging model rather than falsely representing a production-calibrated fraud model.

---

## 3. Growth Specialist

Analyzes:

* product conversion
* product performance
* customer/transaction trends
* revenue opportunities
* campaign opportunities

Example:

> Bharat Smart LED TV conversion declined from 4.2% to 2.1%.

The system recommends investigation rather than blindly executing a campaign.

---

## 4. Recovery Specialist

Analyzes:

* failed payments
* recovery candidates
* retry opportunities
* expected recovery value

Example:

```text
84 failed payments
₹9,86,400 gross failed-payment volume
27 recovery candidates
₹2,41,150 candidate amount
₹1,04,704 expected recovery value
```

Expected recovery is explicitly separated from **actual recovered money**.

---

# 🧩 Dynamic Agent Routing

The Supervisor does not blindly invoke every agent.

It dynamically plans the required workflow.

Examples:

```text
Settlement issue
    → Finance

Chargeback
    → Risk + Finance

Payment failure
    → Recovery + Risk

Product conversion issue
    → Growth

Revenue diagnosis
    → Finance + Risk + Growth + Recovery
```

This allows the system to operate as one financial intelligence layer instead of four independent chatbots.

---

# 🔐 AI Safety Architecture

Financial systems cannot rely on an LLM as the final authorization layer.

Merchant Intelligence OS therefore separates:

### Probabilistic intelligence

Used for:

* interpretation
* reasoning
* query understanding
* specialist coordination
* explanation
* synthesis

### Deterministic systems

Used for:

* monetary calculations
* financial metrics
* risk thresholds
* policy decisions
* authorization
* idempotency
* execution state
* audit records

The LLM **cannot directly authorize a monetary action**.

---

# 🛡️ Policy Engine

Every proposed action passes through deterministic hard guards.

Examples:

```text
Risk Score
≤ 0.65        → eligible for automatic consideration
> 0.65        → rejected / escalated

Amount
≤ ₹10,000     → auto-eligible subject to policy
> ₹10,000     → human approval required

Retry Count
≤ 2           → permitted
≥ 3           → rejected

Destructive actions
→ rejected
```

The exact authorization decision is made by the policy layer rather than the LLM.

---

# 🔁 Execution State Machine

Actions follow a controlled lifecycle:

```text
PROPOSED
    │
    ▼
PENDING_APPROVAL
    │
    ▼
APPROVED
    │
    ▼
EXECUTING
    │
    ├──► SUCCESS
    │
    ├──► FAILED
    │
    └──► UNKNOWN
```

An action cannot simply jump from an AI suggestion to financial execution.

---

# ♻️ Idempotency

Payment operations must never accidentally execute twice.

Merchant Intelligence OS uses cryptographic/idempotency keys to prevent duplicate actions.

For example:

```text
Recovery Candidate
       │
       ▼
Idempotency Check
       │
 ┌─────┴─────┐
 │           │
New       Duplicate
 │           │
 ▼           ▼
Execute    Reject
           Safely
```

Concurrent execution is also tested to ensure only one operation wins an idempotency race.

---

# 🔎 Auditability

Every important workflow produces an audit trail.

The system records:

* merchant
* user
* query
* selected agents
* findings
* evidence
* proposed action
* policy decision
* approval
* execution result
* idempotency state
* timestamps

The audit layer also uses a tamper-evident hash chain.

---

# ⚡ Real-Time Telemetry

The application provides real-time SSE telemetry during workflow execution.

Example:

```text
SUPERVISOR
Dynamic DAG planned

FINANCE
Finance analysis starting

RISK
Risk analysis starting

GROWTH
Growth analysis starting

RECOVERY
Recovery candidates ranked

SUPERVISOR
Multi-agent synthesis complete

POLICY
Action requires human approval

EXECUTION
Action completed

AUDIT
Workflow recorded
```

This allows users to see not only the final answer, but **how the system reached it**.

---

# 🏪 Multi-Tenant Architecture

Every merchant operates inside an isolated tenant boundary.

A newly registered user does not inherit another merchant's data.

New accounts begin with:

```text
merchant_id = NULL
```

and complete merchant onboarding before accessing merchant-specific data.

All major data paths are tenant scoped:

* dashboard
* transactions
* agents
* actions
* audit
* SSE events
* workflows
* webhooks

Cross-merchant access is explicitly tested.

---

# 👤 Authentication & Authorization

The application supports:

* account registration
* login
* logout
* password reset
* Google authentication architecture
* merchant onboarding
* role-based authorization

Supported application roles include:

```text
merchant_admin
finance_user
risk_user
operator
customer
```

Sensitive credentials remain server-side.

---

# 🔌 Razorpay Integration

Merchant Intelligence OS is designed for Razorpay integration through:

* Razorpay API authentication
* payment data ingestion
* webhook ingestion
* HMAC-SHA256 webhook verification
* event deduplication
* transaction lineage
* governed execution

The application separates:

```text
SANDBOX
DEMO
LIVE
```

modes.

LIVE execution is protected by an explicit safety gate.

No Razorpay secret keys are committed to this repository.

---

# 🧾 Webhook Security

Incoming Razorpay webhooks are validated using:

```text
Webhook Payload
      │
      ▼
HMAC-SHA256 Verification
      │
      ├── Invalid → Reject
      │
      ▼
Event ID Deduplication
      │
      ▼
Tenant Validation
      │
      ▼
Transaction Processing
```

Malformed or unsigned requests are rejected.

---

# 🧮 Deterministic Financial Engines

The system contains dedicated engines for:

### Settlement Reconciliation

Identifies settlement mismatches between expected and actual financial records.

### Cash Forecasting

Uses time-series forecasting for forward cash estimation.

### Recovery Scoring

Calculates expected recovery value:

```text
Expected Recovery
=
Amount at Risk × Probability of Recovery
```

### Growth Simulation

Evaluates potential campaign or conversion impact.

### Risk ML

Provides risk scoring and model evidence while maintaining explicit synthetic-data governance.

---

# 🧪 Testing

The repository includes tests covering:

* authentication
* registration
* readiness
* tenant isolation
* zero-data merchants
* policy boundaries
* policy authorization
* idempotency
* concurrent idempotency
* execution outcomes
* reconciliation
* recovery
* risk ML
* routing
* webhook ingestion
* security isolation
* production certification

The latest local verification reported:

```text
67 / 67 backend tests passed
Frontend TypeScript + Vite production build passed
```

These are local/staging verification results and should not be interpreted as proof of production infrastructure readiness.

---

# 🧪 Example End-to-End Workflow

Merchant asks:

> "Analyze my revenue performance and identify what I can safely do to recover lost revenue."

Supervisor dynamically activates:

```text
Finance
Risk
Growth
Recovery
```

The system identifies:

```text
Finance
→ Settlement discrepancy

Risk
→ High-risk transaction signals

Growth
→ Product conversion decline

Recovery
→ Failed payment recovery candidates
```

The Supervisor synthesizes the findings.

The Policy Engine evaluates every action.

Example:

```text
8 actions selected

1 automatically executed
7 require human approval
```

Duplicate actions are blocked through idempotency.

The entire workflow is recorded in the audit system.

---

# 📊 Example Merchant Diagnostic

A sample Bharat Commerce analysis produced:

### Finance

```text
Revenue:
₹46,413,400

Revenue change:
+1.2% over the measured period

Settlement discrepancy:
₹78,000
```

### Recovery

```text
Failed payments:
84

Failed-payment volume:
₹986,400

Recovery candidates:
27

Candidate amount:
₹241,150

Expected recovery:
₹104,704
```

### Risk

```text
High-risk transactions:
3
```

### Growth

```text
Bharat Smart LED TV conversion:

Previous:
4.2%

Current:
2.1%

Change:
-50%
```

An important design principle is that the system does **not blindly accept a merchant's hypothesis**.

If a merchant says:

> "Revenue dropped."

but the measured data shows:

> Revenue increased 1.2%.

the system should report the observed fact and explain the actual areas of financial leakage or opportunity.

---

# 🧠 Why AI Is Necessary

The system does not use AI merely to generate dashboard text.

AI provides value in:

### 1. Natural-language problem understanding

A merchant can ask a broad financial question instead of navigating multiple dashboards.

### 2. Dynamic decomposition

The Supervisor converts a broad question into specialist tasks.

### 3. Multi-domain synthesis

The system connects finance, risk, growth and recovery findings.

### 4. Evidence-based explanation

Findings are presented with traceable evidence rather than unsupported claims.

### 5. Adaptive workflow planning

The system can activate different specialists depending on the merchant's question.

At the same time, deterministic components handle financial truth and authorization.

---

# 🏗️ Technology Stack

## Frontend

* React 18
* TypeScript
* Vite
* Tailwind CSS
* Lucide
* Recharts
* Server-Sent Events

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* JWT authentication

## AI

* Gemini
* Agent orchestration
* Structured agent state
* Multi-agent synthesis
* RAG-ready architecture

## Machine Learning

* Scikit-learn
* Random Forest risk model
* Time-series forecasting
* Recovery probability scoring
* Growth simulation

## Database

Development:

* SQLite

Production architecture:

* PostgreSQL

## Integrations

* Razorpay APIs
* Razorpay Webhooks
* Firebase Authentication
* Cloud deployment architecture

---

# 📁 Repository Structure

```text
merchant-intelligence-os/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── finance/
│   │   │   ├── growth/
│   │   │   ├── recovery/
│   │   │   ├── risk/
│   │   │   └── supervisor/
│   │   │
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── engines/
│   │   ├── execution/
│   │   ├── integrations/
│   │   ├── orchestration/
│   │   ├── policies/
│   │   ├── schemas/
│   │   └── workers/
│   │
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   │
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
│
├── firebase.json
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# 🚀 Local Development

## Backend

```bash
cd backend

python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Application:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
```

---

# 🔐 Environment Variables

Create a local `.env` file from `.env.example`.

Never commit `.env`.

Example:

```env
GEMINI_API_KEY=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=

FIREBASE_PROJECT_ID=
FIREBASE_CLIENT_EMAIL=
FIREBASE_PRIVATE_KEY=

DATA_MODE=SANDBOX
DEMO_MODE=false
AUTOMATED_EXECUTION_ENABLED=false
```

Secrets must be supplied through secure deployment configuration.

---

# ☁️ Deployment Architecture

The intended deployment architecture is:

```text
                    Internet
                       │
                       ▼
             ┌──────────────────┐
             │ Firebase Hosting │
             │ React Frontend   │
             └────────┬─────────┘
                      │ HTTPS
                      ▼
             ┌──────────────────┐
             │ Google Cloud Run │
             │ FastAPI Backend  │
             └────────┬─────────┘
                      │
             ┌────────┴─────────┐
             ▼                  ▼
      ┌──────────────┐   ┌──────────────┐
      │ PostgreSQL   │   │ Razorpay     │
      │ Database     │   │ APIs/Webhook │
      └──────────────┘   └──────────────┘
```

Firebase Hosting is used for the frontend while the FastAPI service requires separate backend infrastructure.

---

# ⚠️ Current Limitations

This project intentionally documents its current boundaries.

### 1. Risk model

The current risk model has been validated using synthetic data.

It should not be represented as a production-certified fraud model without real merchant data, calibration and monitoring.

### 2. Database

Local development uses SQLite.

A horizontally scaled production deployment should use managed PostgreSQL and distributed locking/idempotency infrastructure.

### 3. Razorpay LIVE

LIVE execution requires:

* verified Razorpay credentials
* production webhook
* public HTTPS backend
* production database
* deployment secrets
* operational monitoring
* additional production validation

The system defaults to safe execution settings.

### 4. Financial execution

No financial action is automatically authorized by the LLM.

---

# 🔥 What Broke During Development

Building a financial AI system exposed several important engineering problems.

## Cross-merchant data leakage

A fresh user initially surfaced existing merchant data.

### Resolution

Merchant identity was changed to be explicitly associated with the authenticated user and new users begin without a merchant.

Tenant isolation was added across dashboard, transaction, specialist, action, audit and real-time event paths.

---

## False "DB Offline" status

The frontend health check was accidentally calling the Vite development server rather than the backend health endpoint.

### Resolution

The health endpoint routing was corrected so the frontend uses the actual backend API.

---

## Demo data appearing as real intelligence

Specialist pages previously contained assumptions that could make static/demo data appear to be current merchant intelligence.

### Resolution

Specialists were changed to derive findings from the authenticated merchant's actual data source.

---

## AI claiming activity without data

The AI Command Center could previously display active-looking states even when there was no underlying merchant activity.

### Resolution

The system was changed to distinguish between:

```text
ACTIVE
STANDBY
NO DATA
ERROR
```

instead of pretending analysis occurred.

---

## Unsafe secret handling

Real credentials were initially present in a configuration example and GitHub Push Protection blocked the repository.

### Resolution

The Git history was recreated, credentials were removed from `.env.example`, local secrets were excluded from Git, and the clean repository was successfully pushed to GitHub.

---

# 🏆 Buildathon Submission

## Track

**Open Track**

Razorpay describes Open Track as the category for builders who identify a meaningful real-world problem, use AI meaningfully, build something that works, and demonstrate value.

---

## Project Name

**Merchant Intelligence OS**

---

## One-Line Description

> An AI-powered financial operating system that dynamically coordinates finance, risk, growth and revenue-recovery intelligence into one governed merchant workflow.

---

## Problem Statement

> Digital merchants manage revenue, payments, risk, settlements and recovery through fragmented systems. This makes it difficult to identify the true causes of revenue leakage and safely act on them. Merchant Intelligence OS provides a unified AI-driven financial intelligence layer that understands merchant questions, dynamically routes them to specialized financial agents, synthesizes evidence, and uses deterministic policy controls to govern any proposed action.

---

## Why Open Track?

> Merchant Intelligence OS is intentionally broader than a single financial workflow. It addresses the problem of fragmented merchant financial intelligence by connecting revenue analysis, risk, growth, settlement and recovery into one governed system. The Open Track allows us to demonstrate this end-to-end operating model rather than reducing the product to a single isolated agent.

---

## What Makes It Different?

> We are not building four independent AI chatbots. We are building one AI system that dynamically determines which financial capabilities are required for a merchant problem and coordinates them through a shared state, deterministic policy layer, execution engine and audit trail.

---

## AI Contribution

> AI is used for natural-language problem understanding, dynamic workflow decomposition, specialist coordination, evidence synthesis and merchant-facing explanations. Deterministic systems remain responsible for financial calculations, policy authorization, monetary thresholds, idempotency and execution safety.

---

## Value Created

The system aims to reduce the time between:

```text
Problem detected
      ↓
Cause identified
      ↓
Financial impact quantified
      ↓
Action selected
      ↓
Action governed
      ↓
Outcome audited
```

Instead of forcing a merchant to manually correlate multiple operational dashboards.

---

# 🎥 5-Minute Pitch Structure

### 0:00–0:30 — Problem

"Merchant financial problems don't happen in isolated dashboards."

Show the fragmented workflow.

### 0:30–1:00 — Solution

Introduce Merchant Intelligence OS.

Show:

```text
One merchant question
        ↓
Supervisor
        ↓
Finance + Risk + Growth + Recovery
```

### 1:00–2:30 — Live Demo

Ask:

> "Analyze my revenue performance and identify what I can safely do to recover lost revenue."

Show:

* dynamic routing
* specialist findings
* evidence
* recovery candidates
* policy decisions
* approval
* execution
* audit

### 2:30–3:30 — Architecture

Explain:

```text
LLM
↓
Structured findings
↓
Deterministic engines
↓
Policy
↓
Execution
↓
Audit
```

Emphasize:

> "The LLM never gets the final authority over money."

### 3:30–4:30 — Engineering Depth

Demonstrate:

* tenant isolation
* idempotency
* webhook verification
* action state machine
* policy boundaries
* failure handling
* real-time telemetry

### 4:30–5:00 — Results & Future

Show:

* recovery opportunity
* settlement discrepancy
* risk findings
* conversion opportunity
* test results
* current limitations
* future Razorpay LIVE integration

End with:

> **"We don't build four AI agents. We build one AI system that makes four financial capabilities work together."**

---

# 🔗 Links

## GitHub

https://github.com/JogiRohithKumar/merchant-intelligence-os

## Live Demo

*To be added after Firebase + backend deployment.*

## Pitch Video

*To be added after recording the 5-minute pitch.*

## Architecture

See the architecture section above.

---

# 📜 Safety & Responsible AI

Merchant Intelligence OS is designed around bounded AI.

The system does not allow an LLM to independently:

* authorize monetary actions
* bypass policy
* change financial amounts
* bypass idempotency
* access another merchant's data
* execute destructive operations

AI proposes and explains.

Deterministic systems verify and govern.

---

# 🔮 Future Roadmap

### Phase 1 — Deployment

* Firebase Hosting
* Cloud Run
* PostgreSQL
* secure deployment secrets

### Phase 2 — Razorpay Integration

* Razorpay Test APIs
* real test transactions
* public webhook
* event ingestion
* transaction synchronization

### Phase 3 — Production Intelligence

* real merchant data
* calibrated risk models
* model monitoring
* distributed idempotency
* Redis
* stronger observability

### Phase 4 — Merchant Intelligence

* proactive anomaly detection
* automated financial briefings
* merchant-specific policy learning
* predictive revenue leakage
* intelligent campaign optimization

---

# 👨‍💻 Built For

**Razorpay AI Buildathon 2026**

**Track:** Open Track

**Project:** Merchant Intelligence OS

---

## Final Statement

Merchant Intelligence OS is built around a simple idea:

> **A merchant should not have to become a financial operations expert to understand what is happening to their business.**

The system brings financial intelligence, risk analysis, growth opportunities and revenue recovery into one governed AI operating system.

**Understand → Diagnose → Decide → Govern → Execute → Learn**
