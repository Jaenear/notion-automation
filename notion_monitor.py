import requests
import pandas as pd
from collections import Counter

# 노션 API 키와 데이터베이스 ID 설정
NOTION_API_KEY = "your_notion_api_key"
DATABASE_ID = "your_database_id"
NOTION_VERSION = "2021-08-16"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

def fetch_users_in_database(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()

def extract_user_ids(pages):
    user_ids = []
    for page in pages:
        if "properties" in page:
            for prop in page["properties"].values():
                if prop["type"] == "people":
                    user_ids.extend([person["id"] for person in prop["people"]])
    return user_ids

def extract_last_edited_by_ids(pages):
    last_edited_by_ids = [page["last_edited_by"]["id"] for page in pages if "last_edited_by" in page]
    return last_edited_by_ids

# 데이터베이스에서 페이지들 가져오기
database_data = fetch_users_in_database(DATABASE_ID)
pages = database_data["results"]

# 사용자 ID 추출
user_ids = extract_user_ids(pages)
last_edited_by_ids = extract_last_edited_by_ids(pages)

# 사용자 ID 빈도수 계산
user_id_counts = Counter(user_ids)
last_edited_by_id_counts = Counter(last_edited_by_ids)

# 데이터프레임 생성 및 저장
user_id_df = pd.DataFrame(user_id_counts.items(), columns=["User ID", "Count"])
last_edited_by_df = pd.DataFrame(last_edited_by_id_counts.items(), columns=["Last Edited By ID", "Count"])

user_id_df.to_csv("user_ids.csv", index=False)
last_edited_by_df.to_csv("last_edited_by_ids.csv", index=False)

print("User ID extraction complete. Check user_ids.csv and last_edited_by_ids.csv for results.")
