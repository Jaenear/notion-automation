import requests
import os
from datetime import datetime, timezone

# 환경 변수에서 설정 값들 가져오기
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
LAST_CHECK_TIME = os.getenv("LAST_CHECK_TIME")

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
def check_for_changes(last_check_timestamp, database):
    changes = []
    for item in database['results']:
        last_edited_time = datetime.fromisoformat(item['last_edited_time'].replace('Z', '+00:00'))
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
    response.raise_for_status()

# 메인 실행 함수
def main():
    if LAST_CHECK_TIME:
        last_check_timestamp = datetime.fromisoformat(LAST_CHECK_TIME.replace('Z', '+00:00'))
    else:
        last_check_timestamp = datetime(2021, 1, 1, tzinfo=timezone.utc)

    database = fetch_database()
    changes = check_for_changes(last_check_timestamp, database)
    
    if changes:
        message = format_changes(changes)
        send_slack_message(message)

if __name__ == "__main__":
    main()
