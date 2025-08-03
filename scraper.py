# scraper_module.py

import streamlit as st
import pandas as pd
import time
from googleapiclient.discovery import build

def google_search(query, api_key, cse_id, num_pages=3):
    service = build("customsearch", "v1", developerKey=api_key)
    results = []
    for page in range(num_pages):
        start = page * 10 + 1
        try:
            res = service.cse().list(
                q=query,
                cx=cse_id,
                start=start
            ).execute()
            for item in res.get("items", []):
                results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                })
            time.sleep(1)
        except Exception as e:
            st.warning(f"Error on '{query}' page {page + 1}: {e}")
            break
    return results

def extract_emails(results):
    import re
    emails = set()
    for item in results:
        text = f"{item['title']} {item['snippet']} {item['link']}"
        found = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        emails.update(found)
    return list(emails)
