# notion_monitor.py

import requests
import time
import os

# 환경 변수에서 설정 값들 가져오기
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 노션 데이터베이스에서 데이터 가져오기
def fetch_database():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    return response.json()

# 변경 사항 확인하기
def check_for_changes(last_check_timestamp, database):
    changes = []
    for item in database['results']:
        last_edited_time = item['last_edited_time']
        if last_edited_time > last_check_timestamp:
            changes.append(item)
    return changes

# 변경 사항 포맷팅하기
def format_changes(changes):
    formatted_message = "Changes detected:\n"
    for change in changes:
        title = change['properties']['이름']['title'][0]['plain_text']
        url = change['url']
        last_edited_time = change['last_edited_time']
        formatted_message += f"- [{title}]({url}) at {last_edited_time}\n"
    return formatted_message

# 슬랙으로 알림 보내기
def send_slack_message(message):
    payload = {
        "text": message
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    if response.status_code != 200:
        raise ValueError(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")

# 초기화
last_check_timestamp = "2021-01-01T00:00:00.000Z"

# 주기적으로 데이터베이스 확인하기
database = fetch_database()
changes = check_for_changes(last_check_timestamp, database)
if changes:
    message = format_changes(changes)
    send_slack_message(message)
last_check_timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
