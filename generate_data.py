import pandas as pd
import random
from datetime import datetime, timedelta

def generate_mock_data():
    categories = [
        {"type": "payment_error", "keywords": ["페이 충전 실패", "결제 오류", "돈이 안들어와요", "충전 안됨", "결제 취소 불가"], "rating_range": [1, 2]},
        {"type": "app_crash", "keywords": ["앱 튕김", "접속 불가", "로그인 실패", "실행 안됨", "화면 멈춤"], "rating_range": [1, 2]},
        {"type": "ui_delivery", "keywords": ["배송 언제 오나요", "디자인이 별로에요", "글씨가 너무 작아요", "색상이 촌스러워요", "배송 조회 안됨"], "rating_range": [3, 3]},
        {"type": "satisfaction", "keywords": ["기능 좋아요", "빠른 응대 감사합니다", "편리해요", "잘 쓰고 있습니다", "최고에요"], "rating_range": [4, 5]}
    ]

    data = []
    start_date = datetime.now() - timedelta(days=30)

    for i in range(1, 51): # 50 reviews
        category = random.choice(categories)
        rating = random.randint(category["rating_range"][0], category["rating_range"][1])
        text = random.choice(category["keywords"]) + " " + random.choice(["ㅠㅠ", "...", "!", "ㅋㅋ", ""])
        
        # Add some variation
        if rating <= 2:
            text = f"[{category['type']}] {text} 해결 좀 해주세요."
        elif rating == 3:
            text = f"{text} 그냥 그렇네요."
        else:
            text = f"{text} 앞으로도 잘 부탁드려요."

        review = {
            "review_id": i,
            "date": (start_date + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "review_text": text,
            "star_rating": rating
        }
        data.append(review)

    df = pd.DataFrame(data)
    df.to_csv("data/raw/mock_reviews.csv", index=False, encoding="utf-8-sig")
    print("Mock data generated at data/raw/mock_reviews.csv")

if __name__ == "__main__":
    generate_mock_data()
