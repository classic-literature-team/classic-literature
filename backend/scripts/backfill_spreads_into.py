"""일회성 마이그레이션: AbstractWork -[spreadsInto]-> Book 관계(edge) 백필.

배경
----
`AbstractWork -[spreadsInto]-> Book`(작품 → 이본) 관계가 극히 일부만
존재해, 대부분의 작품이 이본과 끊겨 있다. 조사로 검증된 id 규칙에 따라
누락된 관계를 채운다.

연결 규칙(검증 완료)
--------------------
- AbstractWork.id 는 'AW00' + stem 형태다(예: ``AW00UYJ01``).
- 해당 작품의 이본 Book.id 는 'B' + stem + ... 형태다(예: ``BUYJ01NU001``).
- 즉 AbstractWork.id 에서 접두 'AW00' 을 제거한 stem 에 대해,
  Book.id 가 ``'B' + stem`` 으로 시작하면 그 작품↔이본은 연결된다.

안전 장치
---------
- 접두는 정확히 'AW00' 만 제거한다. 'AW00' 으로 시작하지 않는 작품은
  규칙을 적용하지 않고(임의 추측 금지) 로그로 남긴 뒤 건너뛴다.
- 한 Book 이 두 개 이상의 작품 stem 에 매칭되면(모호) 잘못된 연결을
  막기 위해 해당 Book 을 건너뛰고 로그로 남긴다.
- 기존 (source_id, target_id, relation='spreadsInto', target_class='Book')
  쌍을 미리 읽어 중복 삽입을 방지한다 → 재실행해도 안전(idempotent).

동작 모드
---------
- 기본(dry-run): 삽입될 건수/샘플만 출력하고 **commit 하지 않는다**.
- ``--apply``: 실제로 Edge 를 삽입하고 commit 한다.

이 스크립트는 오직 INSERT 만 수행한다. 기존 데이터를 update/delete 하지 않는다.
삽입한 edge 는
``relation='spreadsInto' AND source_class='AbstractWork' AND target_class='Book'``
조건으로 식별 가능하므로, 문제가 생기면 그 조건으로 삭제해 되돌릴 수 있다.

실행 예
-------
    # backend/ 디렉터리에서
    #   dry-run
    .\\.venv\\Scripts\\python.exe scripts\\backfill_spreads_into.py
    #   실제 삽입
    .\\.venv\\Scripts\\python.exe scripts\\backfill_spreads_into.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 이 스크립트는 backend/scripts/ 아래의 독립 실행 스크립트다.
# `python scripts/backfill_spreads_into.py` 로 실행할 때 backend/ 를
# import 경로에 넣어 app 패키지를 찾을 수 있게 한다.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import AbstractWork, Book, Edge  # noqa: E402

WORK_ID_PREFIX = "AW00"
RELATION = "spreadsInto"
SOURCE_CLASS = "AbstractWork"
TARGET_CLASS = "Book"


class BackfillResult:
    """dry-run / apply 공용 집계 결과."""

    def __init__(self) -> None:
        self.new_pairs: list[tuple[AbstractWork, Book]] = []
        self.skipped_existing = 0
        self.skipped_non_prefix_works: list[str] = []
        self.ambiguous_books: list[tuple[str, list[str]]] = []
        self.unmatched_books: list[str] = []


def compute_backfill(db: Session) -> BackfillResult:
    """규칙에 따라 삽입할 (작품, 이본) 쌍을 계산한다. DB 를 변경하지 않는다."""
    result = BackfillResult()

    works = list(db.scalars(select(AbstractWork)))
    books = list(db.scalars(select(Book)))

    # stem -> work. 'AW00' 으로 시작하지 않는 작품은 규칙 미적용.
    stem_to_work: dict[str, AbstractWork] = {}
    for work in works:
        if not work.id.startswith(WORK_ID_PREFIX):
            result.skipped_non_prefix_works.append(work.id)
            continue
        stem = work.id[len(WORK_ID_PREFIX) :]
        stem_to_work[stem] = work

    # 기존 spreadsInto(AbstractWork->Book) 쌍 집합 → 중복 방지 / idempotent.
    existing_rows = db.execute(
        select(Edge.source_id, Edge.target_id).where(
            Edge.relation == RELATION,
            Edge.source_class == SOURCE_CLASS,
            Edge.target_class == TARGET_CLASS,
        )
    ).all()
    existing_pairs: set[tuple[str, str]] = {(s, t) for s, t in existing_rows}

    stems = list(stem_to_work.keys())
    for book in books:
        # Book.id 가 'B'+stem 으로 시작하는 stem 들을 찾는다.
        matched_stems = [s for s in stems if book.id.startswith("B" + s)]

        if not matched_stems:
            result.unmatched_books.append(book.id)
            continue
        if len(matched_stems) > 1:
            # 모호: 잘못된 연결을 막기 위해 건너뛴다.
            result.ambiguous_books.append((book.id, matched_stems))
            continue

        work = stem_to_work[matched_stems[0]]
        pair = (work.id, book.id)
        if pair in existing_pairs:
            result.skipped_existing += 1
            continue
        result.new_pairs.append((work, book))

    return result


def build_edges(pairs: list[tuple[AbstractWork, Book]]) -> list[Edge]:
    """(작품, 이본) 쌍을 새 Edge 로 변환한다. id 는 넣지 않는다(autoincrement)."""
    edges: list[Edge] = []
    for work, book in pairs:
        edges.append(
            Edge(
                source_class=SOURCE_CLASS,
                source_id=work.id,
                source_name=work.name,
                target_class=TARGET_CLASS,
                target_id=book.id,
                target_name=book.name,
                relation=RELATION,
            )
        )
    return edges


def print_report(result: BackfillResult, *, apply: bool) -> None:
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"=== spreadsInto 백필 [{mode}] ===")
    print(f"새로 추가될 edge 건수      : {len(result.new_pairs)}")
    print(f"이미 존재해 건너뛴 수      : {result.skipped_existing}")
    print(
        "규칙 미적용(AW00 아님) 작품 : "
        f"{len(result.skipped_non_prefix_works)} "
        f"{result.skipped_non_prefix_works[:10]}"
    )
    print(f"모호 매칭 Book 건수        : {len(result.ambiguous_books)}")
    for book_id, stems in result.ambiguous_books[:10]:
        print(f"  - 모호 Book {book_id} -> stems {stems}")
    print(f"어떤 작품과도 매칭 안 된 Book: {len(result.unmatched_books)}")
    for book_id in result.unmatched_books[:10]:
        print(f"  - 미매칭 Book {book_id}")

    print("샘플(최대 10건):")
    for work, book in result.new_pairs[:10]:
        print(f"  {work.id} ({work.name}) -[spreadsInto]-> {book.id} ({book.name})")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AbstractWork -[spreadsInto]-> Book 관계 백필 (기본 dry-run)."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="실제로 edge 를 삽입하고 commit 한다. 없으면 dry-run.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = compute_backfill(db)
        print_report(result, apply=args.apply)

        if not args.apply:
            print(
                "\n[dry-run] 커밋하지 않았습니다. "
                "실제 삽입하려면 --apply 를 붙이세요."
            )
            return 0

        if not result.new_pairs:
            print("\n[apply] 추가할 신규 edge 가 없습니다(이미 최신 상태).")
            return 0

        edges = build_edges(result.new_pairs)
        db.add_all(edges)
        db.commit()
        print(
            f"\n[apply] {len(edges)}건의 spreadsInto edge 를 "
            "삽입하고 commit 했습니다."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
