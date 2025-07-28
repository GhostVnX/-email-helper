# worker.py — Scheduled Background Sender for Large Campaigns

import time
from datetime import datetime
from connect_gmail import login_to_gmail, send_email
from campaign_utils import load_campaign_data, get_next_batch, save_sent_batch
import os
import logging

logging.basicConfig(level=logging.INFO)

# List all campaigns
CAMPAIGN_DIR = "campaigns"
campaign_files = [f for f in os.listdir(CAMPAIGN_DIR) if f.endswith(".csv")]
campaign_names = [f.replace(".csv", "") for f in campaign_files]

# Gmail credentials
creds = login_to_gmail()

# Loop through all campaigns
for campaign in campaign_names:
    logging.info(f"Processing campaign: {campaign}")
    df = load_campaign_data(campaign)

    batch_num, batch_df = get_next_batch(df, campaign)
    if batch_df is None:
        logging.info(f"✅ All emails already sent for '{campaign}'.")
        continue

    sent_emails = set()
    for _, row in batch_df.iterrows():
        email = row.get("email")
        name = row.get("name", "there")
        subject = f"Follow-up from GhostBot ({datetime.today().strftime('%Y-%m-%d')})"
        body = f"Hi {name}, just checking in as promised.<br><br>— GhostBot"
        result = send_email(creds, email, subject, body, campaign)
        if result.get("status") == "success":
            sent_emails.add(email)
            logging.info(f"✅ Sent to {email}")
        else:
            logging.warning(f"❌ Failed to send to {email}: {result.get('error')}")
        time.sleep(2)

    save_sent_batch(campaign, batch_num, sent_emails)
    logging.info(f"📤 Batch {batch_num} for '{campaign}' complete.")
