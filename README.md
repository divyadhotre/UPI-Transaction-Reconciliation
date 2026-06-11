# 💰 UPI Transaction Reconciliation & Fraud Detection

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live-00d4aa?style=for-the-badge)

### An end-to-end ML-powered reconciliation engine for Indian UPI & bank transactions — with real-time fraud detection, discrepancy categorization, and an interactive analytics dashboard.

**[🚀 Live Demo](#)** · **[📊 View Dashboard](#)** · **[📥 Download Sample Data](#)**

---

![Dashboard Preview](assets/dashboard_preview .png)


</div>

---

## 🎯 Problem Statement

> **India processes 10+ Billion UPI transactions every single month.**
> Even a 0.1% discrepancy rate = **10 million unresolved transactions**.
> That's real money stuck — for real people, real businesses, real banks.

Manual reconciliation between bank ledgers and UPI statements is:
- ❌ Slow — finance teams spend days matching records manually
- ❌ Error-prone — humans miss patterns that ML catches instantly
- ❌ Expensive — every unresolved discrepancy costs time and trust

**This project automates the entire reconciliation pipeline** — from raw CSV upload to discrepancy detection, fraud flagging, and downloadable audit reports — in seconds.

---

## ✨ What This Project Does

| Feature | Description |
|---|---|
| 🔄 **Smart Reconciliation** | Matches bank ledger vs UPI statement record-by-record on transaction ID |
| ⚠️ **Discrepancy Categorization** | Classifies every mismatch: Amount Error, Status Conflict, Missing Entry |
| 🚨 **ML Fraud Detection** | Isolation Forest algorithm flags statistically anomalous transactions |
| 📊 **Interactive Dashboard** | 5 real-time charts — bank-wise rates, merchant heatmap, amount distribution |
| 📥 **Audit Report Export** | Download full reconciliation report as CSV for compliance |
| 📂 **Any CSV Upload** | Auto-detects column names — works with any bank's export format |

---

## 📊 Results (on 500 Indian UPI Transactions)

```
Total Transactions Processed  →  500
✅ Successfully Matched        →  450  (90.0% match rate)
⚠️ Discrepancies Detected      →  50   (10.0% error rate)
🚨 Suspicious Transactions     →  25   (5.0% flagged by ML)
💸 Total Amount Gap Found      →  ₹68,013  unreconciled value
```

### Discrepancy Breakdown
```
AMOUNT_MISMATCH   ████████████████████  43 cases
STATUS_CONFLICT   ████                   7 cases
MISSING_IN_UPI    ██                     0 cases
```

---

## 🏗️ Project Architecture

```
UPI-Transaction-Reconciliation/
│
├── 📁 data/
│   ├── bank_ledger.csv          ← Internal bank records
│   └── upi_transactions.csv     ← External UPI statement
│
├── 📁 notebooks/
│   ├── 01_create_data.ipynb     ← Synthetic Indian dataset generator
│   ├── 02_EDA.ipynb             ← Exploratory data analysis
│   └── 03_reconciliation.ipynb  ← Core reconciliation logic
│
├── 📁 src/
│   ├── reconcile.py             ← Matching engine + discrepancy classifier
│   ├── fraud_detector.py        ← Isolation Forest anomaly detection
│   └── utils.py                 ← Helper functions
│
├── 📁 assets/                   ← Screenshots and chart exports
├── app.py                       ← Streamlit dashboard (main entry point)
├── requirements.txt             ← Python dependencies
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.10+ | Core logic |
| Data Processing | Pandas, NumPy | Data cleaning, merging, analysis |
| Machine Learning | Scikit-learn (Isolation Forest) | Unsupervised fraud detection |
| Visualization | Matplotlib, Seaborn | Custom dark-theme charts |
| Web App | Streamlit | Interactive dashboard & file upload |
| Dataset | Synthetic Indian UPI data | SBI, HDFC, ICICI, Axis, Kotak |

---

## 🚀 Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/UPI-Transaction-Reconciliation.git
cd UPI-Transaction-Reconciliation

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate sample data
python -c "exec(open('notebooks/generate_data.py').read())"

# 5. Launch dashboard
streamlit run app.py
```

Open `http://localhost:8501` → click **Load Sample Indian Data** → explore.

---

## 📈 Key Insights from the Data

- **ICICI Bank** had the highest discrepancy rate at **13.5%** — 2x the dataset average
- **Zomato & Amazon** appear most frequently in flagged transactions
- **ATM withdrawals** showed the highest anomaly rate among transaction types
- **Large transactions (₹40,000+)** were 3x more likely to have amount mismatches
- **5% of all transactions** were flagged as suspicious by Isolation Forest

---

## 🧠 How the ML Works

### Reconciliation Engine (`src/reconcile.py`)
1. Outer join bank ledger + UPI statement on `txn_id`
2. Calculate `amount_diff` between the two sources
3. Classify each record into 5 categories:
   - `MATCHED` — exact match, no issues
   - `AMOUNT_MISMATCH` — same ID, different amount (>₹1 difference)
   - `STATUS_CONFLICT` — same ID, different transaction status
   - `MISSING_IN_UPI` — exists in bank but not in UPI statement
   - `MISSING_IN_BANK` — exists in UPI but not in bank ledger

### Fraud Detector (`src/fraud_detector.py`)
1. Encode categorical features (bank, type, merchant) using LabelEncoder
2. Train Isolation Forest on `[amount_inr, type_enc, bank_enc, merchant_enc]`
3. `contamination=0.05` — flags top 5% most anomalous transactions
4. Returns `is_suspicious` boolean column for each transaction

---

## 🌐 Deployment

Live on Streamlit Cloud → **[Click here to open the app](#)**

To deploy your own instance:
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file as `app.py`
5. Click Deploy — live in 2 minutes

---

## 💡 What I Added Beyond the Base Project

This project was inspired by a base reconciliation notebook and significantly extended:

- ✅ **Indian UPI dataset** — synthetic data with SBI, HDFC, Zomato, IRCTC, PhonePe
- ✅ **Fraud detection module** — Isolation Forest (not present in original)
- ✅ **5-chart visual dashboard** — dark theme, professional styling
- ✅ **Discrepancy categorization** — classifies WHY each record mismatches
- ✅ **Streamlit web app** — interactive upload, real-time analysis, CSV export
- ✅ **Auto column detection** — accepts any CSV format from any bank
- ✅ **KPI summary cards** — match rate, discrepancy count, amount gap

---

## 🎯 Real-World Application

This project directly applies to:
- 🏦 **Banks** — reconciling core banking vs payment gateway records
- 💳 **Fintech startups** — Razorpay, PhonePe, Paytm daily settlement reconciliation
- 🏢 **Finance teams** — monthly bank statement reconciliation
- 🔍 **Auditors** — flagging suspicious transaction patterns for investigation

---

## 👨‍💻 About Me

**[Divya Dhotre]** — CSE Student  

I built this project  to apply Python, Pandas, and Machine Learning to a real-world fintech problem that affects billions of Indians daily.




---

## 📄 License

MIT License — feel free to use, modify, and build on this project.

---

<div align="center">
<i>If this project helped you or inspired you, please ⭐ star the repo!</i>
</div>
