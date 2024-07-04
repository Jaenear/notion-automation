import requests
import json
from datetime import date
import os
import time

NOTION_API_KEY = os.getenv('NOTION_API_KEY')
DATABASE_ID = os.getenv('DATABASE_ID')
NEW_DATABASE_ID = os.getenv('NEW_DATABASE_ID')
HEADER = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_database_items(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    for _ in range(5):  # 최대 5번 재시도
        response = requests.post(url, headers=HEADER)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:  # Rate Limit 초과
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
        else:
            print(f"Error: API 호출 실패. 상태 코드: {response.status_code}")
            print(f"응답 내용: {response.text}")
            return None
    return None

def update_database_item(item_id, new_status):
    url = f"https://api.notion.com/v1/pages/{item_id}"
    update_data = {
        "properties": {
            "진행사항": {
                "status": {
                    "name": new_status
                }
            }
        }
    }
    response = requests.patch(url, headers=HEADER, json=update_data)
    return response.status_code == 200

def process_database(database_id):
    items = get_database_items(database_id)
    if items is None:
        print("데이터베이스 조회에 실패했습니다. 프로그램을 종료합니다.")
        return

    today = date.today()
    updated_count = 0
    skipped_count = 0

    for item in items.get("results", []):
        date_prop = item["properties"].get("날짜", {}).get("date", {})
        current_status = item["properties"].get("진행사항", {}).get("status", {}).get("name")
        shape = item["properties"].get("형태", {}).get("status", {}).get("name")

        if current_status in ['완료', '중단', '보류', '초과됨'] or shape == "스케줄":
            skipped_count += 1
            print(f"항목 건너뜀: ID {item['id']}, 상태: {current_status}, 형태: {shape}")
            continue

        if date_prop and date_prop.get("start") and shape == "작업":
            item_date = date.fromisoformat(date_prop["start"].split('T')[0])

            if item_date < today:
                if update_database_item(item["id"], "초과됨"):
                    updated_count += 1
                    print(f"항목 업데이트 완료: ID {item['id']}, 이전 상태: {current_status}, 새 상태: 초과됨")
                else:
                    print(f"항목 업데이트 실패: ID {item['id']}")
        else:
            print(f"Warning: 항목 {item['id']}에 유효한 날짜 정보가 없거나 형태가 '작업'이 아닙니다.")
    
    print(f"처리 완료. 총 {updated_count}개 항목이 업데이트되었습니다.")
    print(f"총 {skipped_count}개 항목이 건너뛰어졌습니다.")

def main():
    print("Processing primary database")
    process_database(DATABASE_ID)
    print("Processing new database")
    process_database(NEW_DATABASE_ID)

if __name__ == "__main__":
    main()
