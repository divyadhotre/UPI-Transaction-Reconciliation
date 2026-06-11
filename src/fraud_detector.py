import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    df_enc = df.copy()

    le = LabelEncoder()
    df_enc['type_enc']     = le.fit_transform(df['type'].astype(str))
    df_enc['bank_enc']     = le.fit_transform(df['bank'].astype(str))
    df_enc['merchant_enc'] = le.fit_transform(df['merchant'].astype(str))

    features = ['amount_inr', 'type_enc', 'bank_enc', 'merchant_enc']

    model = IsolationForest(contamination=0.05, random_state=42)
    raw_scores = model.fit_predict(df_enc[features])
    decision_scores = model.decision_function(df_enc[features])

    # Convert to 0-100 risk score (higher = more suspicious)
    scaler = MinMaxScaler(feature_range=(0, 100))
    risk_scores = scaler.fit_transform(
        (-decision_scores).reshape(-1, 1)
    ).flatten()

    df_enc['anomaly_raw']  = raw_scores
    df_enc['is_suspicious'] = df_enc['anomaly_raw'] == -1
    df_enc['risk_score']   = np.round(risk_scores, 1)

    return df_enc