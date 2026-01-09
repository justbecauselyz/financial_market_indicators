import requests
from datetime import datetime
import os

# Notion 설정
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("DATABASE_ID")

# 금융 데이터 가져오기 함수
def get_financial_data():
    # 실제 사용 시 금융 API로 대체
    # 예: Alpha Vantage, Yahoo Finance API 등
    return {
        "환율": 1450.5,
        "코스피": 2500.3,
        "코스닥": 700.8,
        "나스닥": 15000.2
    }

# Notion DB에 데이터 추가
def add_to_notion(data):
    url = "https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": today
                        }
                    }
                ]
            },
            "환율": {"number": data["환율"]},
            "코스피": {"number": data["코스피"]},
            "코스닥": {"number": data["코스닥"]},
            "나스닥": {"number": data["나스닥"]}
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print(f"✅ {today} 데이터 추가 완료")
    else:
        print(f"❌ 오류: {response.text}")

# 실행
if __name__ == "__main__":
    financial_data = get_financial_data()
    add_to_notion(financial_data)