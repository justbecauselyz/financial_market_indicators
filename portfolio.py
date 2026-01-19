import requests
import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import squarify # 히트맵(트리맵) 그리는 라이브러리

# 환경변수 가져오기
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("PORTFOLIO_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 1. 노션 DB에서 보유 종목 가져오기
def get_portfolio():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    portfolio_data = []
    
    # 페이지가 많을 수 있으니 pagination 처리 (일단 단순화)
    response = requests.post(url, headers=headers).json()
    
    for page in response.get("results", []):
        try:
            props = page["properties"]
            # 데이터 추출 (속성 이름이 노션과 똑같아야 함)
            ticker = props["티커"]["rich_text"][0]["plain_text"]
            qty = props["보유수량"]["number"]
            avg_price = props["평단가"]["number"]
            name = props["종목명"]["title"][0]["plain_text"]
            page_id = page["id"]
            
            portfolio_data.append({
                "page_id": page_id,
                "name": name,
                "ticker": ticker,
                "qty": qty,
                "avg_price": avg_price
            })
        except Exception as e:
            print(f"⚠️ 데이터 읽기 실패 (빈 행이 있나요?): {e}")
            
    return pd.DataFrame(portfolio_data)

# 2. 현재가 조회 및 노션 업데이트 + 히트맵 데이터 준비
def update_prices_and_get_data(df):
    updated_rows = []
    
    print("⏳ 가격 조회 및 업데이트 시작...")
    for index, row in df.iterrows():
        try:
            # yfinance로 현재가 조회
            ticker_symbol = row['ticker']
            stock = yf.Ticker(ticker_symbol)
            # 장중이면 현재가, 장 마감이면 종가
            price = stock.fast_info['last_price'] 
            
            # 노션 업데이트 (현재가)
            update_url = f"https://api.notion.com/v1/pages/{row['page_id']}"
            update_data = {
                "properties": {
                    "현재가": {"number": round(price, 2)}
                }
            }
            requests.patch(update_url, headers=headers, json=update_data)
            print(f"✅ {row['name']} 업데이트 완료: {price}")
            
            # 히트맵용 데이터 계산
            current_value = price * row['qty'] # 평가금액
            return_rate = ((price - row['avg_price']) / row['avg_price']) * 100 # 수익률
            
            updated_rows.append({
                "label": f"{row['ticker']}\n{return_rate:.1f}%",
                "value": current_value,
                "return_rate": return_rate
            })
            
        except Exception as e:
            print(f"❌ {row['name']} 처리 중 에러: {e}")
            
    return pd.DataFrame(updated_rows)

# 3. 포트폴리오 히트맵 그리기 (이미지 저장)
def draw_heatmap(df):
    if df.empty:
        return

    # 색상 설정 (한국: 수익=빨강, 손실=파랑)
    # 수익률에 따라 색상 매핑
    colors = []
    for rate in df['return_rate']:
        if rate > 0:
            # 수익: 연한 빨강 ~ 진한 빨강
            intensity = min(rate / 30, 1) # 30% 이상이면 최대 빨강
            colors.append((1, 1 - intensity, 1 - intensity)) 
        else:
            # 손실: 연한 파랑 ~ 진한 파랑
            intensity = min(abs(rate) / 30, 1)
            colors.append((1 - intensity, 1 - intensity, 1))

    plt.figure(figsize=(12, 8))
    
    # 트리맵 그리기 (크기=평가금액, 색상=수익률)
    squarify.plot(sizes=df['value'], label=df['label'], color=colors, alpha=0.8, 
                  text_kwargs={'fontsize':12, 'fontweight':'bold'})
    
    plt.title("My Stock Portfolio Map", fontsize=18)
    plt.axis('off')
    
    # 이미지 파일로 저장
    plt.savefig("portfolio_heatmap.png")
    print("🎨 히트맵 이미지 저장 완료 (portfolio_heatmap.png)")

# 실행
if __name__ == "__main__":
    df = get_portfolio()
    if not df.empty:
        result_df = update_prices_and_get_data(df)
        draw_heatmap(result_df)
