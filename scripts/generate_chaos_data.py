import pandas as pd
import numpy as np
from faker import Faker
import random
import os

# Initialize Faker for realistic fake data
fake = Faker()
Faker.seed(42)  # Seeds ensure we get the same "randomness" every time
np.random.seed(42)
random.seed(42)

NUM_RECORDS = 100000

print(f"Generating {NUM_RECORDS} messy supply chain records. Please wait...")

# 1. Base Clean Categories
clean_families = ['Engine', 'Transmission', 'Chassis', 'Electrical', 'Hydraulics']

# 2. Generate the Base Data
data = {
    'part_id': [f"PRT-{str(i).zfill(6)}" for i in range(1, NUM_RECORDS + 1)],
    'part_name': [fake.word().capitalize() + " " + random.choice(['Valve', 'Bolt', 'Sensor', 'Pump', 'Belt']) for _ in range(NUM_RECORDS)],
    'elm_code': [f"ELM-{random.randint(1000, 9999)}" for _ in range(NUM_RECORDS)],
    'model_family_group': [random.choice(clean_families) for _ in range(NUM_RECORDS)],
    'base_price': np.round(np.random.uniform(10.0, 500.0, NUM_RECORDS), 2),
    'stock_quantity': np.random.randint(0, 1000, NUM_RECORDS)
}

df = pd.DataFrame(data)

# ==========================================
# INJECTING CHAOS (The Interview Talking Points)
# ==========================================

print("Injecting chaos into the dataset...")

# Chaos 1: Missing ELM Codes (Simulating lazy data entry)
# Randomly drop 5% of the ELM codes
missing_indices = df.sample(frac=0.05, random_state=1).index
df.loc[missing_indices, 'elm_code'] = np.nan

# Chaos 2: Inconsistent Categorizations (Simulating human error)
# Map some clean categories to messy variations
messy_mapping = {
    'Engine': ['engine', 'ENG', 'Motor', 'Engine'],
    'Transmission': ['Trans', 'transmission', 'Gearbox', 'Transmission'],
    'Electrical': ['electric', 'ELEC', 'Electrical']
}

def make_messy(row):
    family = row['model_family_group']
    if family in messy_mapping and random.random() < 0.3: # 30% chance to mess it up
        return random.choice(messy_mapping[family])
    return family

df['model_family_group'] = df.apply(make_messy, axis=1)

# Chaos 3: Extreme Pricing Anomalies (Simulating decimal/system errors)
# Take 1% of the data and multiply the price by 100 to create massive outliers
anomaly_indices = df.sample(frac=0.01, random_state=2).index
df.loc[anomaly_indices, 'base_price'] = df.loc[anomaly_indices, 'base_price'] * 100

# ==========================================
# SAVE THE DATA
# ==========================================

# Ensure the output directory exists
output_dir = os.path.join('data', 'raw')
os.makedirs(output_dir, exist_ok=True)

# Save to CSV
file_path = os.path.join(output_dir, 'messy_spare_parts.csv')
df.to_csv(file_path, index=False)

print(f"Success! Saved messy dataset to: {file_path}")