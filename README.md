# Merchant Intelligence OS

> **Razorpay AI Buildathon 2026 — Open Track**

An AI-powered financial operating system for merchants that unifies **Growth, Risk, Revenue Recovery, and Finance** into one intelligent decision-making platform.

## 🚀 What We Built

Merchant Intelligence OS transforms raw merchant transaction data into **evidence-backed insights, recommendations, and safe actions**.

Instead of building four disconnected AI bots, we built **one AI system that coordinates specialized financial capabilities** through a dynamic supervisor.

### Core Capabilities

- **AI Supervisor** — Understands merchant problems, decomposes them, and dynamically routes work across specialist agents.
- **Finance Agent** — Analyzes revenue, settlements, reconciliation, and cash-flow signals.
- **Risk Agent** — Identifies suspicious transactions and customer/payment risk.
- **Growth Agent** — Detects conversion and revenue-growth opportunities.
- **Recovery Agent** — Finds failed-payment recovery opportunities and estimates recovery value.
- **Policy Engine** — Applies deterministic rules before any action can execute.
- **Action Execution** — Supports safe, idempotent execution with approval controls.
- **Audit & Observability** — Tracks decisions, actions, execution states, and system events.

## 🧠 How It Works

```text
Merchant Query
      ↓
AI Supervisor
      ↓
Dynamic Task Decomposition
      ↓
┌──────────┬──────────┬──────────┬──────────┐
│ Finance  │   Risk   │  Growth  │ Recovery │
└──────────┴──────────┴──────────┴──────────┘
      ↓
Evidence & Findings
      ↓
Deterministic Policy Engine
      ↓
Approval / Safe Execution
      ↓
Outcome + Audit Trail
