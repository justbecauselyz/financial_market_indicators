import requests
import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import squarify

# 환경변수 가져오기
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("PORTFOLIO_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_portfolio():
    print(f"🔍 [진단] 데이터베이스 ID 확인: {DATABASE_ID}")
    
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    # 요청 보내기
    response = requests.post(url, headers=headers)
    
    # 1. 상태 코드 확인
    print(f"📡 [통신 상태] 노션 응답 코드: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ [치명적 오류] 노션 연결 실패! 이유: {response.text}")
        return pd.DataFrame()

    data = response.json()
    results = data.get("results", [])
    
    # 2. 데이터 개수 확인
    print(f"📦 [데이터 수신] 가져온 데이터 개수: {len(results)}개")
    
    if len(results) == 0:
        print("⚠️ [경고] 노션 DB가 비어있거나, 로봇이 내용을 못 읽고 있습니다!")
        print("👉 체크리스트 1: DB에 데이터(행)가 한 줄이라도 있나요?")
        print("👉 체크리스트 2: Notion Integration이 이 DB에 '연결'되어 있나요?")
        return pd.DataFrame()

    portfolio_data = []
    
    for page in results:
        try:
            props = page["properties"]
            # 3. 속성 이름 확인을 위해 출력
            if len(portfolio_data) == 0:
                print(f"📝 [속성 확인] 첫 번째 행의 속성들: {list(props.keys())}")

            # 데이터 추출 (예외 처리 강화)
            ticker_list = props.get("티커", {}).get("rich_text", [])
            ticker = ticker_list[0]["plain_text"] if ticker_list else None
            
            name_list = props.get("종목명", {}).get("title", [])
            name = name_list[0]["plain_text"] if name_list else "이름없음"
            
            qty = props.get("보유수량", {}).get("number", 0)
            avg_price = props.get("평단가", {}).get("number", 0)
            
            if not ticker:
                print(f"⚠️ [스킵] '{name}' 종목에 티커가 없습니다.")
                continue

            portfolio_data.append({
                "page_id": page["id"],
                "name": name,
                "ticker": ticker,
                "qty": qty,
                "avg_price": avg_price
            })
            
        except Exception as e:
            print(f"❌ [데이터 파싱 오류] {e}")
            # 어떤 모양인지 보여줌
            print(f"문제가 된 데이터: {page['properties']}")

    return pd.DataFrame(portfolio_data)

def update_prices_and_get_data(df):
    updated_rows = []
    print("\n🚀 [주가 조회] 시작...")
    
    for index, row in df.iterrows():
        try:
            print(f"➡️ 조회 중: {row['name']} ({row['ticker']})")
            stock = yf.Ticker(row['ticker'])
            price = stock.fast_info['last_price']
            
            # 노션 업데이트
            update_url = f"https://api.notion.com/v1/pages/{row['page_id']}"
            update_data = {"properties": {"현재가": {"number": round(price, 2)}}}
            requests.patch(update_url, headers=headers, json=update_data)
            
            current_value = price * row['qty']
            return_rate = ((price - row['avg_price']) / row['avg_price']) * 100
            
            updated_rows.append({
                "label": f"{row['ticker']}\n{return_rate:.1f}%",
                "value": current_value,
                "return_rate": return_rate
            })
        except Exception as e:
            print(f"❌ [주가 조회 실패] {row['name']}: {e}")
            
    return pd.DataFrame(updated_rows)

def draw_heatmap(df):
    if df.empty:
        print("⚠️ [히트맵 중단] 그릴 데이터가 없습니다.")
        return

    print("🎨 [그림] 히트맵 생성 중...")
    colors = []
    for rate in df['return_rate']:
        if rate > 0:
            intensity = min(rate / 30, 1)
            colors.append((1, 1 - intensity, 1 - intensity)) 
        else:
            intensity = min(abs(rate) / 30, 1)
            colors.append((1 - intensity, 1 - intensity, 1))

    plt.figure(figsize=(12, 8))
    squarify.plot(sizes=df['value'], label=df['label'], color=colors, alpha=0.8, 
                  text_kwargs={'fontsize':12, 'fontweight':'bold'})
    plt.axis('off')
    plt.savefig("portfolio_heatmap.png")
    print("✅ [완료] 히트맵 이미지 저장됨!")

if __name__ == "__main__":
    df = get_portfolio()
    if not df.empty:
        result_df = update_prices_and_get_data(df)
        draw_heatmap(result_df)
    else:
        print("🔚 데이터가 없어서 스크립트를 종료합니다.")
