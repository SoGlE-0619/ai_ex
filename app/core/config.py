from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = ROOT / "data"
DB_PATH = str(ROOT / "cosmetic.db")


EMBED_TOKENIZER = "intfloat/multilingual-e5-small"
EMBED_MAX_TOKENS = 512
EMBED_MODEL = "intfloat/multilingual-e5-small"

# 백터차원 : 임베딩된 문자열 좌표값 갯수
EMBED_DIM = 384
EMBED_DECIMALS = 6

if not Path(DB_PATH).exists():
    print(f"알림: DB 가 아직 없다 -> {DB_PATH}")



