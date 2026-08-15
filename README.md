# 💧 Narmada Jal Nyay AI
## Fair Water for Every Farmer – Agentic AI-Powered Canal Water Distribution & Equity Monitor

> **Hackathon Prototype** | IBM Bob · IBM Granite LLM · IBM Cloud | Water Resource Management – Gujarat

---

## 🎯 What Is This?

**Narmada Jal Nyay AI** ("Jal Nyay" = Water Justice) is an Agentic AI system that monitors the Narmada canal network in Gujarat, ensures equitable water distribution between head-reach and tail-end farmers, detects disputes, and provides AI-powered insights using **IBM Granite LLM** via **IBM watsonx.ai**.

### The Problem
Unequal and inefficient distribution of Narmada canal water across head-reach and tail-end farmers leads to:
- Water shortages and crop stress for tail-end farmers
- Disputes and social tension between farming communities
- Wasted water due to poor scheduling

### Our Solution
An **Agentic AI system** with five specialised agents that autonomously monitor, analyse, schedule, and alert – while keeping humans in the loop for critical decisions.

---

## 🤖 Five AI Agents

| # | Agent | Autonomous | Human Approval Needed |
|---|-------|-----------|----------------------|
| 1 | **Canal Flow Monitoring Agent** | Detects anomalies, generates alerts | Gate adjustments > 20% |
| 2 | **Equitable Distribution Agent** | Calculates fair allocations | Shortage > 25%, gap > 20% |
| 3 | **Farmer Alert Agent** | Sends notifications in Gujarati/English | Emergency field bypasses |
| 4 | **Dispute Detection & Mediation Agent** | Classifies complaints, drafts resolutions | All resolution implementations |
| 5 | **Irrigation Efficiency Dashboard Agent** | Aggregates metrics, generates AI insights | None (read-only) |

---

## ⚖️ Water Equity Algorithm

```
Priority Score = crop_stress_weight × equity_factor × deficit_boost × land_weight

Where:
  equity_factor  = 0.95 (head) / 1.00 (middle) / 1.12 (tail)  ← tail-end gets boost
  deficit_boost  = 1 + deficit_ratio × (0.5 + shortage_level × 0.5)
  land_weight    = √(land_area) / √(5)

Fairness Score = Actual Water Allocated / Expected Water Requirement
```

**Sample Scenario (18% shortage):**

| Farmer | Reach | Crop | Expected | Allocated | Fairness |
|--------|-------|------|----------|-----------|---------|
| F100 | Head | Cotton | 175 m³ | 165 m³ | 94.3% |
| F103 | Middle | Bajra | 110 m³ | 98 m³ | 89.1% |
| F106 | **Tail** | **Cotton** | **245 m³** | **206 m³** | **84.1%** |
| F108 | **Tail** | Vegetables | 78 m³ | 67 m³ | **85.9%** |

*Before optimisation: tail-end gap = 32%. After: gap reduced to 8-15%.*

---

## 🏗️ Architecture

```
Canal Sensors/Data
        │
        ▼
Agent 1: Canal Flow Monitoring
        │ (shortage detected?)
        ▼
Agent 2: Equitable Distribution Scheduling
        │
        ├──► Agent 3: Farmer Alert Agent ──► SMS/WhatsApp/Dashboard
        │
        ▼
Agent 4: Dispute Detection & Mediation
        │ (AI analysis via Granite)
        ▼
Agent 5: Dashboard Agent ──► Authority Dashboard
        │
        ▼
  IBM Granite LLM (explanations, recommendations, chat)
        │
        ▼
  Human Canal Authority (approves critical actions)
```

### IBM Technology Stack

| Component | IBM Service | Purpose |
|-----------|------------|---------|
| LLM reasoning | IBM Granite 13B Chat (watsonx.ai) | Explanations, complaint analysis, chat |
| Backend | IBM Cloud Code Engine | FastAPI Python backend |
| Database | IBM Cloud Databases (PostgreSQL) | Production DB |
| Object Storage | IBM Cloud Object Storage | Historical sensor data |
| Event Streaming | IBM Event Streams (Kafka) | Real-time sensor events |
| Monitoring | IBM Cloud Monitoring | System health |
| Dev Environment | IBM Bob | Development & testing |

---

## 📁 Project Structure

```
narmada-jal-nyay-ai/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── api/
│   │   ├── canal.py               # Canal monitoring endpoints
│   │   ├── farmers.py             # Farmer management
│   │   ├── schedule.py            # Distribution scheduling
│   │   ├── complaints.py          # Disputes & complaints
│   │   ├── dashboard.py           # Dashboard & AI chat
│   │   ├── alerts.py              # Alerts
│   │   ├── simulate.py            # Demo simulation
│   │   └── auth.py                # JWT authentication
│   ├── agents/
│   │   └── agents.py              # All 5 AI agents + orchestrator
│   ├── ml/
│   │   ├── water_equity.py        # Fairness algorithm
│   │   └── models.py              # Flow/anomaly/demand ML models
│   ├── services/
│   │   ├── granite_service.py     # IBM Granite integration
│   │   └── sensor_simulator.py   # Sensor data simulation
│   └── database/
│       ├── models.py              # SQLAlchemy ORM
│       ├── db.py                  # DB connection
│       └── seed.py                # 90 synthetic farmers + data
├── frontend/
│   └── src/
│       ├── App.jsx                # Main app + routing
│       ├── pages/
│       │   ├── AuthorityDashboard.jsx
│       │   ├── CanalMonitoring.jsx
│       │   ├── WaterDistribution.jsx
│       │   ├── FarmerPortal.jsx
│       │   ├── DisputeManagement.jsx
│       │   └── AIAssistant.jsx
│       ├── components/
│       │   ├── ui.jsx             # Reusable components
│       │   └── CanalMap.jsx       # SVG canal visualization
│       └── services/
│           └── api.js             # API client
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- IBM watsonx.ai account (optional – runs in offline mode without it)

### Backend Setup

```bash
cd narmada-jal-nyay-ai

# Copy and configure environment
cp .env.example .env
# Edit .env with your IBM watsonx credentials (optional)

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend
uvicorn backend.main:app --reload --port 8000
```

The backend will:
1. Create the SQLite database
2. Seed 90 synthetic farmers, sensor data, complaints, and schedules
3. Start the API server at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open `http://localhost:5173` in your browser.

### API Documentation
Open `http://localhost:8000/docs` for the interactive Swagger UI.

---

## 🔑 Default Login Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| authority | auth123 | Canal Authority |
| farmer1 | farmer123 | Farmer |

---

## 🎬 Demo Scenario

**"20% Water Reduction Emergency"**

1. Click **"Run Demo Scenario"** on the Authority Dashboard
2. Switch the scenario selector to **"Shortage"**
3. Observe the canal monitoring page – tail sensors turn red
4. Check the distribution page – see fairness recalculation in real-time
5. View AI-generated Granite explanation for affected farmers
6. Go to Disputes – see auto-detected systemic tail-end complaints
7. Use AI Assistant – ask "Why is tail-end receiving less water?"

### Expected Demo Output
- Before: Head equity 92%, Tail equity 68%, Gap = 24%
- After AI rebalancing: Head equity 89%, Tail equity 80%, Gap = 9%
- 100% of tail-end farmers protected above 70% fairness threshold
- Granite generates farmer-friendly explanation in English/Gujarati

---

## 📊 KPIs

| KPI | Formula | Target |
|-----|---------|--------|
| Distribution Equity | Σ(actual/expected) / N | > 90% |
| Head-Tail Gap | Head_avg_fairness – Tail_avg_fairness | < 10% |
| Shortage Response Time | Alert timestamp → Schedule update | < 15 min |
| Dispute Resolution Rate | Resolved / Total complaints | > 80% |
| Water Use Efficiency | Delivered / Available | > 88% |

---

## 🔐 Security

- JWT-based authentication with role separation (admin / authority / farmer)
- No hardcoded API keys – all secrets via `.env`
- Input validation on all API endpoints
- Farmers can only access their own data (farmer role)
- All AI recommendations require human approval for critical actions

---

## 🌍 IBM Granite LLM – Where It's Used

| Use Case | Granite Role |
|----------|-------------|
| Farmer alerts | Convert technical allocation data into friendly messages (Gujarati/English) |
| Shortage explanation | Explain water shortage causes to farmers in simple terms |
| Complaint analysis | Classify severity, identify root cause, recommend resolution |
| Dashboard insight | Generate "Tail-end villages are receiving X% less..." natural language insight |
| Dispute mediation | Summarise evidence and draft fair resolution recommendations |
| AI chat assistant | Answer authority/farmer questions about canal conditions |

> **Architecture principle:** IBM Granite handles ONLY reasoning and explanation.  
> All numerical calculations (allocation, fairness scores, anomaly detection) use deterministic Python algorithms and ML models.

---

## 🏆 Innovation Highlights

1. **Fairness-First Algorithm** – Tail-end farmers receive equity boost factor (1.12×) to overcome structural canal disadvantage
2. **Deficit Carry-Forward** – Historical under-delivery is tracked and compensated in future cycles
3. **Agentic Autonomy** – Agents act independently for non-critical decisions; human in the loop for critical ones
4. **Bilingual AI** – IBM Granite generates farmer messages in Gujarati and English
5. **Explainable AI** – Every AI recommendation includes a plain-language explanation
6. **Dispute Prevention** – Systemic pattern detection identifies structural inequity before individual complaints escalate

---

## ⚠️ Disclaimer

This is a hackathon prototype using **fully synthetic data**. It does not represent real Narmada canal operations, actual farmer data, or real sensor readings. The system is designed to demonstrate the concept and technical feasibility.

---

*Built with ❤️ using IBM Bob · IBM Granite · IBM Cloud · FastAPI · React*
