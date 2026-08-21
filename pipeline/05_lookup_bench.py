"""같은 것을 두 번 찾지 않는다 ― 딕셔너리에 담아 두기 vs 매번 SELECT.

「왜 딕셔너리에 담아 두나. 그냥 필요할 때 SELECT 하면 되지 않나」
그 물음을 **재서** 답한다.

    (A) 조각마다 SELECT section_id FROM sections WHERE product_id=? AND section=?
    (B) 딕셔너리에 담아 두고 꺼내 쓴다

🔴 이 파일은 DB 를 **읽기만 한다.** 지워도 파이프라인이 돈다.

앞:    python pipeline/02_chunk.py
실행:  python pipeline/05_lookup_bench.py
"""

import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from app.core.config import DB_PATH

con = sqlite3.connect(DB_PATH)

# 조각이 저장 모듈에 도착했을 때 들고 있는 것과 같은 모양 ― 자연키뿐이다
keys = con.execute("SELECT product_id, section FROM chunks ORDER BY chunk_id").fetchall()

print(f"조각 {len(keys):,}건에 대해 section_id 를 찾는다\n")

# ─────────────────────────────────────────────── (A) 매번 SELECT
started = time.perf_counter()
a_result = []
for product_id, section in keys:
    row = con.execute(
        "SELECT section_id FROM sections WHERE product_id = ? AND section = ?",
        (product_id, section)).fetchone()
    a_result.append(row[0])
a_elapsed = time.perf_counter() - started

# ─────────────────────────────────────────────── (B) 담아 두고 꺼내 쓰기
started = time.perf_counter()
section_id_lookup = {(product_id, section): section_id for section_id, product_id, section
                     in con.execute("SELECT section_id, product_id, section FROM sections")}
b_result = [section_id_lookup[key] for key in keys]
b_elapsed = time.perf_counter() - started

assert a_result == b_result, "두 방식의 답이 다르다. 재기 전에 이것부터 고쳐야 한다"

print(f"  (A) 조각마다 SELECT      {a_elapsed:>8.4f}초   (질의 {len(keys):,}번)")
print(f"  (B) 담아 두고 꺼내 쓰기   {b_elapsed:>8.4f}초   (질의 1번 + 딕셔너리 조회)")
print(f"  {a_elapsed / b_elapsed:>26.1f}배   ― 답은 {len(a_result):,}건 모두 같다")
con.close()
