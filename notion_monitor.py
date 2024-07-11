import requests
import os
from datetime import datetime, timezone, timedelta

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
    response.raise_for_status()
    return response.json()

# 변경 사항 확인하기
def check_for_changes(start_time, database):
    changes = []
    for item in database['results']:
        last_edited_time = item['last_edited_time']
        if last_edited_time > start_time:
            changes.append(item)
    return changes

# 변경 사항 포맷팅하기
def format_changes(changes):
    formatted_message = "Changes detected:\n"
    now = datetime.now(timezone.utc)
    for change in changes:
        title = change['properties']['이름']['title'][0]['plain_text']
        url = change['url']
        last_edited_time = datetime.fromisoformat(change['last_edited_time'].replace("Z", "+00:00"))
        time_diff = now - last_edited_time
        minutes_ago = int(time_diff.total_seconds() // 60)
        formatted_message += f"- [{title}]({url}) at {minutes_ago}분 전에 변경됨\n"
    return formatted_message

# 슬랙으로 알림 보내기
def send_slack_message(message):
    payload = {
        "text": message
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    response.raise_for_status()

# 현재 시간 기준으로 10분 전 시간 계산
start_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

# 주기적으로 데이터베이스 확인하기
database = fetch_database()
changes = check_for_changes(start_time, database)

if changes:
    message = format_changes(changes)
    send_slack_message(message
