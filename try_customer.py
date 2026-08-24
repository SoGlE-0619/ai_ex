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
"""
C002 고객에 대한 후기 리스트
[
    '세라마이드 브라이트닝 클렌징폼 (별점 5 고민하다 샀는데 잘 산 것 같아요. 향이 세지 않아서 좋아요.)', 
    '히알루론산 링클 클렌징폼 (별점 5 친구가 좋다고 해서 샀는데 만족해요. 건성인데 자극 없이 잘 썼어요.)'
]
""" 
# 각 고객마다의 여러개후기를 하나의 문자열로 묶어서 반환
joined = [" ".join(v) for v in history.values()]
print(len(joined)) # 300 

# 고객당 이어붙인 후기를 토큰갯수로 변환해서 올림차순으로 순서 정려
# 고객 후기당 토큰 개수 파악용 (어느 고객의 후기정보에 대한 토큰량이 많은지 확인 용도)
counts = sorted(len(tok.encode(t)) for t in joined)
print(counts)

# 고객별 후기갯수 구하기
buys = sorted(len(v) for v in history.values()) 
print(buys)

# 고객 평균후기 하나당 얼마의 토큰이 소비되는지 확인
print(sum(counts) / sum(buys)) # 구매후기 하나당 평균 토큰 갯수는 40개