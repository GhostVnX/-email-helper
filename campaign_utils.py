# campaign_utils.py

import os
import pandas as pd
import pickle
from datetime import datetime

CAMPAIGN_DIR = "campaigns"
os.makedirs(CAMPAIGN_DIR, exist_ok=True)

# Save uploaded campaign data to file
def save_campaign_data(campaign_name, df):
    path = os.path.join(CAMPAIGN_DIR, f"{campaign_name}.csv")
    df.to_csv(path, index=False)

# Load campaign from disk
def load_campaign_data(campaign_name):
    path = os.path.join(CAMPAIGN_DIR, f"{campaign_name}.csv")
    return pd.read_csv(path) if os.path.exists(path) else None

# Split large DataFrame into daily batches (e.g., 500 per day)
def split_batches(df, batch_size=500):
    batches = [df[i:i + batch_size] for i in range(0, df.shape[0], batch_size)]
    return batches

# Optional: load batches separately
BATCH_LOG_DIR = "logs/batches"
os.makedirs(BATCH_LOG_DIR, exist_ok=True)

def save_sent_batch(campaign_name, batch_number, sent_emails):
    path = os.path.join(BATCH_LOG_DIR, f"{campaign_name}_batch{batch_number}.pkl")
    with open(path, "wb") as f:
        pickle.dump(sent_emails, f)

def load_sent_batch(campaign_name, batch_number):
    path = os.path.join(BATCH_LOG_DIR, f"{campaign_name}_batch{batch_number}.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return set()

# Get next unsent batch
def get_next_batch(df, campaign_name):
    batches = split_batches(df)
    for i, batch in enumerate(batches):
        sent = load_sent_batch(campaign_name, i)
        unsent_batch = batch[~batch["email"].isin(sent)]
        if not unsent_batch.empty:
            return i, unsent_batch
    return None, None
