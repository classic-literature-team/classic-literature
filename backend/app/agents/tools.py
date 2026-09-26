"""에이전트가 사용하는 tool calling 함수.

한국한문소설 시맨틱 데이터(20개 클래스 · 42종 관계)를 조회하는 단일
도구를 정의한다. @function_tool 데코레이터가 함수의 타입 힌트와
docstring을 읽어 LLM이 이해할 수 있는 tool 명세로 자동 변환하므로,
docstring이 곧 "이 도구를 언제 어떻게 쓸지" 알려주는 설명서가 된다.

설계 원칙
---------
1. 하나의 함수로 통합한다.
   질의 유형마다 함수를 따로 두면 tool 개수가 계속 늘어나고, LLM이
   "어느 함수를 쓸지" 판단하는 단계에서 오류가 생긴다. 클래스 선택과
   조건 지정을 파라미터로 흡수해 함수 하나로 처리한다.

2. 관계를 함께 반환한다.
   시맨틱 데이터의 요체는 노드의 속성값이 아니라 노드 사이의 의미적
   관계에 있다. 따라서 조회 결과에는 연결된 이웃 노드와 그 관계명을
   한국어 의미와 함께 표시한다.

3. steps 유무로 동작을 가른다.
   steps가 비면 단일 클래스 조회, steps를 지정하면 관계를 따라
   이동하는 경로 탐색이 된다.
"""

from agents import function_tool
from sqlalchemy import String, Text, and_, func, or_, select

from app.db.session import SessionLocal
from app.models import (
    AbstractWork,
    Allusion,
    BackgroundE,
    BackgroundL,
    BackgroundW,
    Book,
    Caste,
    Character,
    ChElements,
    Comment,
    Edge,
    EmbeddedWork,
    Episode,
    Number,
    Participant,
    RelatedWork,
    Remark,
    Review,
    Scene,
    SideDot,
    WorksCompilation,
)

# ---------------------------------------------------------------------------
# 매핑 정의
# ---------------------------------------------------------------------------

# LLM이 사용할 테이블 키 → SQLAlchemy 모델
MODELS = {
    # 서지적 요소
    "book": Book,
    "abstract_work": AbstractWork,
    "works_compilation": WorksCompilation,
    "participant": Participant,
    # 참여적 요소
    "review": Review,
    "side_dot": SideDot,
    "related_work": RelatedWork,
    # 표현적 요소
    "embedded_work": EmbeddedWork,
    "allusion": Allusion,
    # 배열적 요소
    "scene": Scene,
    "character": Character,
    "caste": Caste,
    "ch_elements": ChElements,
    "comment": Comment,
    "remark": Remark,
    "number": Number,
    "episode": Episode,
    "background_e": BackgroundE,
    "background_l": BackgroundL,
    "background_w": BackgroundW,
}

# Edge 테이블의 sourceClass/targetClass 표기 ↔ 테이블 키
CLASS_TO_KEY = {
    "Book": "book",
    "AbstractWork": "abstract_work",
    "WorksCompilation": "works_compilation",
    "Participant": "participant",
    "Review": "review",
    "SideDot": "side_dot",
    "RelatedWork": "related_work",
    "EmbeddedWork": "embedded_work",
    "Allusion": "allusion",
    "Scene": "scene",
    "Character": "character",
    "Caste": "caste",
    "ChElements": "ch_elements",
    "Comment": "comment",
    "Remark": "remark",
    "Number": "number",
    "Episode": "episode",
    "BackgroundE": "background_e",
    "BackgroundL": "background_l",
    "BackgroundW": "background_w",
}
KEY_TO_CLASS = {v: k for k, v in CLASS_TO_KEY.items()}

# 관계명의 한국어 의미. 결과에 함께 표기해 의미 기반 해석을 돕는다.
RELATION_KOR = {
    "contains": "보유한다",
    "possess": "요소로 지닌다",
    "isPositionedAs": "신분에 위치한다",
    "commentsOn": "평비가 결부된다",
    "creates": "창작한다",
    "isTheSameAs": "동일 단위이다",
    "hasPart": "하위로 포함한다",
    "spreadsInto": "이본으로 확산된다",
    "edits": "편찬한다",
    "quotes": "전고를 인용한다",
    "sameEditionAs": "동일 이본 계열이다",
    "isAMotifFor": "모티프가 된다",
    "includes": "수록한다",
    "derived": "전고에서 유래한다",
}

# 장문 컬럼. 기본적으로 잘라서 반환한다.
LONG_COLS = {
    "original_text",
    "translation",
    "con_information",
    "contents_information",
}


# ---------------------------------------------------------------------------
# 내부 보조 함수
# ---------------------------------------------------------------------------


def _apply_filters(model, stmt, filters):
    """filters를 SQL 조건으로 변환한다.

    한 컬럼에 세미콜론으로 구분된 복수 값이 오면 OR로, 서로 다른
    컬럼끼리는 AND로 묶는다. 숫자 컬럼에는 ilike를 쓸 수 없으므로
    컬럼 타입을 확인해 등호 비교로 분기한다.
    """
    for column, raw in filters.items():
        if not hasattr(model, column):
            cols = [c.name for c in model.__table__.columns]
            raise ValueError(f"'{column}' 컬럼이 없습니다. 사용 가능: {cols}")

        col = getattr(model, column)
        values = [v.strip() for v in str(raw).split(";") if v.strip()]
        if not values:
            continue

        if isinstance(col.type, (String, Text)):
            stmt = stmt.where(or_(*[col.ilike(f"%{v}%") for v in values]))
        else:
            stmt = stmt.where(or_(*[col == v for v in values]))

    return stmt


def _render(row, brief=True):
    """레코드 한 건을 텍스트로 펼친다. 빈 값은 건너뛴다.

    원문·번역 등 장문 컬럼도 자르지 않고 전문을 그대로 반환한다.
    (brief 인자는 호출부 호환을 위해 남겨두되 더 이상 축약에 쓰이지 않는다.)
    """
    out = []
    for c in row.__table__.columns:
        value = getattr(row, c.name)
        if value is None or str(value).strip() == "":
            continue
        out.append(f"{c.name}: {value}")
    return ", ".join(out)


def _serialize_row(row):
    """레코드 한 건을 근거(trace)용 {컬럼명: 값(str)} 딕셔너리로 직렬화한다.

    LLM용 텍스트를 만드는 ``_render``와 마찬가지로, 프론트 미리보기 표의 원천
    데이터를 만든다. 규칙:
    - 값이 None이거나 공백뿐인 컬럼은 제외한다(비어있지 않은 컬럼만).
    - 원문·번역 등 장문 컬럼도 자르지 않고 전문을 그대로 담는다.
    - ``id``는 (비어있지 않다면) 자연히 포함되며, 병합 시 중복 제거 키로 쓰인다.
    """
    out: dict[str, str] = {}
    for c in row.__table__.columns:
        value = getattr(row, c.name)
        if value is None or str(value).strip() == "":
            continue
        out[c.name] = str(value)
    return out


def _describe_all():
    """전체 클래스 목록과 42종 관계 구조를 안내한다."""
    lines = ["[클래스 목록]"]
    with SessionLocal() as db:
        for key, model in MODELS.items():
            count = db.scalar(select(func.count()).select_from(model))
            lines.append(f"  {key} ({KEY_TO_CLASS[key]}): {count}건")

        lines.append("\n[관계 구조]")
        rows = db.execute(
            select(
                Edge.source_class,
                Edge.relation,
                Edge.target_class,
                func.count(),
            )
            .group_by(Edge.source_class, Edge.relation, Edge.target_class)
            .order_by(func.count().desc())
        ).all()
        for source, relation, target, count in rows:
            kor = RELATION_KOR.get(relation, relation)
            lines.append(f"  {source} -[{relation}/{kor}]→ {target}: {count}건")

    return "\n".join(lines)


def _describe_table(table, model):
    """특정 클래스의 컬럼 목록과 실제 값 예시를 안내한다."""
    lines = [f"[{table}] 컬럼 목록"]
    with SessionLocal() as db:
        for c in model.__table__.columns:
            col = getattr(model, c.name)
            values = db.scalars(
                select(col).where(col.isnot(None)).distinct().limit(6)
            ).all()
            # 값의 가짓수가 적은 범주형 컬럼만 예시를 붙인다.
            if len(values) <= 5 and c.name not in LONG_COLS:
                sample = " / ".join(str(v)[:20] for v in values)
                lines.append(f"  {c.name}: [{sample}]")
            else:
                lines.append(f"  {c.name}")
    return "\n".join(lines)


def _traverse(db, model, stmt, table, steps, limit, filters=None):
    """관계를 따라 여러 단계를 이동하며 경로를 수집한다.

    ``filters``는 근거(trace) 기록용으로만 쓰이며 탐색 로직에는 영향을 주지 않는다
    (출발 노드 필터는 이미 ``stmt``에 반영돼 있다). 기본값 None이면 빈 dict로 기록한다.
    """
    if filters is None:
        filters = {}
    rows = list(db.scalars(stmt.limit(limit)))
    if not rows:
        return "출발 노드를 찾지 못했습니다."

    class_name = KEY_TO_CLASS[table]
    current = [(r.id, getattr(r, "name", None) or r.id) for r in rows]
    paths = {node_id: [f"{class_name}: {label}"] for node_id, label in current}

    # 경로에 등장한 관계명을 순서대로(중복 제거) 모아 근거로 남긴다.
    seen_relations: list[str] = []

    for step in steps:
        if ":" not in step:
            return f"'{step}' 형식 오류. '관계명:도착클래스'로 지정하세요."

        relation, dest_key = step.split(":", 1)
        if dest_key not in MODELS:
            return f"'{dest_key}'는 없는 클래스입니다. 사용 가능: {list(MODELS)}"

        dest_class = KEY_TO_CLASS[dest_key]
        ids = [node_id for node_id, _ in current]

        edges = list(
            db.scalars(
                select(Edge).where(
                    Edge.relation == relation,
                    Edge.source_id.in_(ids),
                    Edge.target_class == dest_class,
                )
            )
        )
        if not edges:
            done = "\n".join(" ".join(p) for p in paths.values())
            return (
                f"{done}\n\n('{relation}'으로 {dest_class}에 연결된 노드가 없습니다.)"
            )

        if relation not in seen_relations:
            seen_relations.append(relation)

        kor = RELATION_KOR.get(relation, relation)
        new_paths, next_nodes = {}, []
        for e in edges[:limit]:
            base = paths.get(e.source_id, [])
            label = f"-[{relation}/{kor}]→ {dest_class}: {e.target_name or e.target_id}"
            new_paths[f"{e.source_id}||{e.target_id}"] = base + [label]
            next_nodes.append((e.target_id, e.target_name or e.target_id))

        paths, current = new_paths, next_nodes

    path_values = list(paths.values())
    out = [f"총 {len(path_values)}개 경로를 찾았습니다.\n"]
    for i, path in enumerate(path_values, start=1):
        out.append(f"[{i}] " + " ".join(path))

    # ── 경로 탐색 근거 기록(반환 텍스트 확정 직후, 값 변경 없이 부수효과로만) ──
    # 지연 import 사유: trace.py가 이 모듈(tools)의 상수를 import하므로, 이 파일
    # 상단에서 trace를 import하면 순환 import가 된다. record는 모듈 로드가 아닌
    # 도구 "실행 시점"에만 필요하므로, 여기서 함수 내부 지연 import로 순환을 피한다.
    from app.agents.trace import ToolQueryRecord, current_collector

    current_collector().record(
        ToolQueryRecord(
            table=table,
            node_class=class_name,
            filters=dict(filters),
            steps=list(steps),
            # 경로 탐색은 레코드 표(rows)가 없으므로 total은 찾은 경로 수로 둔다.
            total=len(path_values),
            shown_rows=[],
            relations=seen_relations,
            path_segments=[" ".join(p) for p in path_values],
        )
    )

    return "\n".join(out)


def _collect_relations(db, table, rows):
    """조회된 노드들에 연결된 이웃 노드를 수집한다.

    노드가 관계의 출발점인 경우(→)와 도착점인 경우(←)를 모두 모은다.
    """
    class_name = KEY_TO_CLASS[table]
    ids = [r.id for r in rows]
    rel_map = {}

    edges = db.scalars(
        select(Edge).where(
            or_(
                and_(Edge.source_class == class_name, Edge.source_id.in_(ids)),
                and_(Edge.target_class == class_name, Edge.target_id.in_(ids)),
            )
        )
    )
    for e in edges:
        kor = RELATION_KOR.get(e.relation, e.relation)
        if e.source_class == class_name and e.source_id in ids:
            rel_map.setdefault(e.source_id, []).append(
                f"  → [{e.relation}/{kor}] {e.target_class}: "
                f"{e.target_name or e.target_id}"
            )
        if e.target_class == class_name and e.target_id in ids:
            rel_map.setdefault(e.target_id, []).append(
                f"  ← [{e.relation}/{kor}] {e.source_class}: "
                f"{e.source_name or e.source_id}"
            )

    return rel_map


# ---------------------------------------------------------------------------
# tool 본체
# ---------------------------------------------------------------------------


@function_tool(strict_mode=False)
def search_hanmun_novel_db(
    table: str,
    filters: dict[str, str],
    steps: list[str] | None = None,
    include_relations: bool = True,
    limit: int = 30,
    full_text: bool = False,
    schema_only: bool = False,
) -> str:
    """한국한문소설 시맨틱DB(20개 클래스·42종 관계)를 조회한다.

    노드의 속성값 검색과, 관계를 따라가는 경로 탐색을 모두 처리한다.
    steps를 비워두면 단일 클래스 조회, steps를 지정하면 관계를 따라
    이동하는 탐색이 된다. 결과에는 연결된 이웃 노드와 그 관계가 함께
    표시되므로, 속성값만이 아니라 "무엇과 어떻게 연결되어 있는가"까지
    확인할 수 있다.

    ─ 사용 가능한 클래스(table) ─
    [서지] book 이본(소장처·책종·평비본 여부·편사 시기)
           abstract_work 작품(이칭·한글본 여부·창작 시기)
           works_compilation 작품집(표제·유형·수록 작품)
           participant 인물(작자·편사자, 생몰년)
    [참여] review 외평(서발·독법·부기) / side_dot 비점
           related_work 연관작품
    [표현] embedded_work 소작품(작중 시문)
           allusion 전고(경사자집 분류)
    [배열] scene 장면 / character 등장인물 / caste 신분
           ch_elements 요소(캐릭터 분류 코드)
           comment 논평 / remark 평비
           number 대표목차 / episode 개별목차
           background_e 시대 / background_l 공간 / background_w 장소

    ─ 자주 쓰는 경로(steps) ─
      이본→등장인물→요소:     ["contains:character", "possess:ch_elements"]
      이본→등장인물→신분:     ["contains:character", "isPositionedAs:caste"]
      이본→장면→평비:         ["contains:scene", "commentsOn:remark"]
      이본→장면→소작품:       ["contains:scene", "isTheSameAs:embedded_work"]
      작품→이본→외평:         ["spreadsInto:book", "contains:review"]
      이본→대표목차→개별목차: ["contains:number", "contains:episode"]

    Args:
        table: 조회를 시작할 클래스. 위 목록 중 하나를 사용한다.
        filters: 컬럼명과 검색어의 딕셔너리. 문자열 컬럼은 부분 일치로
            검색한다. 한 컬럼에 여러 값을 주려면 세미콜론으로 구분하며
            OR로 묶인다. 서로 다른 컬럼끼리는 AND로 묶인다.
            예) {"work_kor": "상사동전객기;운영전"}
                {"institution_kor": "이길환", "pb_edition_status": "Y"}
                {"criticism_type": "Foreword;Postscript"}
            컬럼명이 확실하지 않으면 schema_only=True로 먼저 확인한다.
            빈 딕셔너리면 해당 클래스 전체를 조회한다.
        steps: 관계를 따라 이동할 경로. "관계명:도착클래스" 형식으로
            순서대로 나열한다. None이나 빈 목록이면 단일 클래스 조회가
            된다. 관계명은 contains, possess, isPositionedAs, commentsOn,
            creates, isTheSameAs, hasPart, spreadsInto, edits, quotes,
            sameEditionAs, isAMotifFor, includes, derived 중 하나다.
        include_relations: 단일 클래스 조회일 때 각 노드에 연결된 이웃
            노드를 함께 반환할지 여부. 기본 True. steps를 쓰면 무시된다.
        limit: 반환할 최대 건수. 기본 30건. 조건에 맞는 전체 건수는
            별도로 함께 보고되므로, 표시된 건수를 전체로 오인하지 않는다.
        full_text: True면 원문·번역을 자르지 않고 전문을 반환한다.
            원문 대조가 목적일 때만 쓰고, 건수가 많으면 피한다.
        schema_only: True면 조회하지 않고 해당 클래스의 컬럼 목록과 실제
            값 예시만 반환한다. table을 빈 문자열로 두면 전체 클래스
            목록과 42종 관계 구조를 안내한다.

    Returns:
        조회 결과를 사람이 읽기 좋은 텍스트로 정리해 반환한다. 단일
        조회는 각 노드의 속성값과 연결된 이웃 노드를, 경로 탐색은 각
        단계를 거쳐 도달한 경로를 표시한다.
    """
    # ── 스키마 안내 모드 ──
    if schema_only:
        if not table:
            return _describe_all()
        model = MODELS.get(table)
        if model is None:
            return f"'{table}'은 없는 클래스입니다. 사용 가능: {list(MODELS)}"
        return _describe_table(table, model)

    model = MODELS.get(table)
    if model is None:
        return f"'{table}'은 없는 클래스입니다. 사용 가능: {list(MODELS)}"

    try:
        with SessionLocal() as db:
            stmt = _apply_filters(model, select(model), filters)

            # ── 경로 탐색 모드 ──
            if steps:
                return _traverse(db, model, stmt, table, steps, limit, filters)

            # ── 단일 조회 모드 ──
            total = db.scalar(select(func.count()).select_from(stmt.subquery()))
            rows = list(db.scalars(stmt.limit(limit)))
            if not rows:
                return "조건에 맞는 데이터를 찾지 못했습니다."

            rel_map = _collect_relations(db, table, rows) if include_relations else {}

    except ValueError as err:
        return str(err)

    shown = f"{len(rows)}건 표시" if total > len(rows) else "전부 표시"
    out = [f"전체 {total}건 중 {shown}.\n"]
    for i, row in enumerate(rows, start=1):
        block = [f"[{i}] {_render(row, brief=not full_text)}"]
        block.extend(rel_map.get(row.id, []))
        out.append("\n".join(block))

    # ── 단일 조회 근거 기록(반환 텍스트 확정 직후, 값 변경 없이 부수효과로만) ──
    # 지연 import 사유: trace.py가 이 모듈(tools)의 상수를 import하므로, 이 파일
    # 상단에서 trace를 import하면 순환 import가 된다. record는 모듈 로드가 아닌
    # 도구 "실행 시점"에만 필요하므로, 함수 내부 지연 import로 순환을 피한다.
    from app.agents.trace import ToolQueryRecord, current_collector

    # rel_map 값은 "  → [relation/kor] Class: name" 형태의 텍스트 목록이다.
    # 여기서 원문 관계명(relation)만 첫 등장 순서를 유지하며 중복 없이 추출한다.
    # include_relations=False면 rel_map이 비어 relations도 빈 목록이 된다.
    relations: list[str] = []
    for lines in rel_map.values():
        for line in lines:
            # 예: "  → [contains/보유한다] Scene: ..." → "contains"
            marker = line.split("[", 1)
            if len(marker) < 2:
                continue
            name = marker[1].split("/", 1)[0]
            if name and name not in relations:
                relations.append(name)

    current_collector().record(
        ToolQueryRecord(
            table=table,
            node_class=KEY_TO_CLASS[table],
            filters=dict(filters),
            steps=None,
            total=total,
            shown_rows=[_serialize_row(row) for row in rows],
            relations=relations,
            path_segments=[],
        )
    )

    return "\n\n".join(out)
