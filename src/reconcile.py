import pandas as pd
import numpy as np

def run_reconciliation(bank_df: pd.DataFrame, upi_df: pd.DataFrame) -> pd.DataFrame:
    """
    Matches bank ledger vs UPI statement on txn_id.
    Returns a merged dataframe with match status and discrepancy type.
    """
    merged = pd.merge(
        bank_df, upi_df,
        on='txn_id',
        suffixes=('_bank', '_upi'),
        how='outer',
        indicator=True
    )

    # Amount difference
    merged['amount_diff'] = (
        merged['amount_inr_bank'] - merged['amount_inr_upi']
    ).abs().fillna(0)

    # Match status
    def get_match_status(row):
        if row['_merge'] == 'left_only':
            return 'MISSING_IN_UPI'
        elif row['_merge'] == 'right_only':
            return 'MISSING_IN_BANK'
        elif row['amount_diff'] > 1.0:
            return 'AMOUNT_MISMATCH'
        elif row['status_bank'] != row['status_upi']:
            return 'STATUS_CONFLICT'
        else:
            return 'MATCHED'

    merged['match_status'] = merged.apply(get_match_status, axis=1)
    merged['is_discrepancy'] = merged['match_status'] != 'MATCHED'

    return merged


def get_summary(reconciled: pd.DataFrame) -> dict:
    """Returns key metrics as a dictionary."""
    total = len(reconciled)
    matched = (reconciled['match_status'] == 'MATCHED').sum()
    discrepancies = reconciled['match_status'].value_counts().to_dict()
    amount_gap = reconciled['amount_diff'].sum()

    return {
        'total': total,
        'matched': int(matched),
        'match_rate': round(matched / total * 100, 1),
        'discrepancies': discrepancies,
        'total_amount_gap_inr': round(amount_gap, 2)
    }