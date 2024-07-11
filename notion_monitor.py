import requests
import os
from datetime import datetime
import pytz

# 환경 변수에서 설정 값들 가져오기
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
LOCAL_TIMEZONE = os.getenv("LOCAL_TIMEZONE", "Asia/Seoul")  # 기본 값으로 "Asia/Seoul" 설정

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

# 페이지 내용 가져오기
def fetch_page_content(page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# 변경 사항 확인하기
def check_for_changes(last_check_timestamp, database):
    changes = []
    for item in database['results']:
        last_edited_time = item['last_edited_time']
        if last_edited_time > last_check_timestamp:
            page_id = item['id']
            page_content = fetch_page_content(page_id)
            changes.append({
                'item': item,
                'content': page_content
            })
    return changes

# UTC 시간을 로컬 시간으로 변환하기
def convert_to_local_time(utc_time_str, local_timezone):
    utc_time = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
    local_time = utc_time.astimezone(pytz.timezone(local_timezone))
    return local_time.strftime("%Y-%m-%d %H:%M:%S")

# 사용자 정보 가져오기
def fetch_user_info(user_id):
    url = f"https://api.notion.com/v1/users/{user_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    user_info = response.json()
    return user_info['name']

# 변경 사항 포맷팅하기
def format_changes(changes):
    formatted_message = "Changes detected:\n"
    for change in changes:
        item = change['item']
        content = change['content']
        title = item['properties']['이름']['title'][0]['plain_text']
        url = item['url']
        last_edited_time = convert_to_local_time(item['last_edited_time'], LOCAL_TIMEZONE)
        last_edited_by = fetch_user_info(item['last_edited_by']['id'])
        formatted_message += f"- [{title}]({url}) at {last_edited_time} by {last_edited_by}\n"
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
            return file.read().strip()
    except FileNotFoundError:
        return "2021-01-01T00:00:00.000Z"

def save_last_check_time(timestamp):
    with open("last_check_time.txt", "w") as file:
        file.write(timestamp)

# 초기화
last_check_timestamp = load_last_check_time()

# 주기적으로 데이터베이스 확인하기
database = fetch_database()
changes = check_for_changes(last_check_timestamp, database)

if changes:
    message = format_changes(changes)
    send_slack_message(message)

# 마지막 확인 시간 업데이트
current_time = datetime.utcnow().isoformat() + "Z"
save_last_check_time(current_time)
