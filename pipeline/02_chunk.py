"""긴 상품 상세를 조각으로 자르고 저장한다.

🔴 이 파일에는 자르는 코드가 없다. prep/chunking.py 가 자르고, prep/storage.py 가
   넣는다. 이 파일은 둘을 순서대로 부르고 **숫자를 보여 준다.**
   조절값은 prep/options.py 한 곳에 있다.

🔴 벡터는 여기서 안 만든다. 03_embed.py 가 한다. 가른 이유는 값이다 ―
   조각을 다시 자르는 건 몇 초지만 벡터를 다시 만드는 건 로컬에서 30초쯤 걸리고,
   상용 API 를 켜 두면 그대로 요금이 된다.

앞:    python pipeline/01_schema.py
실행:  python pipeline/02_chunk.py
"""

import sqlite3
import statistics
import sys
from pathlib import Path

# pipeline/ 안에서 돌리는데 app/ 과 pipeline.prep 을 불러와야 한다. 그래서 뿌리를 경로에 넣는다
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from huggingface_hub.utils import disable_progress_bars
from huggingface_hub.utils import logging as hub_logging
from transformers import logging as hf_logging

hf_logging.set_verbosity_error()
hf_logging.disable_progress_bar()
hub_logging.set_verbosity_error()
disable_progress_bars()

from app.core.config import DB_PATH, EMBED_MAX_TOKENS, EMBED_TOKENIZER
from pipeline.prep import chunking, storage
from pipeline.prep.options import (CHUNK_OVERLAP, CHUNK_SIZE, PREFIX_BUDGET,
                                   RESPLIT_OVER)

con = sqlite3.connect(DB_PATH)
con.execute("PRAGMA foreign_keys = ON")

ntok = chunking.count_tokens


def dist(values):
    """분포 한 줄 ― 최소 / 중앙 / 최대"""
    return (f"최소 {min(values):>5,} · 중앙 {int(statistics.median(values)):>5,} · "
            f"최대 {max(values):>5,}")


details = con.execute("""
    SELECT product_details.product_id, products.name, product_details.detail
    FROM product_details
    JOIN products ON product_details.product_id = products.product_id
    ORDER BY product_details.product_id
""").fetchall()

print(f"상품 상세 {len(details)}건을 읽었다\n")


# ═══════════════════════════════════════════════ ① 왜 자르나
print("=" * 74)
print("① 왜 자르나 ― 통째로 넣으면 뒤가 잘린다")
print("=" * 74)

full_tokens = [ntok(detail) for _, _, detail in details]
over = [n for n in full_tokens if n > EMBED_MAX_TOKENS]

print(f"  임베딩 모델 상한 : {EMBED_MAX_TOKENS} 토큰 ({EMBED_TOKENIZER})")
print(f"  상세 토큰 분포   : {dist(full_tokens)}")
print(f"  상한 초과        : {len(over)}/{len(full_tokens)}건 "
      f"({len(over) / len(full_tokens) * 100:.0f}%)\n")


# ═══════════════════════════════════════════════ ②③ 자른다
print("=" * 74)
print("② 2단 구조 ― 사람이 만든 경계로 자르고, 넘치는 것만 다시 자른다")
print("=" * 74)
print(f"  설정: CHUNK_SIZE {CHUNK_SIZE} · OVERLAP {CHUNK_OVERLAP} · "
      f"PREFIX_BUDGET {PREFIX_BUDGET} -> 다시 자를 문턱 {RESPLIT_OVER}")
print("  (prep/options.py 에 있다. 이 파일에는 숫자가 없다)\n")

# 🔴 이 한 줄이 자르기의 전부다. 어떻게 자르는지는 prep/chunking.py 가 안다
sections, chunks, n_resplit = chunking.split_details(details)

section_tokens = [section["n_tokens"] for section in sections]
chunk_tokens = [ntok(chunk["body"]) for chunk in chunks]
print(f"  {'':14s}{'개수':>8s}   분포")
print(f"  0단 (통째로)  {len(full_tokens):>8,}   {dist(full_tokens)}")
print(f"  1단 (섹션)    {len(sections):>8,}   {dist(section_tokens)}")
print(f"  2단 (조각)    {len(chunks):>8,}   {dist(chunk_tokens)}")
print(f"  다시 자른 섹션: {n_resplit}개 / {len(sections):,}개\n")

example = next(chunk for chunk in chunks if chunk["section"] == "주의사항")
print("③ 문맥 유지 ― 조각 앞에 제목과 섹션명을 붙인다")
print(f"  붙이기 전: {example['body'][:46]}...")
print(f"  붙인 뒤  : {example['text'][:46]}...\n")


# ═══════════════════════════════════════════════ ④ 저장
# 🔴 이 한 줄이 저장의 전부다. 어떻게 넣는지는 prep/storage.py 가 안다
storage.save_sections_and_chunks(con, sections, chunks)

stored = [n for (n,) in con.execute("SELECT n_tokens FROM chunks")]
print("=" * 74)
print("④ 저장 ― sections · chunks")
print("=" * 74)
print(f"  sections {len(sections):>6,}행")
print(f"  chunks   {len(chunks):>6,}행  ·  접두어까지 넣은 토큰 {dist(stored)}")
print(f"  상한({EMBED_MAX_TOKENS}) 초과: {sum(n > EMBED_MAX_TOKENS for n in stored)}개")
con.close()
