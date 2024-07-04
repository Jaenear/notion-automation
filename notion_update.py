import requests
import json
from datetime import datetime, date

NOTION_API_KEY = 'secret_DAgF0ADh9gD3xVmtdJp25LZa070ejmXKDSOEqHQGcWj'
DATABASE_ID = '259c5548a62b4288871b96c4ed61ab03'
HEADER = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_database_items():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADER)
    if response.status_code != 200:
        print(f"Error: API 호출 실패. 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        return None
    return response.json()

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
    if response.status_code != 200:
        print(f"Error: 항목 업데이트 실패. 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        print(f"요청 데이터: {json.dumps(update_data, ensure_ascii=False)}")
    return response.status_code == 200

def main():
    items = get_database_items()
    if items is None:
        print("데이터베이스 조회에 실패했습니다. 프로그램을 종료합니다.")
        return

    today = date.today()
    updated_count = 0
    skipped_count = 0

    for item in items.get("results", []):
        try:
            date_prop = item["properties"].get("날짜", {}).get("date", {})
            current_status = item["properties"].get("진행사항", {}).get("status", {}).get("name")
            shape = item["properties"].get("형태", {}).get("status", {}).get("name")

            # 건너뛰어야 할 조건 확인
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
        
        except Exception as e:
            print(f"Error: 항목 처리 중 예외 발생: {e}")

    print(f"처리 완료. 총 {updated_count}개 항목이 업데이트되었습니다.")
    print(f"총 {skipped_count}개 항목이 건너뛰어졌습니다.")

if __name__ == "__main__":
    main()