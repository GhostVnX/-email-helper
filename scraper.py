# scraper.py — Universal Google Search & Contact Extractor for GhostBot

import pandas as pd
import time
import re
from googleapiclient.discovery import build


def extract_emails_from_text(text):
    """Extract email addresses from a string using regex."""
    if not text:
        return []
    return re.findall(r"[\\w\\.-]+@[\\w\\.-]+\\.\\w+", text)


def search_google_and_extract_emails(query, api_key, cse_id, max_pages=3):
    """
    Perform a Google search using Custom Search API and extract emails from snippet text.

    Args:
        query (str): Search keyword.
        api_key (str): Your Google API key.
        cse_id (str): Custom Search Engine ID.
        max_pages (int): Number of pages to scrape (10 results per page).

    Returns:
        pd.DataFrame: A DataFrame with title, link, snippet, and extracted emails.
    """
    service = build("customsearch", "v1", developerKey=api_key)
    all_results = []

    for page in range(max_pages):
        start_index = page * 10 + 1
        try:
            res = service.cse().list(q=query, cx=cse_id, start=start_index).execute()
            for item in res.get("items", []):
                snippet = item.get("snippet", "")
                emails = extract_emails_from_text(snippet)
                all_results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": snippet,
                    "emails_found": ", ".join(emails) if emails else None
                })
            time.sleep(1)  # respect Google API quota
        except Exception as e:
            print(f"Error on page {page + 1}: {e}")
            continue

    df = pd.DataFrame(all_results)
    df = df.dropna(subset=["emails_found"])
    return df
