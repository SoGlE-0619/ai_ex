# axi-ai

화장품 쇼핑몰 데이터(CSV)를 **SQLite 데이터베이스**로 만들고,
그 안의 글을 **벡터**로 바꿔서 **고객 맞춤 추천**과 **질문 검색**을 하는 프로젝트입니다.

---

## 1. 전체 그림

```
data/*.csv
    │  01_schema.py   컬럼 타입·PK·FK를 추측해서 테이블을 만든다
    ▼
cosmetic.db  (customers · products · purchases · product_details)
    │  02_chunk.py    긴 상품 상세를 섹션 → 조각으로 자른다
    ▼
    +  sections · chunks
    │  03_embed.py    조각·상품·고객·후기를 벡터로 바꿔 저장한다
    ▼
    +  chunk_vectors · product_vectors · customer_vectors · review_vectors
    │  04_verify.py   개수·차원·토큰·추천 정확도를 검사한다
    ▼
app/   ← 만들어 둔 DB만 읽어서 검색·추천을 한다
```

앞의 네 단계(`pipeline/`)는 **한 번 돌리고 끝나는 준비 작업**이고,`app/`은 그 결과를 **계속 읽어 쓰는 서비스 코드**입니다.
이 둘을 가른 것이 폴더 구조의 전부입니다.

---

## 2. 폴더 구조

```
ai_tutor/
├── app/                          서비스 코드 (DB를 읽기만 한다)
│   ├── core/                       아래층 — 아무도 이 폴더 밖을 모른다
│   │   ├── config.py                 경로·모델 이름·숫자 설정
│   │   ├── db.py                     SQLite 조회 창구
│   │   └── embedder.py               임베딩 모델을 만드는 유일한 자리
│   └── features/                   위층 — 기능
│       ├── profile.py                고객 정보 조회 (SQL만, 벡터 없음)
│       ├── searching.py              벡터로 찾기 (조각 검색·상품 추천)
│       └── retrieve.py               위 셋을 한 이름 아래 모으는 창구
│
├── pipeline/                     데이터를 만드는 코드 (한 번 돌리고 끝)
│   ├── 01_schema.py                CSV → 테이블
│   ├── 02_chunk.py                 상세 글 → 섹션·조각
│   ├── 03_embed.py                 글 → 벡터
│   ├── 04_verify.py                결과 검사
│   ├── 05_lookup_bench.py          딕셔너리 캐시 vs 매번 SELECT 속도 비교
│   └── prep/                       위 파일들이 부르는 실제 작업 함수
│       ├── options.py                조각을 자를 때 쓰는 값들
│       ├── chunking.py               자르기 (DB를 모른다)
│       ├── storage.py                넣기 (자르는 법을 모른다)
│       ├── embedding.py              무엇을 어떤 글로 적어 벡터로 만드나
│       └── verifying.py              검사 함수 모음
│
├── data/                         원본 CSV
│   ├── customers.csv
│   ├── products.csv
│   ├── product_details.csv
│   └── purchases.csv
│
├── try_customer.py               리팩터링 전 실습 스크립트 (한 파일에 다 있음)
├── try_profile.py                리팩터링 전 실습 스크립트 (한 파일에 다 있음)
└── cosmetic.db                   01~03을 돌리면 생기는 결과물
```

---

## 3. 두 갈래 — `app/` 과 `pipeline/`

|           | `app/`                | `pipeline/`                 |
| --------- | --------------------- | --------------------------- |
| 언제 도나 | 서비스가 떠 있는 내내 | 데이터를 새로 만들 때 한 번 |
| DB를      | 읽는다                | 만들고 쓴다                 |
| 배포할 때 | 따라간다              | 따라가지 않는다             |

여기서 규칙 하나가 나옵니다.

> **`pipeline/` → `app/` 은 되고, `app/` → `pipeline/` 은 안 된다.**

`app/`은 `pipeline/` 없이도 떠야 하기 때문입니다.
그래서 둘이 **같이 쓰는 것**(설정·DB 연결·임베딩 모델)은 전부 `app/core/`에 있습니다.

`app/` 안에서도 층이 한 번 더 갈립니다.

```
app/features/   ← 여러 파일이 있고, 서로를 부르지 않는다
      │ import
      ▼
app/core/       ← 아무도 가져다 쓰지 않는 아래층
```

`core/`가 `features/`를 import 하는 일은 없습니다. 화살표가 한 방향이라 **순환 import가 생길 수 없습니다.**

---

## 4. 용어 미리 알기

| 용어                   | 쉬운 설명                                                               |
| ---------------------- | ----------------------------------------------------------------------- |
| **테이블(Table)**      | 엑셀의 시트 한 장. CSV 파일 하나가 테이블 하나가 됩니다.                |
| **컬럼(Column)**       | 엑셀의 세로 열. `name`, `price` 같은 항목 이름.                         |
| **행(Row)**            | 엑셀의 가로 줄. 데이터 한 건.                                           |
| **타입(Type)**         | 그 컬럼에 들어가는 값의 종류 (숫자인지, 글자인지, 날짜인지).            |
| **기본키(PK)**         | 각 행을 하나로 구분해주는 컬럼. 예: `customer_id`.                      |
| **외래키(FK)**         | 다른 테이블을 가리키는 컬럼. 예: `purchases.customer_id` → `customers`. |
| **스키마(Schema)**     | 테이블의 설계도. "어떤 컬럼이 무슨 타입으로 있는가".                    |
| **토큰(Token)**        | 모델이 글을 세는 단위. 글자 수와는 다릅니다.                            |
| **섹션(Section)**      | 상품 상세 글을 `## 제목` 기준으로 나눈 덩어리. 사람이 만든 경계.        |
| **조각(Chunk)**        | 섹션을 모델이 삼킬 수 있는 크기로 다시 자른 것. 검색의 최소 단위.       |
| **임베딩(Embedding)**  | 글 한 덩어리를 숫자 목록(벡터)으로 바꾸는 것.                           |
| **벡터(Vector)**       | 그 숫자 목록. 이 프로젝트에서는 실수 384개.                             |
| **유사도(Similarity)** | 벡터 두 개가 얼마나 가까운지. 클수록 의미가 비슷합니다.                 |

---

## 5. `app/` - 서비스가 쓰는 코드

### 5-1. `app/core/config.py` - 설정

전체가 함께 쓰는 값을 한곳에 모읍니다. 값이 바뀌면 여기만 고칩니다.

| 이름               | 설명                                                |
| ------------------ | --------------------------------------------------- |
| `ROOT`             | 프로젝트 최상위 경로                                |
| `DATA_DIR`         | 원본 CSV 폴더                                       |
| `DB_PATH`          | SQLite DB 파일 경로                                 |
| `EMBED_TOKENIZER`  | 토큰 수를 셀 때 쓸 토크나이저 이름                  |
| `EMBED_MAX_TOKENS` | 임베딩 모델이 한 번에 받는 최대 토큰 수 (512)       |
| `EMBED_MODEL`      | 임베딩 모델 이름 (`intfloat/multilingual-e5-small`) |
| `EMBED_DIM`        | 벡터 하나에 들어가는 실수의 개수 (384)              |
| `EMBED_DECIMALS`   | 벡터를 글자로 적을 때 소수점 자릿수 (6)             |

이 파일은 아무것도 import 하지 않습니다. **의존성이 0인 유일한 파일**입니다.

### 5-2. `app/core/db.py` — DB 조회 창구

**`query(sql, params)`** — 여러 줄을 튜플 목록으로 꺼냅니다.

**`one(sql, params)`** — 한 줄만 꺼냅니다. 없으면 `None`.

**`dicts(sql, params)`** — 컬럼 이름이 붙은 딕셔너리 목록으로 꺼냅니다.

**`load_vectors(table, key, connection=None)`** — 글자로 넣어 둔 벡터를 NumPy 행렬로 되살립니다.

- 반환값: `(아이디 목록, (행 수 × 384) 행렬)`
- `connection`을 주면 그 연결을, 생략하면 `db.py`의 기본 연결을 씁니다.

**`load_documents(sql, params)`** — SQL 결과를 LangChain `Document` 목록으로 바꿉니다.

- 규약: 첫 컬럼이 id, 둘째가 본문, 셋째가 벡터 글자, 나머지는 metadata.

> **지연 import**: `numpy`는 `load_vectors` 안에서, `Document`는 `load_documents` 안에서 불러옵니다.
> 파일 맨 위에 두면 SELECT만 하는 파일(`profile.py`)까지 무거운 라이브러리를 같이 올리게 됩니다.

### 5-3. `app/core/embedder.py` — 임베딩 모델을 만드는 유일한 자리

**`get_embeddings()`** — 글을 벡터로 바꾸는 모델. 처음 부를 때 한 번만 올리고 재사용합니다.

이 파일이 왜 여기 있는지가 이번 구조 변경의 핵심입니다.

- **왜 한 벌인가** — 예전에는 앱과 파이프라인이 각자 모델을 만들었습니다. 한쪽만 조건이 바뀌면
  질문 벡터와 문서 벡터가 서로 다른 기준으로 만들어지고, **오류 없이 검색 결과만 이상해집니다.**
  주석으로 "같은 조건으로 만들자"고 약속하는 대신 같은 함수를 부르게 했습니다.
- **왜 `app/`인가** — 앱은 파이프라인 없이도 떠야 하므로 `app/ → pipeline/` 화살표를 만들 수 없습니다.
- **왜 `core/`인가** — `features/`의 여러 파일이 이 모델을 씁니다. 그중 한 파일에 두면 나머지가
  그 파일을 import 해야 하고, 서로 부르는 고리가 생겨 `ImportError`로 죽습니다.

| 이 모델을 쓰는 곳            | 부르는 함수       | 무엇을                 |
| ---------------------------- | ----------------- | ---------------------- |
| `app/features/searching.py`  | `embed_query`     | 질문 하나를 그때그때   |
| `pipeline/prep/embedding.py` | `embed_documents` | 문서 수천 개를 한 번에 |

### 5-4. `app/features/profile.py` — 고객 정보 조회 (SQL만)

**`customer_list(limit=None)`** — 고객 목록과 각자의 구매 건수.

**`dashboard(customer_id)`** — 한 고객에 대해 아는 것을 전부 모읍니다. 없는 고객이면 `None`.

- 반환값: 프로필 · 평균 별점 · 총 구매액 · 카테고리별 건수 · 구매 목록

**이 파일은 벡터를 쓰지 않습니다.** `db.dicts` 하나만 알면 됩니다.

- "이 고객이 무엇을 몇 건 샀나"는 SQL이 정확한 답을 줍니다. 벡터는 "대충 이쪽"밖에 못 합니다.
  **질문의 종류가 도구를 정합니다.**
- 임베딩 모델도 벡터 테이블도 필요 없으므로, 화면이 안 뜰 때 원인을 찾을 범위가 절반으로 줄어듭니다.
  실제로 벡터 표 넷을 지운 DB로 `dashboard("C001")`은 그대로 돌았고, `searching.py`는 import 하는 순간 `no such table: product_vectors`로 터졌습니다.

### 5-5. `app/features/searching.py` - 벡터로 찾기

**`get_chunk_store()`** — 조각 벡터스토어. DB에 저장해 둔 벡터를 그대로 올립니다(다시 임베딩하지 않습니다).

**`search_chunks(question, k=4, product_ids_only=None)`** — 질문과 의미가 가까운 조각을 찾고,
그 조각이 속한 **원문 섹션 전체**를 돌려줍니다(small-to-big).

**`rank_products(customer_id, n=5)`** — 고객 벡터와 가까운 상품 n개를 점수와 함께 돌려줍니다.

> 이 파일은 맨 위 두 줄에서 `load_vectors`를 실행합니다.
> 그래서 `03_embed.py`로 벡터를 만들기 전에는 **import 하는 것만으로 오류가 납니다.**
> `profile.py`를 따로 가른 이유가 이것입니다.

### 5-6. `app/features/retrieve.py` - 창구

`embedder` · `profile` · `searching`의 이름을 한곳에 모아 `__all__`로 내보냅니다.
**로직이 한 줄도 없습니다.**

밖에서는 `from app.features.retrieve import ...` 한 줄만 쓰면 되므로,
나중에 몸통을 다시 쪼개도 부르는 쪽은 안 바뀝니다.
"공개된 이름"과 "그 이름이 사는 파일"은 다른 물건이고, 뒤엣것만 바꾸면 됩니다.

지금은 이 파일이 **동작 확인 수단**이기도 합니다.

```bash
python -m app.features.retrieve
```

`searching.py`나 `profile.py`를 고쳤으면 이 한 줄을 돌려서 출력이 그대로인지 봅니다.
리팩터링이 됐다는 기준은 하나뿐입니다 — **동작이 안 바뀌는 것.**

---

## 6. `pipeline/` — 데이터를 만드는 코드

번호가 붙은 파일과 `prep/`의 역할이 정확히 나뉩니다.

|             | 하는 일                                                     |
| ----------- | ----------------------------------------------------------- |
| `01_`~`05_` | **순서를 정하고 숫자를 보여 준다.** 실제 계산은 하지 않는다 |
| `prep/*.py` | **실제 일을 한다.** 혼자서는 실행되지 않는다                |

### 6-1. `01_schema.py` — CSV를 DB로

```
[1] DATA_DIR 안의 모든 CSV 찾기
[2] read_csv() 로 컬럼명과 행 읽기
[3] infer_type() / infer_pk() 로 타입과 기본키 추측
[4] 결과를 tables 딕셔너리에 모으기
[5] owner_of() 로 외래키 관계 찾기
[6] sort_by_dependency() 로 부모 테이블부터 처리할 순서 만들기
[7] build_create() 로 CREATE TABLE 실행
[8] convert() 로 값을 타입에 맞게 바꾸고 INSERT
[9] FK 컬럼에 인덱스를 만들고 commit
```

| 함수                         | 하는 일                                                         |
| ---------------------------- | --------------------------------------------------------------- |
| `read_csv(path)`             | CSV 하나를 읽어 `(컬럼명 목록, 행 목록)` 반환                   |
| `looks_int(text)`            | 정수로 저장해도 되는 문자열인지                                 |
| `looks_float(text)`          | 소수로 저장해도 되는 문자열인지                                 |
| `looks_date(text)`           | `YYYY-MM-DD` 형식인지                                           |
| `infer_type(values)`         | 한 컬럼 전체를 보고 타입 결정 (`INTEGER`/`FLOAT`/`DATE`/`TEXT`) |
| `infer_pk(columns, rows)`    | `_id`로 끝나고, 빈 값이 없고, 값이 전부 다른 컬럼을 PK로        |
| `owner_of(column, tables)`   | FK 후보가 어느 테이블을 가리키는지                              |
| `build_create(name, table)`  | `CREATE TABLE` SQL 문자열 만들기                                |
| `sort_by_dependency(tables)` | 부모 테이블이 먼저 만들어지도록 정렬                            |
| `convert(value, kind)`       | CSV의 글자를 타입에 맞는 파이썬 값으로                          |

> `sort_by_dependency`가 필요한 이유: `purchases`가 `customers`를 참조하는데
> `customers`가 아직 없으면 테이블을 만들 수 없습니다.
>
> `convert`가 필요한 이유: CSV는 모든 값이 글자입니다. `"25400"`을 숫자 `25400`으로 바꿔야
> DB에서 계산과 정렬이 제대로 됩니다.

### 6-2. `02_chunk.py` + `prep/options.py` · `prep/chunking.py` · `prep/storage.py`

`02_chunk.py`에는 **자르는 코드가 없습니다.** 상세 글을 SQL로 가져와 두 줄을 부르고,
나머지는 전부 **숫자를 보여 주는 코드**입니다.

```python
sections, chunks, n_resplit = chunking.split_details(details)   # 자르기 전부
storage.save_sections_and_chunks(con, sections, chunks)         # 저장 전부
```

화면에 네 단계가 찍힙니다.

```
① 왜 자르나      상세 200건 중 184건(92%)이 상한 512토큰을 넘는다
② 2단 구조       0단 통째로 200 → 1단 섹션 1,560 → 2단 조각 1,560
③ 문맥 유지      조각 앞에 [상품명 > 섹션] 을 붙이기 전 / 붙인 뒤
④ 저장          sections·chunks 행 수와, 상한 초과 0개 확인
```

> `dist()`는 `최소 / 중앙 / 최대` 한 줄을 만드는 **출력 서식 함수**라 이 파일에 있습니다.
> `chunking.py`가 화면에 어떻게 보일지까지 알게 되면 그게 규칙 위반입니다.
> 토큰을 세는 `ntok`은 `chunking.count_tokens`를 가리키는 별칭일 뿐, 여기서 다시 만들지 않습니다.

> **주의:** `save_sections_and_chunks()`는 `chunk_vectors` 테이블을 함께 지웁니다.
> 조각을 새로 만들면 옛 벡터의 `chunk_id`가 어긋나기 때문입니다.
> **02를 다시 돌렸으면 03도 다시 돌려야 합니다.**

**`prep/options.py`** — 실습에서 **손대는 건 여기뿐입니다.**

| 값              | 뜻                                                                            |
| --------------- | ----------------------------------------------------------------------------- |
| `CHUNK_SIZE`    | 조각 하나의 토큰 상한 (384)                                                   |
| `CHUNK_OVERLAP` | 경계에서 겹치는 몫 (48)                                                       |
| `PREFIX_BUDGET` | 접두어 `[상품명 > 섹션]`이 쓸 토큰 자리 (32)                                  |
| `RESPLIT_OVER`  | 다시 자를 문턱 — `EMBED_MAX_TOKENS - PREFIX_BUDGET`으로 **계산해서** 잡습니다 |
| `HEADERS`       | 섹션 경계로 볼 마크다운 표시 (`##`)                                           |
| `SEPARATORS`    | 다시 자를 때 쓸 구분자 순서                                                   |

**`prep/chunking.py`** - 자릅니다. **이 파일에는 `import sqlite3`가 없습니다.**

| 함수                                        | 하는 일                                        |
| ------------------------------------------- | ---------------------------------------------- |
| `get_tokenizer()`                           | 토크나이저를 한 번만 올린다                    |
| `count_tokens(text)`                        | 글의 토큰 수                                   |
| `with_context(product_name, section, body)` | 조각 앞에 `[상품명 > 섹션]` 접두어를 붙인다    |
| `split_sections(details)`                   | 1단 — `## 제목` 같은 사람이 만든 경계로 자른다 |
| `split_chunks(sections)`                    | 2단 — 상한을 넘는 것만 다시 자른다             |
| `split_details(details)`                    | 위 둘을 순서대로 부른다                        |

- 들어오는 것: `[(상품번호, 상품명, 상세 원문), ...]` - 그냥 파이썬 목록
- 나가는 것: `(섹션 목록, 조각 목록, 다시 자른 횟수)` - 튜플이 아니라 **딕셔너리** 목록입니다.
  `storage.py`가 `chunking.py`를 안 읽고도 무엇이 오는지 알 수 있어야 하기 때문입니다.
- **DB를 모르므로 DB 없이 시험할 수 있습니다.** 숫자도 없습니다(전부 `options.py`).

**`prep/storage.py`** - 넣습니다. **스플리터를 부르지 않습니다.**

| 함수                                                      | 하는 일                                             |
| --------------------------------------------------------- | --------------------------------------------------- |
| `save_sections_and_chunks(con, sections, chunks)`         | `sections` · `chunks` 테이블을 만들고 넣는다        |
| `vector_to_text(vector)`                                  | 벡터를 `'[0.018827,-0.024955,...]'` 라는 **글자**로 |
| `save_vectors(con, kind, key, parent, ids, vectors, dim)` | `{kind}_vectors` 테이블을 만들고 넣는다             |

- 커넥션을 **밖에서 받습니다.** 이 파일은 `sqlite3.connect()`를 부르지 않습니다.
- 그래서 "조각이 이상하다"와 "저장이 이상하다"를 따로 볼 수 있습니다.
- `save_vectors`는 PK 타입을 손으로 적지 않고 부모 테이블의 `PRAGMA table_info`에서 읽어 옵니다.
  `chunks.chunk_id`는 INTEGER이고 `products.product_id`는 TEXT라서, 어긋나면
  **조인이 오류 없이 0건**이 됩니다.
- 벡터를 BLOB이 아니라 글자로 넣습니다. 크기는 두 배지만 `SELECT` 하면 눈에 보입니다.

### 6-3. `03_embed.py` + `prep/embedding.py`

`03_embed.py`의 여섯 단계:

```
1. DB에 연결하고 임베딩 모델을 준비한다
2. 검색에 쓸 텍스트를 만든다 (조각·상품·고객·후기)
3. targets 딕셔너리에 모은다  {종류: (ID 컬럼, 부모 테이블, ID 목록, 텍스트 목록)}
4. embed_documents() 로 벡터로 바꾼다
5. storage.save_vectors() 로 종류별 벡터 테이블에 저장한다
6. 개수·평균 글자 수·걸린 시간·초당 처리량을 출력한다
```

네 종류가 전부 같은 길을 지나갑니다.

| 종류       | 무엇을 벡터로                         | 만드는 표          |
| ---------- | ------------------------------------- | ------------------ |
| `chunk`    | `chunks.text` 그대로                  | `chunk_vectors`    |
| `product`  | `product_text()`로 만든 한 문장       | `product_vectors`  |
| `customer` | `customer_text()`로 만든 취향 한 문장 | `customer_vectors` |
| `review`   | 후기 한 건                            | `review_vectors`   |

**`prep/embedding.py`** — "무엇을 어떤 글로 적어 벡터로 만드나"만 다룹니다.

| 함수                                  | 하는 일                                               |
| ------------------------------------- | ----------------------------------------------------- |
| `product_text(row)`                   | 이름·브랜드·카테고리·가격·성분… 을 `·`로 이은 한 문장 |
| `top(values, n=3)`                    | 가장 자주 나온 값 n개를 `·`로 이어서                  |
| `customer_text(skin_type, purchases)` | 피부 타입 + 자주 산 카테고리·성분·고민 + 평균 별점    |
| `embed_documents(texts)`              | 글 목록 → `(벡터 목록, 걸린 시간)`                    |

> `customer_text`의 `purchases` 한 항목은 `(카테고리, 성분, 고민, 별점)` 순서입니다.
> **순서가 곧 약속**이라 `03_embed.py` 한쪽만 바꾸면 엉뚱한 칸을 읽고,
> 오류 없이 이상한 문장이 만들어집니다.

### 6-4. `04_verify.py` + `prep/verifying.py`

`04_verify.py`는 **검사 순서와 입력값**을, `verifying.py`는 **검사 방법**을 담당합니다.

```
1단계  테이블 개수와 FK 연결 상태          check_table_data()
2단계  벡터 차원과 모델 이름이 같은지        check_vector_data()
3단계  TEXT 저장 크기 vs BLOB 예상 크기     check_vector_storage()
4단계  토큰 상한을 넘는 조각이 있는지        check_token_sizes()
5단계  추천 방식 세 가지의 hit@1·3·5 비교   compare_recommendations()
6단계  예시 질문으로 검색 결과 눈으로 확인    inspect_search_results()
       발견한 문제를 모아 최종 출력          print_final_result()
```

`check(ok, error_message, problems)`가 실패한 검사를 `problems` 목록에 모으고,
마지막에 한꺼번에 보여 줍니다.

### 6-5. `05_lookup_bench.py`

「왜 딕셔너리에 담아 두나. 그냥 필요할 때 SELECT 하면 되지 않나」를 **재서** 답합니다.

- (A) 조각마다 `SELECT section_id FROM sections WHERE product_id=? AND section=?`
- (B) 딕셔너리에 담아 두고 꺼내 쓰기

DB를 읽기만 하므로, 지워도 파이프라인은 그대로 돕니다.

---

## 7. 이름이 비슷한 두 파일 — 주의

| 파일                         | 하는 일                                 | 성격 |
| ---------------------------- | --------------------------------------- | ---- |
| `app/core/embedder.py`       | **임베딩기(모델)를 만든다**             | 도구 |
| `pipeline/prep/embedding.py` | **무엇을 어떤 글로 적어 벡터로 만드나** | 작업 |

원래 둘 다 `embedding.py`였는데 헷갈려서 앞엣것을 `embedder.py`로 바꿨습니다.
`prep/embedding.py`는 모델을 직접 만들지 않고 `app.core.embedder.get_embeddings()`를 불러 씁니다.

---

## 8. 데이터 관계

```
customers (고객)              products (상품)
  customer_id (PK)              product_id (PK)
        ▲                             ▲
        │                             │
        └──────┬──────────────────────┘
               │
          purchases (구매)          product_details (상품 상세)
            purchase_id (PK)          product_id (PK, FK → products)
            customer_id (FK)
            product_id  (FK)
            is_holdout                 ← 1이면 정답용으로 숨겨 둔 최근 구매
```

- `customers.csv` — 고객 정보 (`customer_id`, `name`, `age`, `skin_type`, `city` 등)
- `products.csv` — 상품 정보 (`product_id`, `name`, `brand`, `price`, `ingredient`, `concern` 등)
- `product_details.csv` — 상품 상세 설명 (`product_id`, `detail`) ← 조각으로 잘리는 원본
- `purchases.csv` — 구매 내역 (`purchase_id`, `customer_id`, `product_id`, `rating`, `review`)

`customer_id`, `product_id`처럼 **다른 테이블의 PK와 이름이 같은 컬럼**을 `01_schema.py`가 찾아서 FK로 연결합니다.

`is_holdout = 1`인 구매는 학습에서 빼 두고 **추천이 맞았는지 채점하는 정답**으로 씁니다.
그래서 `03_embed.py`와 `profile.py`의 SQL에는 `WHERE is_holdout = 0`이 붙어 있습니다.

파생 테이블(01~03이 만듭니다): `sections`, `chunks`,
`chunk_vectors`, `product_vectors`, `customer_vectors`, `review_vectors`

---

## 9. 실행 방법

**반드시 프로젝트 루트에서** 순서대로 실행합니다.

```bash
python -m pipeline.01_schema        # CSV → cosmetic.db
python -m pipeline.02_chunk         # 상세 글 → 섹션·조각
python -m pipeline.03_embed         # 글 → 벡터 (로컬 CPU 기준 30초쯤)
python -m pipeline.04_verify        # 검사

python -m app.features.retrieve     # 앱 쪽이 도는지 확인
python -m pipeline.05_lookup_bench  # (선택) 속도 비교
```

02는 01 뒤에, 03은 02 뒤에 돌려야 합니다.
**02를 다시 돌리면 `chunk_vectors`가 지워지므로 03도 같이 돌려야 합니다.**

`options.py` 값만 바꿔 조각 크기를 실험할 때는 `02 → 03`만 다시 돌리면 되고,
01(CSV → 테이블)까지 갈 필요는 없습니다. 02와 03을 가른 이유도 이 값 차이입니다 —
조각을 다시 자르는 건 몇 초지만 벡터를 다시 만드는 건 30초쯤 걸리고,
상용 API를 쓰면 그대로 요금이 됩니다.

### 왜 `python pipeline/01_schema.py`가 아니라 `python -m` 인가요?

`-m`은 "파일을 직접 실행"이 아니라 **모듈로 불러와서 실행**하라는 뜻입니다.
이 방식을 쓰면 항상 루트에서 명령을 치게 되고, 거기서 두 가지 이점이 생깁니다.

**1) 매번 하위 폴더로 이동할 필요가 없습니다**

```bash
# 이렇게 왔다 갔다 할 필요 없이
cd pipeline
python 01_schema.py
cd ..

# 루트에 그대로 있으면서 실행
python -m pipeline.01_schema
```

터미널의 현재 위치가 항상 루트로 고정되므로, `config.py`의 `ROOT`·`DATA_DIR`·`DB_PATH` 같은
경로도 매번 같은 기준에서 동작합니다.

**2) 실수로 인한 잘못된 git commit을 막아줍니다**

터미널이 하위 폴더(`pipeline/`)에 들어가 있는 상태에서 아래처럼 커밋하면,
**그 폴더 안의 변경사항만** 커밋되고 상위 폴더(`app/`, `data/` 등)의 변경사항은 빠집니다.

```bash
cd pipeline
git add .        # ← pipeline/ 안의 변경사항만 스테이징됨
git commit -m "작업"
```

`git add .`의 `.`은 "저장소 전체"가 아니라 **"지금 있는 폴더 아래"** 를 뜻하기 때문입니다.

> 참고: `git status`나 옵션 없는 `git commit -m "..."`은 하위 폴더에서 실행해도 저장소 전체를 기준으로 동작합니다.
> 문제가 되는 건 위처럼 `.`(현재 폴더)을 경로로 넘기는 경우입니다.

### 실행 전 확인

- 터미널 프롬프트의 경로가 `.../ai_tutor` 인지 확인하세요.
- 모듈명에 `.py`는 붙이지 않습니다. (`pipeline.01_schema` ○ / `pipeline.01_schema.py` ✗)
- 폴더 구분은 `/`가 아니라 `.`을 씁니다. (`pipeline.01_schema` ○ / `pipeline/01_schema` ✗)

---

## 10. `try_customer.py` · `try_profile.py` — 리팩터링 전 원본

구조를 나누기 전에 **한 파일에 전부 적어 보던** 실습 스크립트입니다.
지금 코드와 비교하는 용도로 남겨 뒀습니다.

| `try_profile.py`                | 지금 어디에 있나                                         |
| ------------------------------- | -------------------------------------------------------- |
| 모델 생성 (8~13줄)              | `app/core/embedder.py` `get_embeddings()`                |
| 상품 문장 만들기 (20~33줄)      | `pipeline/prep/embedding.py` `product_text()`            |
| `top()` · `taste()` (110~130줄) | `pipeline/prep/embedding.py` `top()` · `customer_text()` |
| 고객 정보 SQL (53줄)            | `app/features/profile.py`                                |
| 벡터 유사도 정렬                | `app/features/searching.py` `rank_products()`            |

---

## 11. 수업 진행 순서 — 구조 변경을 설명할 때

파일을 여는 순서입니다. **의존성 아래층부터 위층으로** 올라갑니다.

### 도입 — 왜 바꿨나 (5분)

새 구조를 먼저 열지 않습니다. **`try_profile.py`(247줄)를 띄우고 10번 표를 보여 줍니다.**
직접 쓴 한 파일이 어디로 흩어졌는지가 그대로 오늘의 목차입니다.

### 1부 — 아래층 셋 (`app/core/`)

| 순서 | 파일                   | 여기서 할 이야기                                                             |
| ---- | ---------------------- | ---------------------------------------------------------------------------- |
| 1    | `app/core/config.py`   | 20줄, 의존성 0. 여기부터 봐야 뒤 파일들의 `import`가 설명 없이 읽힌다        |
| 2    | `app/core/db.py`       | 조회 창구 넷. `load_vectors` 안의 `import numpy` — **왜 함수 안에서 부르나** |
| 3    | `app/core/embedder.py` | **오늘의 핵심.** 왜 한 벌인가 / 왜 `app/`인가 / 왜 `core/`인가               |

여기서 한 번 끊고 화살표를 그립니다 — `pipeline → app`은 되고 `app → pipeline`은 안 된다.
이 한 방향이 구조의 전부입니다.

### 2부 — 위층 (`app/features/`)

| 순서 | 파일                        | 여기서 할 이야기                                           |
| ---- | --------------------------- | ---------------------------------------------------------- |
| 4    | `app/features/profile.py`   | 벡터를 안 쓴다. SQL만                                      |
| 5    | `app/features/searching.py` | 맨 위 두 줄이 import 시점에 실행된다                       |
| 6    | `app/features/retrieve.py`  | 로직 0줄, 창구뿐. `python -m app.features.retrieve`로 확인 |

**4·5는 붙여서 보여주고 바로 시연하세요.**
벡터 표 넷을 지운 DB 사본으로 `dashboard("C001")`은 돌고
`searching.py`는 import에서 `no such table`로 죽습니다.
"왜 갈랐나"를 말로 하는 것보다 이 화면 하나가 낫습니다.

### 3부 — 같은 규칙이 한 번 더 (`pipeline/`)

| 순서 | 파일                        | 여기서 할 이야기                             |
| ---- | --------------------------- | -------------------------------------------- |
| 7    | `pipeline/02_chunk.py`      | 자르는 코드가 없다. 두 줄을 부를 뿐          |
| 8    | `pipeline/prep/chunking.py` | `import sqlite3`가 없다 → DB 없이 시험된다   |
| 9    | `pipeline/prep/storage.py`  | 스플리터를 안 부른다 → 저장 문제만 따로 본다 |
| 10   | `pipeline/prep/options.py`  | 실습에서 손대는 건 여기뿐                    |

한 문장으로 정리됩니다 — **번호 붙은 파일은 순서와 숫자만, `prep/`은 실제 일, `options.py`는 값만.**

### 4부 — 이름 함정 (2분)

`app/core/embedder.py`(임베딩기를 만든다) vs `pipeline/prep/embedding.py`(무슨 글로 적을까).
7번 표를 띄우고, 실제로 헷갈려서 이름을 바꿨다는 사실까지 이야기합니다.

### 시간이 남으면

| 파일                                          | 이야기                                                  |
| --------------------------------------------- | ------------------------------------------------------- |
| `pipeline/03_embed.py`                        | 여섯 단계 흐름 주석이 이미 정리돼 있어 읽기만 해도 된다 |
| `pipeline/04_verify.py` + `prep/verifying.py` | 검사 **순서** / 검사 **방법** 분리 — 3부 규칙의 반복    |

### 수업 전 확인

- **`03_embed.py`가 돌아간 `cosmetic.db`가 있어야** 2부 시연이 됩니다.
- 벡터 표 삭제 시연은 **DB 사본**으로 하세요.
