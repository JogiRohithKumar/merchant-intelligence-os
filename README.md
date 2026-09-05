# Merchant Intelligence OS

> **AI-Powered Financial Operating System for Merchants**
> Built for the **Razorpay AI Buildathon 2026 — Open Track**

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev/)
[![Gemini](https://img.shields.io/badge/AI-Gemini-orange)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](#license)

## 🚀 Overview

**Merchant Intelligence OS** is an AI-powered financial operating system designed to help merchants understand, manage, and improve their payment business from a single intelligent interface.

Instead of building isolated AI bots for individual financial tasks, the system uses a **Supervisor Agent** that understands a merchant's problem, dynamically decomposes it, coordinates specialized agents, evaluates their findings, applies deterministic safety policies, and recommends or executes safe actions.

### The Core Idea

> **One merchant problem → Multiple specialized agents → One coordinated decision → Safe execution → Measurable outcome**

---

## 🎯 Problem

Merchants typically need to analyze several disconnected areas:

* Revenue and transaction performance
* Payment failures and recovery
* Fraud and transaction risk
* Settlement discrepancies
* Customer conversion and growth

These areas are highly interconnected.

For example:

> **"My revenue is dropping. Why, and what can I safely do about it?"**

Answering this properly may require analyzing payment failures, settlement issues, customer risk, conversion performance, and recovery opportunities simultaneously.

Merchant Intelligence OS brings these capabilities together into **one coordinated intelligence layer**.

---

# 🧠 Solution

The platform uses a **multi-agent orchestration architecture** consisting of:

### 1. Supervisor Agent

The central intelligence layer.

It:

* Understands the merchant's request
* Decomposes complex problems
* Determines which agents are required
* Builds the execution workflow dynamically
* Coordinates dependencies between agents
* Synthesizes findings
* Passes proposed actions through policy controls

### 2. Finance Agent

Analyzes:

* Revenue trends
* Transaction performance
* Settlement reconciliation
* Cash-flow conditions
* Financial anomalies

### 3. Risk Agent

Analyzes:

* Transaction risk
* Fraud indicators
* Customer/device patterns
* Risk scores
* Suspicious activity

### 4. Growth Agent

Analyzes:

* Conversion performance
* Product/customer performance
* Revenue opportunities
* Growth signals
* Potential optimization opportunities

### 5. Recovery Agent

Identifies:

* Failed payments
* Recoverable transactions
* Retry opportunities
* Expected recovery value
* Recovery actions

---

# 🔄 How It Works

```text
Merchant Query
      │
      ▼
Supervisor Agent
      │
      ├──────────────┐
      ▼              ▼
   Finance          Risk
      │              │
      ├──────┬───────┤
             ▼
          Growth
             │
             ▼
         Recovery
             │
             ▼
      Shared Findings
             │
             ▼
       Policy Engine
             │
      ┌──────┴──────┐
      ▼             ▼
 Auto Execute   Human Approval
      │             │
      └──────┬──────┘
             ▼
        Execution
             │
             ▼
      Audit + Outcome
```

The system does **not** allow an LLM to directly control financial execution.

Instead:

> **LLM decides and explains → Data/ML calculates → Policy controls → APIs execute → Audit records**

---

# ⚙️ Key Technical Features

### Dynamic Agent Orchestration

The Supervisor dynamically determines the required specialists instead of always running every agent.

Workflows can be represented as a dependency-aware DAG.

### Shared Agent State

Agents communicate through structured state and standardized findings rather than passing unstructured text between agents.

### Deterministic Financial Computation

Financial calculations are handled by dedicated computation engines rather than relying on LLM-generated numbers.

Implemented capabilities include:

* Settlement reconciliation
* Cash forecasting
* Risk scoring
* Recovery value estimation
* Conversion/uplift analysis

### Policy Engine

Every proposed action is evaluated against deterministic business and safety rules.

Examples:

| Rule                | Decision                         |
| ------------------- | -------------------------------- |
| Risk ≤ 0.65         | Eligible for automated execution |
| Risk > 0.65         | Rejected                         |
| Amount ≤ ₹10,000    | Auto-execution eligible          |
| Amount > ₹10,000    | Human approval required          |
| Retry count ≤ 2     | Allowed                          |
| Retry count ≥ 3     | Rejected                         |
| Destructive actions | Rejected                         |

The LLM **cannot override these rules**.

---

# 🛡️ Safety & Reliability

Financial automation requires strong controls.

Merchant Intelligence OS implements:

* JWT authentication
* Merchant-level tenant isolation
* Role-based authorization
* Razorpay webhook signature validation
* HMAC-SHA256 verification
* Constant-time signature comparison
* Cryptographic idempotency
* Human approval workflows
* Execution state tracking
* Audit logging
* Fail-closed execution gates
* Sensitive credential protection
* Data provenance tracking

### Execution Lifecycle

```text
PROPOSED
   ↓
PENDING_APPROVAL
   ↓
APPROVED
   ↓
EXECUTING
   ↓
SUCCESS / FAILED / UNKNOWN
```

An execution is considered successful only after confirmation from the payment gateway.

---

# 📊 Example: Revenue Investigation

A merchant can ask:

> **"Analyze my revenue performance, identify the major problems, and tell me what I can safely do to recover lost revenue."**

The system can coordinate:

```text
Supervisor
    ↓
Finance ──→ Revenue / Settlement Analysis
    ↓
Risk ─────→ Transaction Risk
    ↓
Growth ───→ Conversion Opportunities
    ↓
Recovery ─→ Failed Payment Recovery
    ↓
Policy Engine
    ↓
Recommended Actions
```

The final response combines the findings into an **executive-level recommendation** instead of returning four disconnected agent responses.

---

# 💰 Recovery Intelligence

The Recovery Agent estimates the value of potential recovery opportunities.

For a candidate payment:

```text
Expected Recovery Value
=
Amount × Probability of Recovery
```

This allows the system to prioritize recovery opportunities based on expected financial impact rather than simply listing failed transactions.

---

# 🔐 Razorpay Integration

The system is designed to integrate with Razorpay for:

* Payment data
* Webhooks
* Transaction events
* Payment retry execution

The application supports separate operating modes:

```text
SANDBOX
DEMO
LIVE
```

Real execution is protected by a safety gate requiring:

```text
LIVE mode
+
Live credentials
+
Automated execution enabled
+
Valid configuration
```

Without these conditions, real financial execution is blocked.

---

# 🧪 Validation

The current implementation has been extensively tested across:

* Authentication
* Tenant isolation
* Agent orchestration
* Policy boundaries
* Webhook security
* Idempotency
* Reconciliation
* Execution safety
* Risk model validation
* Frontend build
* Backend APIs

### Current validation

**67/67 backend tests passing**

Frontend production build also completes successfully.

The current system is validated for:

> **Sandbox / Staging deployment**

Live production execution still requires external infrastructure and production credentials.

---

# 🏗️ Technology Stack

### Frontend

* React 18
* Vite
* Tailwind CSS
* Lucide
* Recharts

### Backend

* Python
* FastAPI
* Pydantic
* JWT Authentication

### AI / ML

* Google Gemini
* Multi-Agent Architecture
* Dynamic Agent Orchestration
* Random Forest Risk Model
* Holt Double Exponential Forecasting

### Data & Infrastructure

* SQLite for development/staging
* Razorpay APIs & Webhooks
* REST APIs
* Server-Sent Events
* Cryptographic Idempotency

---

# 📁 Architecture

```text
merchant-intelligence-os/
│
├── backend/
│   ├── agents/
│   │   ├── supervisor/
│   │   ├── finance/
│   │   ├── risk/
│   │   ├── growth/
│   │   └── recovery/
│   │
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── policy/
│   ├── execution/
│   ├── security/
│   └── app/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── services/
│
├── .env.example
├── README.md
└── ...
```

---

# 🎥 Buildathon Demo Flow

The recommended demonstration focuses on one end-to-end merchant problem:

### Step 1

Merchant asks:

> **"Why is my revenue underperforming, and what can I safely do to recover it?"**

### Step 2

Supervisor dynamically creates the required workflow.

### Step 3

Finance, Risk, Growth and Recovery analyze the merchant data.

### Step 4

The Supervisor synthesizes the findings.

### Step 5

The Policy Engine evaluates proposed actions.

### Step 6

Low-risk actions can be automatically executed within configured limits.

### Step 7

Higher-value or sensitive actions are sent for human approval.

### Step 8

Every execution is recorded and its outcome can be measured.

---

# 🌟 What Makes It Different

Most AI financial applications answer questions.

**Merchant Intelligence OS is designed to move from:**

```text
Question
   ↓
Analysis
   ↓
Decision
   ↓
Policy
   ↓
Action
   ↓
Outcome
```

The key differentiator is **coordinated, policy-controlled financial intelligence**, rather than a collection of independent chatbots.

---

# 🚧 Current Status

### Buildathon Status

**Production-grade Sandbox/Staging Release Candidate**

Implemented:

* Multi-agent architecture
* Dynamic orchestration
* Financial intelligence
* Risk analysis
* Revenue recovery
* Growth intelligence
* Policy-controlled actions
* Human approval
* Auditability
* Tenant isolation
* Razorpay integration layer
* Security controls
* Automated testing

### Remaining for Full Live Production

* Production Razorpay credentials
* Public HTTPS webhook deployment
* Managed PostgreSQL
* Distributed idempotency/locking for horizontal scaling
* Production risk-model calibration with real merchant data

---

# 👥 Team

Built for the **Razorpay AI Buildathon 2026**.

**Track:** Open Track

---

# 📜 License

MIT License.
