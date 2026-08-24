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
    # 고객 특정 제품을 반복해서 샀더라도  반복된 제품아이디를 중복처리하지 않고 출력하기 위함
    bought.setdefault(cid, set()).add(pid)

print("002고객의 정답상품", hits_product["C002"])
print("002고객 정답을 제외한 구매상품", bought["C002"])

# 고객별 구매 이력중 인기 상품 구매 이력이 있는 고객 아이디를 리스트로 반환
# history(고객의 구매 내역) 과 hits_product(인기상품 구매내역)을 비교해서 각 레코드의 공통의 cid(고객 아이디)를 비교하면
# 결국 인기상품을 구매한 고객정보 목록을 확인 가능
# 고객의 구매내역을 반복돌면서 해당고객 아이디가 인기상품 구매목록 아이디와 겹치는 정보만 추출
cids = [c for c in sorted(history) if c in hits_product]
print(len(cids))

# 리스트에사 특정 값의 갯수를 카운트에서 가장 많이 나온 value값을 상위 n번째까지 반환해주는 함수
def top(items, n=3):
    # 리스트에 각 값의 갯수를 카운트해서 가장 많이 나온값의 상위 n번째 값까지 반환하는 함수
    return "/".join(x for x, _ in Counter(items).most_common(n))


# 인자로 전달받은 고객아이디를 통해서 해당 고객의 구매이력을 선호도와 함께 반환하는 함수
def taste(cid):
    h = history[cid]

    #특정 고객의 구매이력에서 별점만 모두 더한뒤, 해당 별점의 총합을 구매 건수로 나면 해당 고객의 평균 별점 반환
    avg = sum(x[4] for x in h) / len(h)

    # 고객의 피부타입과 구매이력에서 자주 등장한 항목들을 추출해서 하나의 소개 문장으로 만든다.
    # customer_info[cid][2]: 고객의 피부타입

    # 해당 고객이 제일 많이 구매한 제품 카테고리 명이 반환
    skin_type = customer_info[cid][2] # 해당 사용자의 스킨 타입
    t_category = top(x[1] for x in h) # 해당 사용자가 구매한 제품중 가장 많이 언급된 제품 카테고리 명
    t_ingredient = top(x[2] for x in h) # 해당 사용자가 구매한 제품중 가장 많이 언급된 성분명
    t_concern = top(x[3] for x in h)

    return (f"스킨타입:{skin_type} / 선호제품 카테고리: {t_category} / 선호 성분: {t_ingredient} / 주요관심사: {t_concern} / 평균별점: {avg:.1f} ")

print("특정 고객 취향 분석 문장", taste("C002"))

# 지금까지 만들어놓은 정보셋을 어떤식으로 조합해서 임베딩값을 비교해야지 우리가 원하는 정밀도에 맞게 검사할수 있는 비교
# 프리셋1: 고객의 후기만 이용해서 맞춤 상품 추천도
# 프리셋2: 고객의 취향만 이용해서 맞춤 상품 추천도
# 프리셋3: 고객의 취향+ 나이,성별,거주지역 이용해서 맞춤 상품 추천도
# 프리셋4: 고객의 취향 + 고객후기 이용해서 맞춤 상품 추천도

# ===============================================
# 람다식 정리
# ===============================================
# def double(x):
#     return x*2

# lambda x: x*2
# 위와 같이 간단 구조의 함수임에도 불구하고 매번 함수명을 지정하고 들여쓰기 해서 함수를 정의하는게 번거로움
# 지금같은 경우에는 여러가지 프리셋 함수를 만들어서 다양하게 테스트해야되는데 매번 함수 정의형태로 만드는게 비효율 -> 람다식으로 축약
VARIANTS = [
    #("함수라벨", 특정 값을 반환하는 함수의 호출문이 아닌 정의형태가 들어가 있음)
    ("1.후기만 이어붙임", lambda c: " ".join(f"{x[0]} (별점 {x[4]}) {x[5]}" for x in history[c])),
    ("2.취향만 가져옴", taste),
    ("3.취향+나이,성별,거주지", lambda c: f"{customer_info[c][0] // 10 * 10}대  /  {'여성' if customer_info[c][1] =="F" else '남성'} / {customer_info[c][3]} /" + taste(c) ),
    # 기본고객정보 / 후기1, 후기2, 후기3, 후기4
    ("4.취향 + 후기", lambda c: taste(c) + " / " +" ".join(x[5] for x in history[c])[:200]),
]

# 위의 variants값을 이용해서 해당 프리셋을 반복돌면서 각 결과정보를 문자열로 출력 (미션 : 30분까지 테스트)
for label, func in VARIANTS: 
    # cids에 고객의 id값이 리스트 형태로 들어가 있음
    print(f"{label}: {func("C002")}")
    print()

# 1.후기만 이어붙임: 세라마이드 브라이트닝 클렌징폼 (별점 5) 고민하다 샀는데 잘 산 것 같아요. 향이 세지 않아서 좋아요. 히알루론산 링클 클렌징폼 (별점 5) 친구가 좋다고 해서 샀는데 만족해요. 건성인데 자극 없이 잘 썼어요.

# 2.취향만 가져옴: 스킨타입:건성 / 선호제품 카테고리: 클렌징폼 / 선호 성분: 세라마이드/히알루론산 / 주요관심사: 미백/주름 / 평균별점: 5.0 

# 3.취향+나이,성별,거주지: 30대  /  여성 / 광주 /스킨타입:건성 / 선호제품 카테고리: 클렌징폼 / 선호 성분: 세라마이드/히알루론산 / 주요관심사: 미백/주름 / 평균별점: 5.0 

# 4.취향 + 후기: 스킨타입:건성 / 선호제품 카테고리: 클렌징폼 / 선호 성분: 세라마이드/히알루론산 / 주요관심사: 미백/주름 / 평균별점: 5.0  / 고민하다 샀는데 잘 산 것 같아요. 향이 세지 않아서 좋아요. 친구가 좋다고 해서 샀는데 만족해요. 건성인데 자극 없이 잘 썼어요.

