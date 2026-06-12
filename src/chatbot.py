import streamlit as st
import pandas as pd
from google import genai

def setup_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    # Modern SDK initialization pattern
    return genai.Client(api_key=api_key)

def build_data_context(result_df: pd.DataFrame, summary: dict, flagged_df: pd.DataFrame) -> str:
    bank_col     = 'bank_bank'     if 'bank_bank'     in result_df.columns else 'bank'
    type_col     = 'type_bank'     if 'type_bank'     in result_df.columns else 'type'
    merchant_col = 'merchant_bank' if 'merchant_bank' in result_df.columns else 'merchant'
    
    bank_rates = (result_df.groupby(bank_col)['is_discrepancy'].mean() * 100).round(1).to_dict()
    type_rates = (result_df.groupby(type_col)['is_discrepancy'].mean() * 100).round(1).to_dict()
    top_merchants = (result_df[result_df['is_discrepancy']][merchant_col].value_counts().head(5).to_dict())
    
    suspicious = flagged_df[flagged_df['is_suspicious']]
    
    # Safely evaluate bounds outside the string literal block to prevent f-string parser bugs
    highest_risk = f"{suspicious['risk_score'].max():.1f}/100 risk score" if len(suspicious) > 0 else 'None'
    avg_suspicious = f"₹{suspicious['amount_inr'].mean():,.2f}" if len(suspicious) > 0 else 'N/A'
    
    context = f"""You are an expert financial data analyst assistant for a UPI Transaction Reconciliation system.
You have access to the following real-time data from the dashboard:

RECONCILIATION SUMMARY:
- Total Transactions: {summary['total']:,}
- Matched: {summary['matched']:,} ({summary['match_rate']}% match rate)
- Discrepancies: {summary['total'] - summary['matched']:,}
- Total Amount Gap: ₹{summary['total_amount_gap_inr']:,.2f}

BANK-WISE DISCREPANCY RATES:
{chr(10).join([f'- {bank}: {rate}%' for bank, rate in bank_rates.items()])}

TRANSACTION TYPE ERROR RATES:
{chr(10).join([f'- {t}: {rate}%' for t, rate in type_rates.items()])}

TOP MERCHANTS WITH DISCREPANCIES:
{chr(10).join([f'- {m}: {c} cases' for m, c in top_merchants.items()])}

ML FRAUD DETECTION:
- Suspicious transactions flagged: {len(suspicious)}
- Highest risk transaction: {highest_risk}
- Average suspicious amount: {avg_suspicious}

Answer questions about this data clearly and concisely. Use ₹ for rupees. Be specific with numbers.
If asked something outside this data, say you can only answer about the current transaction dataset.
Keep answers under 100 words unless a detailed breakdown is asked."""
    return context

def get_ai_response(client, user_question: str, data_context: str, chat_history: list) -> str:
    try:
        history_text = ""
        for msg in chat_history[-4:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
            
        full_prompt = f"""{data_context}

CONVERSATION HISTORY:
{history_text}
CURRENT QUESTION: {user_question}

Answer the question based on the data provided above."""
        
        # Modern client inference block utilizing the powerful, stable flash model layout
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        return f"Sorry, I couldn't process that. Error: {str(e)}"