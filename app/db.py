"""
    SQLite 테이터 페이스 조회기능은 모두 이곳에 모아둘 예정

    다른 파일에서 데이터 조회가 필요 시 이곳에 모아놓은 함수를 import해서 사용

    from app.db import query, one
    - pipeline/01_schema.py는 초기 DB생성, 데이터 저장의 역할만 담당
    - app/db.py 는 이미 만들어진 테이블의 뎅터를 조회하는 역할만 담당
    - 나중에 SQLite를 다른 DB로 교체할때 수정 범위를 줄일 수 있음
"""

import sqlite3

from app.config import DB_PATH

con = sqlite3.connect(DB_PATH)

def query(sql, params=()):
    return con.execute(sql, params).fetchall()

# products 테이블에서 제품이름을 3개만 가져오는 sql문을 params를 이용해서 호출

rows = query("SELECT name FROM products WHERE price >=? LIMIT 3", ("10000",))
print(rows)