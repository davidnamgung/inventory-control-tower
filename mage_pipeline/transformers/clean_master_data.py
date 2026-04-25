import pandas as pd
import numpy as np

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def transform(df, *args, **kwargs):
    """
    Executes the core cleaning and anomaly detection logic.
    """
    print(f"Initial record count: {len(df)}")

    # =========================================================
    # 1. STANDARDIZE TEXT (Fixing the messy categories)
    # =========================================================
    # We convert everything to lowercase first, map the weird variations 
    # to their proper names, and then capitalize them properly.
    category_mapping = {
        'eng': 'Engine', 'motor': 'Engine', 'engine': 'Engine',
        'trans': 'Transmission', 'gearbox': 'Transmission', 'transmission': 'Transmission',
        'electric': 'Electrical', 'elec': 'Electrical', 'electrical': 'Electrical'
    }
    
    df['model_family_group'] = df['model_family_group'].str.lower().replace(category_mapping)
    df['model_family_group'] = df['model_family_group'].str.title()

    # =========================================================
    # 2. IMPUTE MISSING DATA (Handling NULL ELM Codes)
    # =========================================================
    # We don't just delete missing data (that drops valuable inventory value).
    # We flag it, and fill the missing space with a searchable keyword.
    df['is_missing_elm'] = df['elm_code'].isna()
    df['elm_code'] = df['elm_code'].fillna('REQUIRES-MANUAL-AUDIT')

    # =========================================================
    # 3. ANOMALY DETECTION (Catching extreme pricing)
    # =========================================================
    # Using the IQR (Interquartile Range) algorithm to mathematically 
    # define what an "outlier" is, rather than guessing a number.
    Q1 = df['base_price'].quantile(0.25)
    Q3 = df['base_price'].quantile(0.75)
    IQR = Q3 - Q1
    upper_bound = Q3 + 1.5 * IQR

    # Create a boolean flag for massive price spikes
    df['is_price_anomaly'] = df['base_price'] > upper_bound

    # =========================================================
    # 4. MASTER DATA QUALITY FLAG
    # =========================================================
    # Create a single column for the Streamlit BI Dashboard to filter by
    df['data_health'] = np.where(
        df['is_missing_elm'] | df['is_price_anomaly'], 
        'Needs Review', 
        'Clean'
    )

    return df

@test
def test_output(output, *args) -> None:
    """
    Quality Assurance checks before allowing data to move forward.
    """
    assert output is not None, 'The output is undefined'
    assert 'data_health' in output.columns, 'Master flag was not created'
    assert output['elm_code'].isna().sum() == 0, 'There are still NULL values in ELM codes'