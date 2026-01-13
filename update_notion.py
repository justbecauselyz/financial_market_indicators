import requests
from datetime import datetime
import os
import yfinance as yf  # 금융 데이터 라이브러리 추가

# Notion 설정
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("DATABASE_ID")

# 금융 데이터 가져오기 함수 (실제 데이터 연동)
def get_financial_data():
    print("⏳ 데이터 수집 중...")
    
    # 야후 파이낸스 티커 심볼
    # 환율(KRW=X), 코스피(^KS11), 코스닥(^KQ11), 나스닥(^IXIC)
    tickers = {
        "환율": "KRW=X",
        "코스피": "^KS11",
        "코스닥": "^KQ11",
        "나스닥": "^IXIC"
    }
    
    data = {}
    
    for name, symbol in tickers.items():
        try:
            # 가장 최근 장마감(Close) 가격 가져오기
            ticker = yf.Ticker(symbol)
            # 기간을 5일로 잡는 이유는 휴일일 경우 전날 데이터를 가져오기 위함
            history = ticker.history(period="5d") 
            last_price = history['Close'].iloc[-1] # 가장 최신 데이터 선택
            data[name] = round(last_price, 2) # 소수점 2자리 반올림
            print(f"✅ {name}: {data[name]}")
        except Exception as e:
            print(f"❌ {name} 데이터 수집 실패: {e}")
            data[name] = 0 # 에러 시 0으로 처리 (혹은 이전 값 유지 로직 필요)

    return data

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
            # 노션 DB의 속성 이름(환율, 코스피 등)이 정확히 일치해야 해!
            "환율": {"number": data.get("환율", 0)},
            "코스피": {"number": data.get("코스피", 0)},
            "코스닥": {"number": data.get("코스닥", 0)},
            "나스닥": {"number": data.get("나스닥", 0)}
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print(f"🎉 {today} 데이터 노션 전송 완료!")
    else:
        print(f"❌ 전송 오류: {response.text}")

# 실행
if __name__ == "__main__":
    financial_data = get_financial_data()
    if financial_data:
        add_to_notion(financial_data)
