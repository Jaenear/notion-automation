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
    return response.json(), response.request.url

# 사용자 정보 가져오기
def fetch_user(user_id):
    url = f"https://api.notion.com/v1/users/{user_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json(), response.request.url

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
    for change in changes:
        title = change['properties']['이름']['title'][0]['plain_text']
        url = change['url']
        last_edited_time = datetime.fromisoformat(change['last_edited_time'].replace("Z", "+00:00"))
        last_edited_time_kst = last_edited_time + timedelta(hours=9)  # UTC+9
        last_edited_time_kst_str = last_edited_time_kst.strftime('%Y-%m-%d %H:%M:%S')

        user_id = change['last_edited_by']['id']
        user_data, user_api = fetch_user(user_id)
        user_name = user_data['name']

        formatted_message += f"- [{title}]({url}) at {last_edited_time_kst_str} (KST) by {user_name} (User ID: {user_id})\n"

    return formatted_message

# 슬랙으로 알림 보내기
def send_slack_message(message, api_info):
    payload = {
        "text": f"{message}\n\nAPI Information:\n{api_info}"
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    response.raise_for_status()

# 현재 시간 기준으로 10분 전 시간 계산
start_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

# 주기적으로 데이터베이스 확인하기
database_data, db_api = fetch_database()
changes = check_for_changes(start_time, database_data)

if changes:
    message = format_changes(changes)
    api_info = f"Database API: {db_api}\n"
    for change in changes:
        user_id = change['last_edited_by']['id']
        user_data, user_api = fetch_user(user_id)
        api_info += f"User API for {user_data['name']} (User ID: {user_id}): {user_api}\n"
    send_slack_message(message, api_info)
