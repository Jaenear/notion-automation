import requests
import os

# 환경 변수에서 설정 값들 가져오기
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 사용자 정보 조회 함수 정의
def fetch_user_info(user_id):
    url = f"https://api.notion.com/v1/users/{user_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    user_data = response.json()
    return user_data

# last_edited_by 필드의 ID 목록
last_edited_by_ids = [
    '8fb5ae58-80dc-4c86-8886-90975e2fc726',
    'b8231844-d81d-4f86-ab7a-de5f3ab895a1',
    '00000000-0000-0000-0000-000000000003',
    '09022b86-684f-45bb-a111-2bdecd2d7493'
]

# 각 ID에 대한 사용자 정보 조회
user_info_list = []
for user_id in last_edited_by_ids:
    try:
        user_info = fetch_user_info(user_id)
        user_info_list.append(user_info)
    except requests.exceptions.HTTPError as e:
        user_info_list.append({'user_id': user_id, 'error': str(e)})

# 사용자 정보 출력
for info in user_info_list:
    print(info)
