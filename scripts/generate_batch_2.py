import pandas as pd
import numpy as np
from faker import Faker
import random
import os

fake = Faker()
NUM_RECORDS = 5000  # A smaller daily batch

data = {
    'part_id': [f"PRT-B2-{str(i).zfill(4)}" for i in range(1, NUM_RECORDS + 1)],
    'part_name': [fake.word().capitalize() + " " + random.choice(['Valve', 'Bolt', 'Sensor']) for _ in range(NUM_RECORDS)],
    'elm_code': [f"ELM-{random.randint(1000, 9999)}" for _ in range(NUM_RECORDS)],
    'model_family_group': [random.choice(['Engine', 'eng', 'Transmission', 'electric']) for _ in range(NUM_RECORDS)],
    'base_price': np.round(np.random.uniform(10.0, 500.0, NUM_RECORDS), 2),
    'stock_quantity': np.random.randint(0, 1000, NUM_RECORDS)
}

df = pd.DataFrame(data)

# Inject one massive anomaly just to be sure our transformer catches it
df.loc[0, 'base_price'] = 99999.99 

output_dir = os.path.join('data', 'raw')
file_path = os.path.join(output_dir, 'messy_spare_parts_batch_2.csv')
df.to_csv(file_path, index=False)
print(f"Batch 2 generated with {NUM_RECORDS} records!")