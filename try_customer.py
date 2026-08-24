import sqlite3
import statistics

from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small")

con = sqlite3.connect("cosmetic.db")

# 고객의 후기만 따로 모아서 저장할 빈 딕셔너리 {고객ID: ['후기1','후기2',.....]}
history = {}

# 고객이 구매한 제품내용을 반복돌며 고객id, 제품이름, 별점 , 리뷰를 추출
for cid, name, rating, review in con.execute("""
    SELECT purchases.customer_id, products.name, purchases.rating, purchases.review
    FROM purchases JOIN products ON products.product_id = purchases.product_id
    WHERE purchases.is_holdout = 0
    ORDER BY purchases.customer_id
    """):
    # 고객 ID의 리스트가 없으면 생성하고, 상품명, 별점, 후기를 하나의 문장으로 추가
    history.setdefault(cid, []).append(f"{name} (별점 {rating} {review})")



print("history", history["C002"])