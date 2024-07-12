import requests
import os
import re
from collections import Counter
import pandas as pd

# 환경 변수에서 설정 값들 가져오기
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 사용자 정보 조회 함수 정의
def fetch_all_users():
    url = "https://api.notion.com/v1/users"
    user_ids = []
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        user_ids.extend([user['id'] for user in data['results']])
        url = data.get('next_cursor')
    return user_ids

# 노션 API를 사용하여 모든 사용자 ID를 가져오기
all_user_ids = fetch_all_users()

# 로그 파일 경로
log_file_path = '0_monitor.txt'

# 로그 파일 읽기
with open(log_file_path, 'r') as file:
    log_data = file.read()

# last_edited_by 필드의 ID 추출
last_edited_by_pattern = re.compile(r"'last_edited_by': {'object': 'user', 'id': '(.*?)'}")
last_edited_by_ids = last_edited_by_pattern.findall(log_data)

# ID 발생 횟수 계산
last_edited_by_counts = Counter(last_edited_by_ids)

# 데이터프레임 생성 및 저장
last_edited_by_df = pd.DataFrame(last_edited_by_counts.items(), columns=['ID', 'Count'])
last_edited_by_df.to_csv('last_edited_by_ids.csv', index=False)

user_id_df = pd.DataFrame(all_user_ids, columns=['ID'])
user_id_df['Count'] = 0  # 사용자 ID는 빈도수를 계산할 필요가 없으므로 0으로 설정
user_id_df.to_csv('user_ids.csv', index=False)

print("Data extraction complete. Check last_edited_by_ids.csv and user_ids.csv for results.")
