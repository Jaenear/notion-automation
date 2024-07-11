import requests
import os
from datetime import datetime, timezone

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

# 마지막 확인 시간 저장 및 불러오기
def load_last_check_time():
    try:
        with open("last_check_time.txt", "r") as file:
            return datetime.fromisoformat(file.read().strip())
    except FileNotFoundError:
        return datetime(2021, 1, 1, tzinfo=timezone.utc)

def save_last_check_time(timestamp):
    with open("last_check_time.txt", "w") as file:
        file.write(timestamp.isoformat())

# 메인 실행 함수
def main():
    last_check_timestamp = load_last_check_time()
    database = fetch_database()
    changes = check_for_changes(last_check_timestamp, database)
    
    if changes:
        message = format_changes(changes)
        send_slack_message(message)
    
    # 마지막 확인 시간 업데이트
    current_time = datetime.now(timezone.utc)
    save_last_check_time(current_time)

if __name__ == "__main__":
    main()
