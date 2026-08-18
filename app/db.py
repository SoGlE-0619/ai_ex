"""
  SQLite 데이터베이스 조회기능은 모두 이곳에 모아둘 예정

  다른 파일에서 데이터조회가 필요시 이곳에 모아놓은 함수를 import해서 사용

  from app.db import query, one
  - pipeline/01_schema.py는 초기 DB생성, 데이터 저장의 역할만 담당
  - app/db.py 는 이미 만들어진 테이블의 데이터를 조회하는 역할만 담당
  - 나중에 SQLite를 다른 DB로 교체할때 수정 범위를 줄일 수 있음
"""

import sqlite3
from app.config import DB_PATH
con = sqlite3.connect(DB_PATH)

# 여러개의 행을 list[tuple] 형태로 반환하는 함수
def query(sql, params=()):
  return con.execute(sql, params).fetchall()

# 하나의 행 정보만 반환하는 함수 (고객정보)
def one(sql, params=()):
  return con.execute(sql, params).fetchone()

# rows = query("SELECT name FROM products WHERE price >=? LIMIT 3", ("10000",))
# print(rows)

# C001이라는 아이디의 고객정보를 가져오는 구문
info = one("SELECT * FROM customers WHERE customer_id = ?", ("C001",))
print(info)

