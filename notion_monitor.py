import requests
import os
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)

file_path = "/path/to/your/last_check_time.txt"  # 절대 경로로 수정

# Load last check time
if os.path.exists(file_path):
    with open(file_path, "r") as f:
        last_check_time = f.read().strip()
        logging.info(f"Loaded last check time: {last_check_time}")
else:
    logging.info("Last check time file does not exist. Creating a new one.")
    last_check_time = "2021-01-01T00:00:00.000Z"
    with open(file_path, "w") as f:
        f.write(last_check_time)

last_check_time_dt = datetime.fromisoformat(last_check_time.replace("Z", "+00:00"))

# Fetch data from Notion
notion_api_key = os.environ["NOTION_API_KEY"]
database_id = os.environ["DATABASE_ID"]
headers = {
    "Authorization": f"Bearer {notion_api_key}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

url = f"https://api.notion.com/v1/databases/{database_id}/query"
response = requests.post(url, headers=headers)
response.raise_for_status()
data = response.json()

changes_detected = []

for result in data["results"]:
    last_edited_time = result["last_edited_time"]
    last_edited_time_dt = datetime.fromisoformat(last_edited_time.replace("Z", "+00:00"))
    logging.info(f"Item last edited time: {last_edited_time_dt}")
    if last_edited_time_dt > last_check_time_dt:
        changes_detected.append(f"- [{result['properties']['Name']['title'][0]['plain_text']}]({result['url']}) at {last_edited_time}")

# Send Slack notification if changes are detected
if changes_detected:
    slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    message = "Changes detected:\n" + "\n".join(changes_detected)
    response = requests.post(slack_webhook_url, json={"text": message})
    response.raise_for_status()

# Update last check time
current_time = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat() + 'Z'
with open(file_path, "w") as f:
    f.write(current_time)
logging.info(f"Saved last check time: {current_time}")
