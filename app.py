import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys, os
from src.chatbot import setup_gemini, build_data_context, get_ai_response
sys.path.append(os.path.dirname(__file__))
from src.reconcile import run_reconciliation, get_summary
from src.fraud_detector import detect_anomalies

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UPI Reconciliation Dashboard",
    page_icon="💰", layout="wide"
)

# Initialize Gemini modern client once
if 'gemini_client' not in st.session_state:
    st.session_state['gemini_client'] = setup_gemini()

# Initialize chat log history
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* KPI Cards — fixed overflow */
.metric-card {
    background: linear-gradient(135deg,#1e2130,#252840);
    border:1px solid #3d4266; border-radius:12px;
    padding:16px 10px; text-align:center;
    height:auto; min-height:100px;
    word-wrap:break-word; overflow-wrap:break-word;
    box-sizing:border-box;
}
.metric-value {
    font-size:1.75rem; font-weight:700; color:#fff;
    line-height:1.2; margin:6px 0; display:block;
}
.metric-label {
    font-size:0.78rem; color:#8b92b3;
    margin-bottom:4px; line-height:1.4;
    display:block; word-break:break-word;
}
.metric-delta-good { font-size:0.73rem; color:#00d4aa; display:block; line-height:1.4; }
.metric-delta-bad  { font-size:0.73rem; color:#ff6b6b; display:block; line-height:1.4; }

/* Section headers */
.section-header {
    font-size:1.05rem; font-weight:600; color:#e0e4ff;
    margin:1.5rem 0 0.8rem 0;
    border-left:4px solid #7c83ff; padding-left:12px;
}

/* Insight boxes */
.insight-box {
    background:#1a1d2e; border:1px solid #3d4266;
    border-radius:10px; padding:14px 16px;
    margin-bottom:8px; min-height:64px;
    box-sizing:border-box;
}
.insight-text {
    color:#e0e4ff; font-size:0.87rem;
    line-height:1.7; display:block;
}
.risk-high   { color:#ff4444; font-weight:700; }
.risk-medium { color:#ffa64d; font-weight:700; }
.risk-low    { color:#00d4aa; font-weight:700; }

/* Sidebar built-by block */
.sidebar-info {
    font-size:0.77rem; color:#8b92b3;
    line-height:1.7; padding:4px 0;
}

/* Hide streamlit branding */
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding:1.2rem 0 0.4rem 0;'>
  <h1 style='color:#fff;font-size:2rem;margin:0;font-weight:700;'>
    💰 UPI Transaction Reconciliation
  </h1>
  <p style='color:#7c83ff;font-size:0.95rem;margin:4px 0 0 0;'>
    ML-powered Fraud Detection & Discrepancy Analysis · India Fintech
  </p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Upload Transaction Files")
    st.markdown(
        "<p style='font-size:0.78rem;color:#8b92b3;margin-top:-8px;'>"
        "Upload your own CSVs or use sample data below</p>",
        unsafe_allow_html=True
    )
    bank_file = st.file_uploader("🏦 Bank Ledger (CSV)", type='csv')
    upi_file  = st.file_uploader("📱 UPI Statement (CSV)", type='csv')
    st.divider()

    if st.button("▶ Load Sample Indian Data", use_container_width=True):
        try:
            bank_df = pd.read_csv('data/bank_ledger.csv')
            upi_df  = pd.read_csv('data/upi_transactions.csv')
            st.session_state['bank_df'] = bank_df
            st.session_state['upi_df']  = upi_df
            st.success("✅ Sample data loaded!")
        except FileNotFoundError:
            st.error("❌ data/ folder not found. Run data generator first.")

    st.divider()

    # ── Built-by block — clean, no overflow ──────────────────────────────────
    st.markdown("""
    <div class="sidebar-info">
      <b style='color:#e0e4ff;font-size:0.82rem;'>Built by</b><br>
      Divya Dhotre · CSE  Student <br><br>
      <b style='color:#e0e4ff;font-size:0.82rem;'>Tech Stack</b><br>
      Python · Pandas · NumPy<br>
      Scikit-learn · Isolation Forest<br>
      Streamlit · Matplotlib
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Quick stats pill ─────────────────────────────────────────────────────
    st.markdown("""
    <div style='background:#1a1d2e;border:1px solid #3d4266;
                border-radius:8px;padding:10px 12px;font-size:0.77rem;
                color:#8b92b3;line-height:1.8;'>
      <b style='color:#e0e4ff;'>📌 How to use</b><br>
      1. Upload Bank Ledger CSV<br>
      2. Upload UPI Statement CSV<br>
      3. Dashboard updates instantly<br>
      <span style='color:#7c83ff;'>Or click Load Sample Data ↑</span>
    </div>
    """, unsafe_allow_html=True)

    # ── ADDITION 3: AI Chatbot Side Panel ────────────────────────────────────

    st.divider()
    st.markdown("""
    <div style='font-size:0.82rem;font-weight:500;
                color:var(--color-text-primary);margin-bottom:6px;'>
      🤖 AI Transaction Assistant
    </div>
    <div style='font-size:0.75rem;color:#8b92b3;margin-bottom:10px;line-height:1.5;'>
      Ask anything about your transaction data
    </div>
    """, unsafe_allow_html=True)

    # Suggested questions
    suggestions = [
        "Which bank has highest risk?",
        "How many frauds detected?",
        "What is the total amount gap?",
        "Which merchant causes most issues?",
    ]
    st.markdown("<div style='font-size:0.72rem;color:#8b92b3;margin-bottom:4px;'>Quick questions:</div>",
                unsafe_allow_html=True)
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        if cols[i % 2].button(suggestion, key=f"sugg_{i}",
                               use_container_width=True):
            st.session_state['pending_question'] = suggestion

    # Chat input
    user_input = st.chat_input("Ask about your transactions...")

    # Handle question (from input or suggestion button)
    question = user_input or st.session_state.pop('pending_question', None)

    if question and 'bank_df' in st.session_state:
        # FIXED: Look up 'gemini_client' to match your top initialization line
        client_instance = st.session_state.get('gemini_client')
        
        if client_instance:
            result_temp  = run_reconciliation(
                st.session_state['bank_df'],
                st.session_state['upi_df']
            )
            summary_temp = get_summary(result_temp)
            flagged_temp = detect_anomalies(st.session_state['bank_df'])
            context = build_data_context(result_temp, summary_temp, flagged_temp)

            st.session_state['chat_history'].append({
                "role": "user", "content": question
            })
            with st.spinner("Thinking..."):
                answer = get_ai_response(
                    client_instance, question, context,
                    st.session_state['chat_history']
                )
            st.session_state['chat_history'].append({
                "role": "assistant", "content": answer
            })
        else:
            st.session_state['chat_history'].append({
                "role": "user", "content": question
            })
            st.session_state['chat_history'].append({
                "role": "assistant",
                "content": "⚠️ Gemini API key not configured. Add it to .streamlit/secrets.toml"
            })
    elif question and 'bank_df' not in st.session_state:
        st.warning("Load data first to use the AI assistant.")

    # Display chat history
    if st.session_state['chat_history']:
        st.markdown("<div style='margin-top:10px;max-height:320px;overflow-y:auto;'>",
                    unsafe_allow_html=True)
        for msg in st.session_state['chat_history'][-6:]:
            if msg['role'] == 'user':
                st.markdown(f"""
                <div style='background:#252840;border-radius:8px;
                            padding:8px 12px;margin-bottom:6px;
                            font-size:0.8rem;color:#e0e4ff;'>
                  <b style='color:#7c83ff;'>You:</b> {msg['content']}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background:#1a2e1a;border:0.5px solid #2d5a2d;
                            border-radius:8px;padding:8px 12px;
                            margin-bottom:6px;font-size:0.8rem;
                            color:#e0e4ff;line-height:1.6;'>
                  <b style='color:#00d4aa;'>AI:</b> {msg['content']}
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state['chat_history'] = []
            st.rerun()

# ── Upload handler ────────────────────────────────────────────────────────────
if bank_file and upi_file:
    try:
        bank_df = pd.read_csv(bank_file)
        upi_df  = pd.read_csv(upi_file)
        col_map = [
            ('amount_inr', ['amount_inr','amount','Amount','amt','AMOUNT']),
            ('txn_id',     ['txn_id','transaction_id','id','ref','TXN_ID','ID']),
            ('status',     ['status','Status','STATE','state']),
            ('type',       ['type','Type','TYPE','category','txn_type']),
            ('bank',       ['bank','Bank','BANK','bank_name']),
            ('merchant',   ['merchant','Merchant','MERCHANT','vendor','shop']),
            ('date',       ['date','Date','DATE','timestamp','time']),
        ]
        for target, options in col_map:
            for opt in options:
                if opt in bank_df.columns and opt != target:
                    bank_df.rename(columns={opt: target}, inplace=True); break
                if opt in upi_df.columns and opt != target:
                    upi_df.rename(columns={opt: target}, inplace=True); break
        for c in ['type','bank','merchant','status']:
            if c not in bank_df.columns: bank_df[c] = 'Unknown'
            if c not in upi_df.columns:  upi_df[c]  = 'Unknown'
        st.session_state['bank_df'] = bank_df
        st.session_state['upi_df']  = upi_df
        st.sidebar.success("✅ Files uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")

# ── Helper ────────────────────────────────────────────────────────────────────
def dark_fig(w=6, h=4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor('#1e2130')
    ax.set_facecolor('#1e2130')
    for sp in ax.spines.values(): sp.set_color('#3d4266')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#8b92b3')
    return fig, ax

# ── Main dashboard ────────────────────────────────────────────────────────────
if 'bank_df' in st.session_state:
    bank_df = st.session_state['bank_df']
    upi_df  = st.session_state['upi_df']
    result  = run_reconciliation(bank_df, upi_df)
    summary = get_summary(result)
    flagged = detect_anomalies(bank_df)

    total   = summary['total']
    matched = summary['matched']
    disc    = total - matched
    gap     = summary['total_amount_gap_inr']

    # ── KPI CARDS ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Reconciliation Summary</div>',
                unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    kpi_data = [
        (k1, "Total Transactions",  f"{total:,}",       "Dataset processed",                       True),
        (k2, "✅ Matched",           f"{matched:,}",     f"↑ {summary['match_rate']}% match rate",  True),
        (k3, "⚠️ Discrepancies",     f"{disc:,}",        f"↓ {round(100-summary['match_rate'],1)}% error rate", False),
        (k4, "💸 Amount Gap",        f"₹{gap:,.0f}",     "Total unreconciled (INR)",                False),
    ]
    for col, label, val, delta, good in kpi_data:
        d_class = "metric-delta-good" if good else "metric-delta-bad"
        col.markdown(f"""
        <div class="metric-card">
          <span class="metric-label">{label}</span>
          <span class="metric-value">{val}</span>
          <span class="{d_class}">{delta}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AUTO INSIGHTS ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🧠 Auto-Generated Insights</div>',
                unsafe_allow_html=True)

    bank_col     = 'bank_bank'     if 'bank_bank'     in result.columns else 'bank'
    type_col     = 'type_bank'     if 'type_bank'     in result.columns else 'type'
    merchant_col = 'merchant_bank' if 'merchant_bank' in result.columns else 'merchant'

    bank_rates    = result.groupby(bank_col)['is_discrepancy'].mean() * 100
    worst_bank    = bank_rates.idxmax()
    worst_bank_r  = bank_rates.max()
    best_bank     = bank_rates.idxmin()
    best_bank_r   = bank_rates.min()

    type_rates    = result.groupby(type_col)['is_discrepancy'].mean() * 100
    riskiest_type = type_rates.idxmax()
    riskiest_pct  = type_rates.max()

    top_merchant  = result[result['is_discrepancy']][merchant_col].value_counts()
    top_m_name    = top_merchant.index[0] if len(top_merchant) else "N/A"
    top_m_count   = int(top_merchant.iloc[0]) if len(top_merchant) else 0

    suspicious_ct = int(flagged['is_suspicious'].sum())
    susp_df       = flagged[flagged['is_suspicious']]
    high_risk_amt = susp_df['amount_inr'].mean() if len(susp_df) else 0

    match_rate = summary['match_rate']
    health     = ("🟢 Healthy"       if match_rate >= 92 else
                  "🟡 Moderate Risk" if match_rate >= 85 else
                  "🔴 High Risk")

    insights = [
        (f"🏦 <b>{worst_bank} Bank</b> has the highest discrepancy rate at "
         f"<span class='risk-high'>{worst_bank_r:.1f}%</span> — flag for priority investigation."),
        (f"✅ <b>{best_bank} Bank</b> is the most reliable with only "
         f"<span class='risk-low'>{best_bank_r:.1f}%</span> discrepancy rate."),
        (f"💳 <b>{riskiest_type}</b> transactions have the highest error rate at "
         f"<span class='risk-medium'>{riskiest_pct:.1f}%</span> — review processing pipeline."),
        (f"🛒 <b>{top_m_name}</b> appears most in discrepancies "
         f"(<span class='risk-high'>{top_m_count} cases</span>) — check settlement agreements."),
        (f"🚨 ML model flagged <b>{suspicious_ct} suspicious transactions</b> "
         f"with average amount <span class='risk-high'>₹{high_risk_amt:,.0f}</span>."),
        (f"📊 Overall portfolio health: <b>{health}</b> "
         f"({match_rate}% match rate across {total:,} transactions)"),
    ]

    col_a, col_b = st.columns(2)
    for i, ins in enumerate(insights):
        target = col_a if i % 2 == 0 else col_b
        target.markdown(
            f'<div class="insight-box"><span class="insight-text">{ins}</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── DISCREPANCY CHARTS ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📈 Discrepancy Analysis</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        disc_data = result[result['is_discrepancy']]['match_status'].value_counts()
        fig, ax = dark_fig()
        colors = ['#ff6b6b','#ffa64d','#ffd93d','#6bcb77','#4d96ff']
        bars = ax.barh(disc_data.index, disc_data.values,
                       color=colors[:len(disc_data)], height=0.5)
        for bar, val in zip(bars, disc_data.values):
            ax.text(bar.get_width()+0.3, bar.get_y()+bar.get_height()/2,
                    str(val), va='center', color='white',
                    fontsize=10, fontweight='bold')
        ax.set_xlim(0, disc_data.values.max()*1.3)
        ax.set_title('Discrepancy Type Breakdown', color='white', fontsize=12, pad=10)
        ax.set_xlabel('Count', color='#8b92b3')
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c2:
        if bank_col in result.columns:
            bank_rate = (result.groupby(bank_col)['is_discrepancy']
                         .mean()*100).round(1).sort_values(ascending=False)
            fig, ax = dark_fig()
            avg = bank_rate.mean()
            bar_colors = ['#ff6b6b' if v >= avg else '#7c83ff'
                          for v in bank_rate.values]
            bars = ax.bar(bank_rate.index, bank_rate.values,
                          color=bar_colors, width=0.5, zorder=3)
            for bar, val in zip(bars, bank_rate.values):
                ax.text(bar.get_x()+bar.get_width()/2,
                        bar.get_height()+0.2, f'{val}%',
                        ha='center', color='white',
                        fontsize=9, fontweight='bold')
            ax.axhline(y=avg, color='#ffd93d', linestyle='--',
                       linewidth=1.2, alpha=0.8, zorder=2)
            ax.text(len(bank_rate)-0.5, avg+0.3,
                    f'Avg {avg:.1f}%', color='#ffd93d', fontsize=8)
            ax.set_ylabel('Discrepancy Rate (%)', color='#8b92b3')
            ax.set_title('Bank-wise Discrepancy Rate', color='white', fontsize=12, pad=10)
            plt.tight_layout(); st.pyplot(fig); plt.close()

    # ── MONTHLY TREND ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📅 Monthly Transaction Trend</div>',
                unsafe_allow_html=True)
    try:
        date_col = 'date_bank' if 'date_bank' in result.columns else 'date'
        result[date_col] = pd.to_datetime(result[date_col], errors='coerce')
        result['month']  = result[date_col].dt.to_period('M')

        monthly = result.groupby('month').agg(
            total=('txn_id', 'count'),
            discrepancies=('is_discrepancy', 'sum')
        ).reset_index()
        monthly['month_str']  = monthly['month'].astype(str)
        monthly['match_rate'] = (
            (monthly['total'] - monthly['discrepancies'])
            / monthly['total'] * 100
        ).round(1)

        fig, ax1 = plt.subplots(figsize=(12, 4))
        fig.patch.set_facecolor('#1e2130')
        ax1.set_facecolor('#1e2130')
        x = range(len(monthly))

        ax1.bar(x, monthly['total'], color='#7c83ff', alpha=0.55,
                label='Total Transactions', width=0.6, zorder=2)
        ax1.bar(x, monthly['discrepancies'], color='#ff6b6b', alpha=0.9,
                label='Discrepancies', width=0.6, zorder=3)

        ax2 = ax1.twinx()
        ax2.set_facecolor('#1e2130')
        ax2.plot(x, monthly['match_rate'], color='#00d4aa',
                 linewidth=2.5, marker='o', markersize=6,
                 label='Match Rate %', zorder=5)
        ax2.fill_between(x, monthly['match_rate'],
                         alpha=0.08, color='#00d4aa')
        ax2.set_ylabel('Match Rate (%)', color='#00d4aa', fontsize=10)
        ax2.tick_params(colors='#00d4aa')
        ax2.set_ylim(60, 105)

        for i, rate in enumerate(monthly['match_rate']):
            ax2.annotate(f'{rate}%', xy=(i, rate), xytext=(0, 9),
                         textcoords='offset points',
                         color='#00d4aa', fontsize=8,
                         ha='center', fontweight='bold')

        ax1.set_xticks(x)
        ax1.set_xticklabels(monthly['month_str'],
                            rotation=30, ha='right', color='#8b92b3')
        ax1.set_ylabel('Transaction Count', color='#8b92b3', fontsize=10)
        ax1.set_title('Monthly Volume: Total vs Discrepancies + Match Rate Trend',
                      color='white', fontsize=12, pad=12)
        ax1.tick_params(colors='#8b92b3')
        for sp in ax1.spines.values(): sp.set_color('#3d4266')
        ax1.spines['top'].set_visible(False)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1+lines2, labels1+labels2,
                   facecolor='#252840', labelcolor='white',
                   fontsize=9, loc='upper left')
        plt.tight_layout(); st.pyplot(fig); plt.close()

    except Exception as e:
        st.warning(f"Trend chart issue: {e}")

    # ── PIE + MERCHANT ────────────────────────────────────────────────────────
    c3, c4 = st.columns(2)

    with c3:
        if type_col in result.columns:
            type_dist = result[type_col].value_counts()
            fig, ax = dark_fig()
            pie_colors = ['#7c83ff','#00d4aa','#ffd93d','#ff6b6b','#ffa64d']
            wedges, texts, autotexts = ax.pie(
                type_dist.values, labels=type_dist.index,
                autopct='%1.1f%%',
                colors=pie_colors[:len(type_dist)],
                startangle=90,
                wedgeprops={'edgecolor':'#1e2130','linewidth':2}
            )
            for t in texts:
                t.set_color('#e0e4ff'); t.set_fontsize(9)
            for a in autotexts:
                a.set_color('white'); a.set_fontsize(8); a.set_fontweight('bold')
            ax.set_title('Transaction Type Mix', color='white', fontsize=12, pad=10)
            plt.tight_layout(); st.pyplot(fig); plt.close()

    with c4:
        if merchant_col in result.columns:
            disc_m = (result[result['is_discrepancy']]
                      [merchant_col].value_counts().head(8))
            fig, ax = dark_fig()
            grad = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(disc_m)))
            bars = ax.barh(disc_m.index, disc_m.values,
                           color=grad, height=0.5)
            for bar, val in zip(bars, disc_m.values):
                ax.text(bar.get_width()+0.05,
                        bar.get_y()+bar.get_height()/2,
                        str(val), va='center', color='white',
                        fontsize=9, fontweight='bold')
            ax.set_xlim(0, disc_m.values.max()*1.3)
            ax.set_title('Top Merchants with Discrepancies',
                         color='white', fontsize=12, pad=10)
            ax.set_xlabel('Discrepancy Count', color='#8b92b3')
            plt.tight_layout(); st.pyplot(fig); plt.close()

    # ── AMOUNT DISTRIBUTION ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">💸 Amount Analysis</div>',
                unsafe_allow_html=True)
    fig, ax = dark_fig(12, 3.5)
    m_amt = result[~result['is_discrepancy']]['amount_inr_bank'].dropna()
    d_amt = result[result['is_discrepancy']]['amount_inr_bank'].dropna()
    ax.hist(m_amt, bins=40, color='#00d4aa', alpha=0.7,
            label=f'Matched ({len(m_amt)})', edgecolor='none')
    ax.hist(d_amt, bins=40, color='#ff6b6b', alpha=0.9,
            label=f'Discrepancy ({len(d_amt)})', edgecolor='none')
    ax.set_xlabel('Transaction Amount (₹)', color='#8b92b3')
    ax.set_ylabel('Frequency', color='#8b92b3')
    ax.set_title('Amount Distribution: Matched vs Discrepancy',
                 color='white', fontsize=12, pad=10)
    ax.legend(facecolor='#252840', labelcolor='white', fontsize=9)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    # ── FRAUD DETECTION ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🚨 ML Fraud Detection (Isolation Forest)</div>',
                unsafe_allow_html=True)

    suspicious = flagged[flagged['is_suspicious']].copy()
    fraud_pct  = round(len(suspicious)/len(bank_df)*100, 1)

    f1, f2, f3 = st.columns(3)
    for col, label, val, delta, good in [
        (f1, "🔍 Transactions Scanned", f"{len(bank_df):,}",              "Full dataset",             True),
        (f2, "🚨 Suspicious Flagged",   f"{len(suspicious)}",             f"{fraud_pct}% of total",   False),
        (f3, "✅ Clean Transactions",    f"{len(bank_df)-len(suspicious):,}", f"{100-fraud_pct}% clean", True),
    ]:
        d_class = "metric-delta-good" if good else "metric-delta-bad"
        v_color = "#ff6b6b" if not good else "#fff"
        col.markdown(f"""
        <div class="metric-card">
          <span class="metric-label">{label}</span>
          <span class="metric-value" style="color:{v_color};">{val}</span>
          <span class="{d_class}">{delta}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if len(suspicious):
        def color_risk(val):
            if isinstance(val, (int, float)):
                if val >= 70:   return 'background-color:#3d1515;color:#ff4444'
                elif val >= 40: return 'background-color:#2d2010;color:#ffa64d'
                else:           return 'background-color:#0d2d1a;color:#00d4aa'
            return ''

        display_cols = ['txn_id','date','amount_inr',
                        'type','bank','merchant','status','risk_score']
        avail = [c for c in display_cols if c in suspicious.columns]
        styled = suspicious[avail].style.map(color_risk, subset=['risk_score'])
        st.dataframe(styled, use_container_width=True, height=300)
    else:
        st.success("✅ No suspicious transactions detected.")

    # ── DOWNLOAD + RAW ────────────────────────────────────────────────────────
    st.divider()
    d1, d2 = st.columns(2)
    with d1:
        st.markdown('<div class="section-header">📥 Download Report</div>',
                    unsafe_allow_html=True)
        st.download_button(
            "⬇️ Download Reconciliation Report (CSV)",
            result.to_csv(index=False).encode('utf-8'),
            "reconciliation_report.csv", "text/csv",
            use_container_width=True
        )
    with d2:
        st.markdown('<div class="section-header">🔍 Raw Data</div>',
                    unsafe_allow_html=True)
        with st.expander("View full reconciliation table"):
            st.dataframe(result, use_container_width=True)

# ── Landing page ──────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style='text-align:center;padding:3rem 0 2rem 0;'>
      <div style='font-size:3.5rem;'>💰</div>
      <h2 style='color:#e0e4ff;margin:8px 0 6px 0;'>Ready to reconcile</h2>
      <p style='color:#8b92b3;max-width:480px;margin:0 auto;
                font-size:0.92rem;line-height:1.8;'>
        Upload your bank ledger and UPI statement in the sidebar,<br>
        or click <b style='color:#7c83ff;'>Load Sample Indian Data</b>
        to explore the full dashboard instantly.
      </p>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    features = [
        (c1, "✅", "Smart Matching",     "Record-by-record reconciliation on txn_id"),
        (c2, "🧠", "Auto Insights",      "AI identifies worst bank & riskiest merchant"),
        (c3, "🚨", "ML Fraud Detection", "Isolation Forest with 0–100 risk scoring"),
        (c4, "📅", "Trend Analysis",     "Monthly volume & match rate over time"),
    ]
    for col, icon, title, desc in features:
        col.markdown(f"""
        <div class="metric-card" style='padding:18px 12px;'>
          <div style='font-size:1.9rem;margin-bottom:8px;'>{icon}</div>
          <div style='color:#e0e4ff;font-weight:600;
                      font-size:0.9rem;margin-bottom:5px;'>{title}</div>
          <div style='color:#8b92b3;font-size:0.78rem;
                      line-height:1.5;'>{desc}</div>
        </div>""", unsafe_allow_html=True)
