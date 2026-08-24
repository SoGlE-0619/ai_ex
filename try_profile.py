import sqlite3
from collections import Counter

import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

con = sqlite3.connect("cosmetic.db")

model = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-small",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True, "batch_size": 64}
)

product_rows = con.execute("""
    SELECT product_id, name, brand, category, price, skin_type, ingredient, concern, tags, description 
    FROM products ORDER BY product_id
""").fetchall()


# ===============================================
# 1. 상품아이디 리스트, 상품아이디별 벡터화할 상품정보 리스트
# ===============================================
# 상품 아이디만 리스트로 반환
product_ids = [r[0] for r in product_rows]
print(product_ids)

# 상품 아이디를 제외한 나머지 상품정보를 하나의 문자열로 묶어서 리스트로 반환
# 반환된 각각의 리스트를 벡터화 처리
product_vectors = np.array(model.embed_documents(
[
    " / ".join(str(x) for x in r[1:]) # 첫번재 제품아이디를 제외한 나머지 값들을 문자화 시킨뒤 하나의 문자열로 이어붙임
    for r in product_rows # 각레코드를 하나씩 추출해서 
]
), dtype="float32") 

print(product_vectors[0])

# ===============================================
# 2. 고객id별 기본정보 분리해서 가져옴
# ===============================================
# [c, *r in 리스트]
# [
#     ("C001", 25, "여성", "건성", "서울"), 
#     ("C001", 25, "여성", "건성", "서울"), 
# ]
# [
#     ("C001","나머지값")
# ]
# 기본 고객 정보를 가져옴 (이때 고객아이디와, 나머지 고객정보를 분리해서 저장)
customer_rows = con.execute("SELECT customer_id, age, gender, skin_type, city FROM customers")
customer_info = {c: r for c, *r in customer_rows}
print(customer_info["C002"])
print("-------")

# ===============================================
# 3. 고객별 구매 이력을 가져와서 딕서녀리 형태로 카테고라이징
# ===============================================
history = {}

for cid, name, cat, ing, concern, rating, review in con.execute("""
    SELECT purchases.customer_id, products.name, products.category, products.ingredient, products.concern, 
    purchases.rating, purchases.review
    FROM purchases JOIN products ON products.product_id = purchases.product_id
    WHERE purchases.is_holdout = 0
    ORDER BY purchases.customer_id, purchases.purchase_id
"""):
    history.setdefault(cid,[]).append((name, cat, ing, concern, rating, review))

# ("고객아이디", [제품명, 카테고리명, 성분, 피부걱정, 별점, 리뷰])
print(history["C002"])

# 지금까지 찾아놓은 고객별 구매 정보를 반환받음

# ===============================================
# 4. 고객별 인기 구매 상품 비교
# ===============================================
# is_holdout=1로 숨겨놓은 제품을 위의 정보와 비교하면서 해당고객이 구매한 제품중 인기 제품이 얼마나 많이 있는지 비교
# 해당 고객이 구매한 항목중 인기상품 항목만 가져옴 (이고객의 취향 비교를 위해 이고객의 정답 제품만 가져옴)
hits_product = dict(con.execute("SELECT customer_id, product_id FROM purchases WHERE is_holdout=1"))

# 고객아이디별로 구매한 제품명이 등록될 빈 딕셔너리
bought = {}
for cid, pid in con.execute("SELECT customer_id, product_id FROM purchases WHERE is_holdout=0"):
    bought.setdefault(cid, set()).add(pid)

print("002고객의 정답상품", hits_product["C002"])
print("002고객 정답을 제외한 구매상품", bought["C002"])
