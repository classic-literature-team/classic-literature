"""답변 근거(trace) 수집·병합을 위한 데이터 구조와 상수.

도구 ``search_hanmun_novel_db``가 조회 과정에서 계산한 구조화 데이터를
요청 단위로 모으고, 이를 프론트가 소비할 단일 trace 페이로드로 병합하기
위한 기반 모듈이다. 이 파일은 다음 세 층으로 확장된다.

1. 원본 기록 구조(``ToolQueryRecord``)와 클래스 한국어 label 매핑 상수 — (본 작업)
2. 요청 단위 수집기(``TraceCollector`` / ``current_collector``)
3. 병합 빌더(``build_trace_payload``)

순환 import 방지
----------------
클래스명↔키 매핑(``CLASS_TO_KEY``/``KEY_TO_CLASS``)과 관계 한국어 병기
(``RELATION_KOR``)는 이미 ``app.agents.tools``에 정의돼 있다. 공용 상수를
한쪽(``tools``)에만 두고 ``trace``가 ``tools``를 참조하는 단방향 구조를
택한다. 이후 ``tools``가 ``trace``의 수집기를 사용(계측)하게 되지만, 그
호출은 모듈 로드 시점이 아니라 도구 실행 시점에 이뤄지므로 import 순환이
발생하지 않는다.
"""

import contextvars
from dataclasses import dataclass, field

from app.agents.tools import CLASS_TO_KEY, KEY_TO_CLASS, RELATION_KOR

__all__ = [
    "ToolQueryRecord",
    "CLASS_LABEL_KOR",
    "CLASS_TO_KEY",
    "KEY_TO_CLASS",
    "RELATION_KOR",
    "TraceCollector",
    "current_collector",
    "build_trace_payload",
]


@dataclass
class ToolQueryRecord:
    """도구가 한 번 조회할 때마다 남기는 원본 근거 기록.

    ``tools.py``가 내부적으로 이미 계산하는 값(총 건수·표시 행·관계·경로)을
    원천에서 그대로 담아, 반환 텍스트를 다시 파싱하지 않고도 정확한 근거
    표를 만들 수 있게 한다.

    Attributes:
        table: 조회를 시작한 클래스의 테이블 키 (예: ``"book"``).
        node_class: Edge 표기 클래스명 (예: ``"Book"``). ``KEY_TO_CLASS[table]``.
        filters: 적용된 컬럼→검색어 딕셔너리.
        steps: 경로 탐색 시 ``"관계명:도착클래스"`` 단계 목록. 단일 조회면 None.
        total: 조건에 맞는 전체 건수.
        shown_rows: 표시된 레코드의 컬럼→값 매핑 목록. 장문 컬럼은 축약된다.
        relations: 등장한 관계명(원문 키, 예: ``"spreadsInto"``) 목록.
        path_segments: 경로 탐색 시 각 단계를 나타내는 라벨 목록.
    """

    table: str
    node_class: str
    filters: dict[str, str]
    steps: list[str] | None
    total: int
    shown_rows: list[dict[str, str]]
    relations: list[str] = field(default_factory=list)
    path_segments: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 클래스 한국어 label 매핑
# ---------------------------------------------------------------------------

# Edge 표기 클래스명(sourceClass/targetClass) → 한국어 label.
# 라벨은 tools.py의 도구 docstring에 정리된 클래스 설명과 일치시킨다.
# CLASS_TO_KEY(20개 클래스)를 단일 진실 원천으로 삼아 커버 범위를 맞춘다.
CLASS_LABEL_KOR = {
    # 서지적 요소
    "Book": "이본",
    "AbstractWork": "작품",
    "WorksCompilation": "작품집",
    "Participant": "인물",
    # 참여적 요소
    "Review": "외평",
    "SideDot": "비점",
    "RelatedWork": "연관작품",
    # 표현적 요소
    "EmbeddedWork": "소작품",
    "Allusion": "전고",
    # 배열적 요소
    "Scene": "장면",
    "Character": "등장인물",
    "Caste": "신분",
    "ChElements": "요소",
    "Comment": "논평",
    "Remark": "평비",
    "Number": "대표목차",
    "Episode": "개별목차",
    "BackgroundE": "시대",
    "BackgroundL": "공간",
    "BackgroundW": "장소",
}


# ---------------------------------------------------------------------------
# 요청 단위 근거 수집기 (contextvars 기반)
# ---------------------------------------------------------------------------

# 요청(=asyncio 태스크) 단위 수집기를 담는 ContextVar.
#
# 가변 기본값(예: TraceCollector 인스턴스)을 ContextVar의 default로 두면 모든
# 태스크가 같은 인스턴스를 공유해 근거가 뒤섞인다(Error Scenario 4). 따라서
# default는 None으로만 두고, 수집기가 없을 때 current_collector()가 그 태스크
# 문맥에 새 인스턴스를 set 하는 지연 바인딩 패턴을 사용한다. contextvars는
# asyncio 태스크 경계에서 문맥을 복사하되 set은 해당 문맥에만 반영되므로,
# 동시 요청은 각자 별도 수집기를 갖게 되어 서로 격리된다(Requirement 2.2).
_collector_var: contextvars.ContextVar["TraceCollector | None"]
_collector_var = contextvars.ContextVar("trace_collector", default=None)


class TraceCollector:
    """한 요청 동안 도구가 남기는 ``ToolQueryRecord`` 들을 순서대로 모으는 수집기.

    라우트(요청 핸들러)가 스트리밍 시작 시 ``reset()`` 으로 비우고, 도구가 조회
    도중 ``record()`` 로 근거를 append 하며, 델타 스트리밍이 끝난 뒤 라우트가
    ``snapshot()`` 으로 기록 전체를 읽어 trace로 병합한다.

    인스턴스는 요청(태스크)마다 하나씩 ``current_collector()`` 를 통해 바인딩되므로,
    이 클래스 자체는 태스크 간 공유를 고려하지 않는다.
    """

    def __init__(self) -> None:
        self._records: list[ToolQueryRecord] = []

    def reset(self) -> None:
        """수집된 기록을 모두 비운다(요청 시작 시 호출; Requirement 2.1)."""
        self._records = []

    def record(self, rec: ToolQueryRecord) -> None:
        """근거 기록 하나를 기록 순서 그대로 추가한다."""
        self._records.append(rec)

    def snapshot(self) -> list[ToolQueryRecord]:
        """기록된 순서를 보존한 목록을 반환한다(Requirement 2.3).

        호출자가 반환 리스트를 변경해도 내부 상태가 오염되지 않도록 얕은 복사본을
        돌려준다. ``ToolQueryRecord`` 항목 자체는 기록 후 변경하지 않는 전제이므로
        방어적 복사는 리스트 컨테이너 수준으로 충분하다.
        """
        return list(self._records)


def current_collector() -> TraceCollector:
    """현재 태스크 문맥의 수집기를 반환한다(없으면 새로 만들어 바인딩).

    ContextVar에 수집기가 아직 없으면 새 ``TraceCollector`` 를 생성해 현재 문맥에
    ``set`` 한 뒤 반환한다. 이렇게 지연 바인딩하면 태스크마다 별도 인스턴스가
    할당되어 동시 요청 간 근거가 격리된다(Requirement 2.2, Error Scenario 4).
    """
    collector = _collector_var.get()
    if collector is None:
        collector = TraceCollector()
        _collector_var.set(collector)
    return collector


# ---------------------------------------------------------------------------
# trace 페이로드 병합 빌더
# ---------------------------------------------------------------------------


def _class_label(node_class: str) -> str:
    """Edge 표기 클래스명의 한국어 label을 반환한다.

    매핑에 없는 클래스명이 오면(데이터 이상 등) 원문 클래스명을 그대로
    label로 써서 정보 손실 없이 표시한다.
    """
    return CLASS_LABEL_KOR.get(node_class, node_class)


def build_trace_payload(records: list[ToolQueryRecord]) -> dict | None:
    """여러 도구 호출 기록(``ToolQueryRecord``)을 하나의 trace로 병합한다.

    설계 결정 3의 병합 규칙을 그대로 구현한다.

    - classes: 등장 클래스를 첫 등장 순서 유지·중복 제거한 합집합.
    - relations: 등장 관계명을 첫 등장 순서 유지·중복 제거한 합집합(한국어 병기).
    - records: 클래스별 레코드를 누적하되 ``id`` 기준 중복 제거, total은 그
      클래스를 조회한 기록들의 total 중 최댓값, columns는 등장 순서 유지 합집합.
    - path: 병합된 경로 단계가 있으면 그 한국어 라벨 목록, 없으면 조회 클래스
      label 나열.
    - evidence: 클래스별 조회 건수 요약 문장 리스트.

    기록이 비어 있으면(도구를 안 썼으면) ``None``을 반환한다(Requirement 3.9).

    Returns:
        design.md "Backend Component 3"의 JSON 스키마를 따르는 dict, 또는 None.
    """
    # Requirement 3.9: 빈 입력이면 trace 자체를 만들지 않는다.
    if not records:
        return None

    # 클래스별 병합 상태를 첫 등장 순서대로 보존하기 위해 dict(삽입 순서 유지)를
    # 키(node_class) 기준으로 누적한다. 파이썬 dict는 3.7+ 삽입 순서를 보장하므로
    # 별도 순서 리스트 없이도 첫 등장 순서를 유지한다(Requirement 3.1).
    class_groups: dict[str, dict] = {}
    # 관계명은 첫 등장 순서 유지·중복 제거를 위해 dict를 순서 집합처럼 사용한다.
    relation_order: dict[str, None] = {}

    for rec in records:
        node_class = rec.node_class
        key = CLASS_TO_KEY.get(node_class, rec.table)

        group = class_groups.get(node_class)
        if group is None:
            group = {
                "key": key,
                "node_class": node_class,
                "label": _class_label(node_class),
                "total": rec.total,
                # columns: 등장 순서 유지 합집합(dict를 순서 집합으로 사용).
                "_columns": {},
                # rows: id 기준 중복 제거하며 누적. id가 없으면 완전 동일 dict만 제거.
                "_rows": [],
                # id 기준 중복 판정용 집합. "id" 컬럼이 있는 행에만 적용한다.
                "_seen_ids": set(),
                # id가 없는 행은 완전 동일 dict 중복만 제거하기 위한 판정용 집합.
                "_seen_norows": set(),
            }
            class_groups[node_class] = group
        else:
            # Requirement 3.4: 같은 클래스 total은 조회들의 최댓값(보수적 상한).
            group["total"] = max(group["total"], rec.total)

        for row in rec.shown_rows:
            # 판단 근거: 대부분의 클래스 레코드는 "id"를 갖지만(_render는 모든
            # 비어있지 않은 컬럼을 담고 모델은 id PK를 가짐), 방어적으로 "id"
            # 키가 있을 때만 id 중복 제거를 적용한다. id가 없으면 완전 동일
            # dict(모든 컬럼·값이 같은 행)만 중복으로 보고 제거한다. 이렇게 하면
            # design.md Validation Rules(rows의 각 키는 columns의 부분집합,
            # id는 유일)와 모순되지 않으면서 id 없는 클래스도 합리적으로 처리된다.
            row_id = row.get("id")
            if row_id is not None:
                if row_id in group["_seen_ids"]:
                    continue
                group["_seen_ids"].add(row_id)
            else:
                # 완전 동일 dict 중복 제거용 정규화 키(정렬된 아이템 튜플).
                signature = tuple(sorted(row.items()))
                if signature in group["_seen_norows"]:
                    continue
                group["_seen_norows"].add(signature)

            # columns 합집합(등장 순서 유지): 이 행에 실제로 존재하는 컬럼만.
            for col in row.keys():
                group["_columns"].setdefault(col, None)
            group["_rows"].append(row)

        # Requirement 3.2: 관계명 첫 등장 순서 유지·중복 제거.
        for name in rec.relations:
            relation_order.setdefault(name, None)

    # classes 배열(첫 등장 순서 유지·중복 제거; Requirement 3.1, 3.10).
    classes = [
        {
            "key": g["key"],
            "node_class": g["node_class"],
            "label": g["label"],
        }
        for g in class_groups.values()
    ]

    # relations 배열(Requirement 3.2, 한국어 병기).
    relations = [
        {"name": name, "korean": RELATION_KOR.get(name, name)}
        for name in relation_order
    ]

    # records 배열(Trace_Record_Group; Requirement 3.3, 3.4, 3.5).
    records_out = []
    for g in class_groups.values():
        columns = list(g["_columns"].keys())
        # rows의 각 dict 키는 columns의 부분집합이어야 한다(design Validation
        # Rules). columns는 등장 순서 합집합이므로 각 행의 키는 이미 부분집합이다.
        rows = g["_rows"]
        records_out.append(
            {
                "key": g["key"],
                "node_class": g["node_class"],
                "label": g["label"],
                "total": g["total"],
                "shown": len(rows),  # 병합된 rows 길이(shown == rows.length).
                "columns": columns,
                "rows": rows,
            }
        )

    # path: 경로 탐색 단계(path_segments)가 하나라도 있으면 병합 경로의 한국어
    # 라벨 목록, 없으면 조회 클래스 label 나열(Requirement 3.6, 3.7).
    path = _build_path(records, classes)

    # evidence: 클래스별 조회 건수 요약 문장(Requirement 3.8).
    evidence = []
    for g in class_groups.values():
        label = g["label"]
        node_class = g["node_class"]
        total = g["total"]
        shown = len(g["_rows"])
        if total == shown:
            # 예: "작품(AbstractWork) 2건 확인"
            evidence.append(f"{label}({node_class}) {total}건 확인")
        else:
            # 예: "이본(Book) 142건 중 30건 확인"
            evidence.append(f"{label}({node_class}) {total}건 중 {shown}건 확인")

    return {
        "path": path,
        "classes": classes,
        "relations": relations,
        "evidence": evidence,
        "records": records_out,
    }


def _build_path(records: list[ToolQueryRecord], classes: list[dict]) -> list[str]:
    """병합된 path 단계 목록을 만든다.

    경로 탐색 단계(path_segments)가 존재하는 기록이 있으면, 그 기록들의 경로
    조각을 등장 순서대로 이어 하나의 단계 목록으로 재구성한다(설계 결정 3).
    이때 같은 라벨이 연달아 중복되면(동일 단계 반복) 한 번만 남긴다. 경로
    단계가 전혀 없으면(단일 조회만 있었으면) 조회 클래스의 한국어 label을
    나열한다(Requirement 3.7).

    path_segments 라벨은 도구가 이미 한국어 관계 병기를 포함해 만든 문자열이므로
    (예: ``"-[contains/보유한다]→ Scene: ..."``) 그대로 사용한다.
    """
    merged: list[str] = []
    for rec in records:
        for seg in rec.path_segments:
            if merged and merged[-1] == seg:
                continue
            merged.append(seg)

    if merged:
        return merged

    # Requirement 3.7: 경로 부재 시 조회 클래스의 label 나열.
    return [c["label"] for c in classes]
