import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sys, os

sys.path.append(os.path.dirname(__file__))
from src.reconcile import run_reconciliation, get_summary
from src.fraud_detector import detect_anomalies

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UPI Reconciliation Dashboard",
    page_icon="💰", layout="wide"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg,#1e2130,#252840);
    border:1px solid #3d4266; border-radius:12px;
    padding:20px; text-align:center; height:110px;
}
.metric-value { font-size:2rem; font-weight:700; color:#fff; }
.metric-label { font-size:0.82rem; color:#8b92b3; margin-bottom:4px; }
.metric-delta-good { font-size:0.78rem; color:#00d4aa; }
.metric-delta-bad  { font-size:0.78rem; color:#ff6b6b; }
.section-header {
    font-size:1.1rem; font-weight:600; color:#e0e4ff;
    margin:1.5rem 0 0.8rem 0;
    border-left:4px solid #7c83ff; padding-left:12px;
}
.insight-box {
    background:#1a1d2e; border:1px solid #3d4266;
    border-radius:10px; padding:14px 18px; margin-bottom:8px;
}
.insight-icon { font-size:1.1rem; margin-right:8px; }
.insight-text { color:#e0e4ff; font-size:0.9rem; line-height:1.6; }
.risk-high   { color:#ff4444; font-weight:700; }
.risk-medium { color:#ffa64d; font-weight:700; }
.risk-low    { color:#00d4aa; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding:1.5rem 0 0.5rem 0;'>
  <h1 style='color:#fff;font-size:2.2rem;margin:0;'>
    💰 UPI Transaction Reconciliation
  </h1>
  <p style='color:#7c83ff;font-size:1rem;margin:4px 0 0 0;'>
    ML-powered Fraud Detection & Discrepancy Analysis · India Fintech
  </p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Upload Transaction Files")
    st.markdown("<p style='font-size:0.8rem;color:#8b92b3;'>Upload your own CSVs or use sample data</p>",
                unsafe_allow_html=True)
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
            st.error("❌ Run data generator first")

    st.divider()
    st.markdown("""
    <div style='font-size:0.78rem;color:#8b92b3;line-height:1.6'>
    <b style='color:#e0e4ff'>Built by</b><br>
    [Your Name] · CSE 3rd Year<br><br>
    <b style='color:#e0e4ff'>Tech Stack</b><br>
    Python · Pandas · Scikit-learn<br>
    Isolation Forest · Streamlit<br>
    Matplotlib · Seaborn
    </div>""", unsafe_allow_html=True)

# ── Upload handler ────────────────────────────────────────────────────────────
if bank_file and upi_file:
    try:
        bank_df = pd.read_csv(bank_file)
        upi_df  = pd.read_csv(upi_file)
        for col, targets in [
            ('amount_inr', ['amount_inr','amount','Amount','amt']),
            ('txn_id',     ['txn_id','transaction_id','id','ref']),
            ('status',     ['status','Status','state']),
            ('type',       ['type','Type','category']),
            ('bank',       ['bank','Bank','bank_name']),
            ('merchant',   ['merchant','Merchant','vendor']),
            ('date',       ['date','Date','timestamp']),
        ]:
            for t in targets:
                if t in bank_df.columns and t != col:
                    bank_df.rename(columns={t: col}, inplace=True)
                if t in upi_df.columns and t != col:
                    upi_df.rename(columns={t: col}, inplace=True)
        for c in ['type','bank','merchant','status']:
            if c not in bank_df.columns: bank_df[c] = 'Unknown'
            if c not in upi_df.columns:  upi_df[c]  = 'Unknown'
        st.session_state['bank_df'] = bank_df
        st.session_state['upi_df']  = upi_df
        st.sidebar.success("✅ Files uploaded!")
    except Exception as e:
        st.sidebar.error(f"❌ {e}")

# ── Dashboard ─────────────────────────────────────────────────────────────────
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

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Reconciliation Summary</div>',
                unsafe_allow_html=True)
    k1,k2,k3,k4 = st.columns(4)
    for col, label, val, delta, good in [
        (k1, "Total Transactions",  f"{total:,}",    "Dataset processed",            True),
        (k2, "✅ Matched",           f"{matched:,}",  f"↑ {summary['match_rate']}% match rate", True),
        (k3, "⚠️ Discrepancies",     f"{disc:,}",     f"↓ {round(100-summary['match_rate'],1)}% error rate", False),
        (k4, "💸 Amount Gap (INR)",  f"₹{gap:,.0f}",  "Total unreconciled value",     False),
    ]:
        d_class = "metric-delta-good" if good else "metric-delta-bad"
        col.markdown(f"""<div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{val}</div>
            <div class="{d_class}">{delta}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AUTO INSIGHTS ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🧠 Auto-Generated Insights</div>',
                unsafe_allow_html=True)

    bank_col     = 'bank_bank'     if 'bank_bank'     in result.columns else 'bank'
    type_col     = 'type_bank'     if 'type_bank'     in result.columns else 'type'
    merchant_col = 'merchant_bank' if 'merchant_bank' in result.columns else 'merchant'

    # Compute insights
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
    top_m_count   = top_merchant.iloc[0]  if len(top_merchant) else 0

    suspicious_ct = flagged['is_suspicious'].sum()
    high_risk_amt = flagged[flagged['is_suspicious']]['amount_inr'].mean()

    match_rate    = summary['match_rate']
    health        = "🟢 Healthy" if match_rate >= 92 else \
                    "🟡 Moderate Risk" if match_rate >= 85 else "🔴 High Risk"

    insights = [
        (f"🏦 <b>{worst_bank} Bank</b> has the highest discrepancy rate at "
         f"<span class='risk-high'>{worst_bank_r:.1f}%</span> — "
         f"flag for priority investigation."),
        (f"✅ <b>{best_bank} Bank</b> is the most reliable with only "
         f"<span class='risk-low'>{best_bank_r:.1f}%</span> discrepancy rate."),
        (f"💳 <b>{riskiest_type}</b> transactions have the highest error rate at "
         f"<span class='risk-medium'>{riskiest_pct:.1f}%</span> — "
         f"review processing pipeline for this type."),
        (f"🛒 <b>{top_m_name}</b> appears most in discrepancies "
         f"(<span class='risk-high'>{top_m_count} cases</span>) — "
         f"check merchant settlement agreements."),
        (f"🚨 ML model flagged <b>{suspicious_ct} suspicious transactions</b> "
         f"with average amount ₹<span class='risk-high'>{high_risk_amt:,.0f}</span> "
         f"— elevated compared to dataset average."),
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

    # ── CHARTS ROW 1 ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📈 Discrepancy Analysis</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    def dark_fig(w=6, h=4):
        fig, ax = plt.subplots(figsize=(w, h))
        fig.patch.set_facecolor('#1e2130')
        ax.set_facecolor('#1e2130')
        for sp in ax.spines.values(): sp.set_color('#3d4266')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(colors='#8b92b3')
        return fig, ax

    with c1:
        disc_data = result[result['is_discrepancy']]['match_status'].value_counts()
        fig, ax = dark_fig()
        colors = ['#ff6b6b','#ffa64d','#ffd93d','#6bcb77','#4d96ff']
        bars = ax.barh(disc_data.index, disc_data.values,
                       color=colors[:len(disc_data)], height=0.5)
        for bar, val in zip(bars, disc_data.values):
            ax.text(bar.get_width()+0.3, bar.get_y()+bar.get_height()/2,
                    str(val), va='center', color='white', fontsize=10, fontweight='bold')
        ax.set_xlim(0, disc_data.values.max()*1.25)
        ax.set_title('Discrepancy Type Breakdown', color='white', fontsize=12, pad=10)
        ax.set_xlabel('Count', color='#8b92b3')
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c2:
        if bank_col in result.columns:
            bank_rate = (result.groupby(bank_col)['is_discrepancy']
                         .mean()*100).round(1).sort_values(ascending=False)
            fig, ax = dark_fig()
            bar_colors = ['#ff6b6b' if v >= bank_rate.mean()
                          else '#7c83ff' for v in bank_rate.values]
            bars = ax.bar(bank_rate.index, bank_rate.values,
                          color=bar_colors, width=0.5)
            for bar, val in zip(bars, bank_rate.values):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
                        f'{val}%', ha='center', color='white',
                        fontsize=9, fontweight='bold')
            ax.axhline(y=bank_rate.mean(), color='#ffd93d',
                       linestyle='--', linewidth=1, alpha=0.8)
            ax.text(len(bank_rate)-0.5, bank_rate.mean()+0.3,
                    f'Avg {bank_rate.mean():.1f}%', color='#ffd93d', fontsize=8)
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
        monthly['match_rate'] = ((monthly['total'] - monthly['discrepancies'])
                                  / monthly['total'] * 100).round(1)

        fig, ax1 = plt.subplots(figsize=(12, 4))
        fig.patch.set_facecolor('#1e2130')
        ax1.set_facecolor('#1e2130')

        x = range(len(monthly))
        bars = ax1.bar(x, monthly['total'], color='#7c83ff',
                       alpha=0.6, label='Total Transactions', width=0.6)
        ax1.bar(x, monthly['discrepancies'], color='#ff6b6b',
                alpha=0.9, label='Discrepancies', width=0.6)

        ax2 = ax1.twinx()
        ax2.set_facecolor('#1e2130')
        ax2.plot(x, monthly['match_rate'], color='#00d4aa',
                 linewidth=2.5, marker='o', markersize=5,
                 label='Match Rate %', zorder=5)
        ax2.set_ylabel('Match Rate (%)', color='#00d4aa', fontsize=10)
        ax2.tick_params(colors='#00d4aa')
        ax2.set_ylim(60, 105)

        for i, (rate, tot) in enumerate(
                zip(monthly['match_rate'], monthly['total'])):
            ax2.annotate(f'{rate}%',
                         xy=(i, rate), xytext=(0, 8),
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

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    except Exception as e:
        st.warning(f"Trend chart needs date column: {e}")

    # ── CHARTS ROW 2 ──────────────────────────────────────────────────────────
    c3, c4 = st.columns(2)
    with c3:
        if type_col in result.columns:
            type_dist = result[type_col].value_counts()
            fig, ax = dark_fig()
            pie_colors = ['#7c83ff','#00d4aa','#ffd93d','#ff6b6b','#ffa64d']
            wedges, texts, autotexts = ax.pie(
                type_dist.values, labels=type_dist.index,
                autopct='%1.1f%%', colors=pie_colors[:len(type_dist)],
                startangle=90,
                wedgeprops={'edgecolor':'#1e2130','linewidth':2}
            )
            for t in texts:      t.set_color('#e0e4ff'); t.set_fontsize(9)
            for a in autotexts:  a.set_color('white'); a.set_fontsize(8); a.set_fontweight('bold')
            ax.set_title('Transaction Type Mix', color='white', fontsize=12, pad=10)
            plt.tight_layout(); st.pyplot(fig); plt.close()

    with c4:
        if merchant_col in result.columns:
            disc_m = (result[result['is_discrepancy']]
                      [merchant_col].value_counts().head(8))
            fig, ax = dark_fig()
            grad = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(disc_m)))
            bars = ax.barh(disc_m.index, disc_m.values, color=grad, height=0.5)
            for bar, val in zip(bars, disc_m.values):
                ax.text(bar.get_width()+0.05, bar.get_y()+bar.get_height()/2,
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
            label=f'Matched ({len(m_amt)})')
    ax.hist(d_amt, bins=40, color='#ff6b6b', alpha=0.9,
            label=f'Discrepancy ({len(d_amt)})')
    ax.set_xlabel('Transaction Amount (₹)', color='#8b92b3')
    ax.set_ylabel('Frequency', color='#8b92b3')
    ax.set_title('Amount Distribution: Matched vs Discrepancy',
                 color='white', fontsize=12, pad=10)
    ax.legend(facecolor='#252840', labelcolor='white', fontsize=9)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    # ── FRAUD DETECTION ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🚨 ML Fraud Detection (Isolation Forest)</div>',
                unsafe_allow_html=True)

    suspicious  = flagged[flagged['is_suspicious']].copy()
    fraud_pct   = round(len(suspicious)/len(bank_df)*100, 1)

    f1,f2,f3 = st.columns(3)
    for col, label, val, delta, good in [
        (f1, "🔍 Transactions Scanned", f"{len(bank_df):,}", "Full dataset", True),
        (f2, "🚨 Suspicious Flagged",   f"{len(suspicious)}", f"{fraud_pct}% of total", False),
        (f3, "✅ Clean Transactions",    f"{len(bank_df)-len(suspicious):,}", f"{100-fraud_pct}% flagged clean", True),
    ]:
        d_class = "metric-delta-good" if good else "metric-delta-bad"
        col.markdown(f"""<div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{'#ff6b6b' if not good else '#fff'}">{val}</div>
            <div class="{d_class}">{delta}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if len(suspicious):
        # Risk score color
        def color_risk(val):
            if isinstance(val, float):
                if val >= 70:   return 'background-color:#3d1515;color:#ff4444'
                elif val >= 40: return 'background-color:#2d2010;color:#ffa64d'
                else:           return 'background-color:#0d2d1a;color:#00d4aa'
            return ''

        display_cols = ['txn_id','date','amount_inr',
                        'type','bank','merchant','status','risk_score']
        avail = [c for c in display_cols if c in suspicious.columns]
        styled = suspicious[avail].style.map(color_risk, subset=['risk_score'])
        st.dataframe(styled, use_container_width=True, height=300)

    # ── DOWNLOAD ──────────────────────────────────────────────────────────────
    st.divider()
    d1, d2 = st.columns(2)
    with d1:
        st.markdown('<div class="section-header">📥 Download Report</div>',
                    unsafe_allow_html=True)
        st.download_button("⬇️ Download Reconciliation Report (CSV)",
                           result.to_csv(index=False).encode('utf-8'),
                           "reconciliation_report.csv", "text/csv",
                           use_container_width=True)
    with d2:
        st.markdown('<div class="section-header">🔍 Raw Data</div>',
                    unsafe_allow_html=True)
        with st.expander("View full reconciliation table"):
            st.dataframe(result, use_container_width=True)

else:
    st.markdown("""
    <div style='text-align:center;padding:3rem 0;'>
      <h2 style='color:#7c83ff;font-size:3rem;margin:0;'>💰</h2>
      <h3 style='color:#e0e4ff;'>Ready to reconcile</h3>
      <p style='color:#8b92b3;max-width:500px;margin:0 auto;line-height:1.7;'>
        Upload your bank ledger and UPI statement CSVs in the sidebar,<br>
        or click <b style='color:#7c83ff;'>Load Sample Indian Data</b> to explore.
      </p>
    </div>""", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col,icon,title,desc in [
        (c1,"✅","Smart Matching","Record-by-record reconciliation"),
        (c2,"🧠","Auto Insights","AI-generated risk analysis"),
        (c3,"🚨","ML Fraud Detection","Isolation Forest scoring"),
        (c4,"📅","Trend Analysis","Monthly volume & match rate"),
    ]:
        col.markdown(f"""<div class="metric-card" style='padding:16px;height:auto;'>
          <div style='font-size:1.8rem;'>{icon}</div>
          <div style='color:#e0e4ff;font-weight:600;margin:6px 0 4px;'>{title}</div>
          <div style='color:#8b92b3;font-size:0.82rem;'>{desc}</div>
        </div>""", unsafe_allow_html=True)