import requests
import os
from datetime import datetime

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

# 변경 사항 포맷팅하기
def format_changes(changes):
    formatted_message = "Changes detected:\n"
    for change in changes:
        item = change['item']
        content = change['content']
        title = item['properties']['이름']['title'][0]['plain_text']
        url = item['url']
        last_edited_time = item['last_edited_time']
        changes_summary = get_changes_summary(title, content)
        formatted_message += f"- [{title}]({url}) at {last_edited_time}, {changes_summary}\n"
    return formatted_message

# 페이지 변경 요약 가져오기
def get_changes_summary(title, new_content):
    old_content_dir = "old_contents"
    old_content_file = f"{old_content_dir}/old_content_{title}.txt"
    
    # 디렉터리가 없으면 생성
    if not os.path.exists(old_content_dir):
        os.makedirs(old_content_dir)

    new_content_text = extract_text_from_content(new_content)

    if os.path.exists(old_content_file):
        with open(old_content_file, "r") as file:
            old_content_text = file.read()
    else:
        old_content_text = ""

    changes_summary = compare_content(old_content_text, new_content_text)

    with open(old_content_file, "w") as file:
        file.write(new_content_text)

    return changes_summary

# 콘텐츠에서 텍스트 추출
def extract_text_from_content(content):
    text = ""
    for block in content.get('results', []):
        block_type = block.get('type')
        if block_type == 'paragraph':
            for text_block in block['paragraph'].get('text', []):
                text += text_block['plain_text'] + "\n"
        elif block_type == 'heading_1':
            for text_block in block['heading_1'].get('text', []):
                text += "# " + text_block['plain_text'] + "\n"
        elif block_type == 'heading_2':
            for text_block in block['heading_2'].get('text', []):
                text += "## " + text_block['plain_text'] + "\n"
        elif block_type == 'heading_3':
            for text_block in block['heading_3'].get('text', []):
                text += "### " + text_block['plain_text'] + "\n"
        # 추가 블록 타입을 필요에 따라 처리
    return text

# 콘텐츠 비교
def compare_content(old_content, new_content):
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()

    changes = []
    for i, line in enumerate(new_lines):
        if i >= len(old_lines):
            changes.append(f"Added: {line}")
        elif line != old_lines[i]:
            changes.append(f"Changed: {line}")

    for i in range(len(new_lines), len(old_lines)):
        changes.append(f"Removed: {old_lines[i]}")

    return ", ".join(changes)

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
