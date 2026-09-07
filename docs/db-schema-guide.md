# DB 스키마 변경 가이드 (Alembic)

테이블(컬럼/테이블) 구조를 바꿀 때 지켜야 할 규칙과 순서.

## 🚫 절대 규칙: DB에서 직접 바꾸지 않는다

pgAdmin, DBeaver, SQL 콘솔 등에서 **테이블을 직접 수정하지 마세요.**
(컬럼 추가/삭제/타입 변경/새 테이블 등)

DB에서 직접 바꾸면:

- DB만 바뀌고 **모델 코드는 그대로** → 둘이 어긋남
- 다음 `alembic revision`이 그 변경을 **되돌리는** 마이그레이션을 만들 수 있음
- **협업자는 그 변경을 모름** (마이그레이션 파일에 안 남음) → 각자 DB가 달라짐

**원본(정답)은 항상 모델 코드**(`app/models/`)입니다. DB는 그걸로 만들어지는 결과물일 뿐.

---

## ✅ 올바른 변경 순서

```
1. 모델 코드 수정        app/models/entities.py
        ↓
2. 마이그레이션 생성      alembic revision --autogenerate -m "무엇을 바꿨는지"
        ↓
3. 생성된 파일 확인       alembic/versions/ 의 새 파일을 열어 내용 점검
        ↓
4. 내 DB에 적용          alembic upgrade head
        ↓
5. 커밋 & 공유           git add / commit / push → PR
        ↓
(협업자) pull 후          alembic upgrade head   ← 자기 DB에 똑같이 적용
```

> 모든 alembic 명령은 **`backend` 폴더에서, 가상환경 `(.venv)`가 켜진 상태**로 실행합니다.

---

## 예시 1: 기존 테이블에 컬럼 추가

`Book`에 `page_count`(쪽수)를 추가한다고 가정.

```python
# app/models/entities.py 의 Book 클래스
from sqlalchemy import Integer  # 파일 상단 import에 포함돼 있는지 확인

class Book(EntityMixin, Base):
    __tablename__ = "book"
    ...
    page_count: Mapped[int | None] = mapped_column(Integer)  # ← 추가
```

```powershell
alembic revision --autogenerate -m "add page_count to book"
alembic upgrade head
```

Alembic이 "코드엔 page_count 있는데 DB엔 없다 → ADD COLUMN"을 자동 생성합니다.

---

## 예시 2: 새 테이블 추가

1. `app/models/entities.py`에 새 클래스 작성

```python
class NewThing(EntityMixin, Base):
    __tablename__ = "new_thing"
    some_field: Mapped[str | None] = mapped_column(Text)
```

2. `app/models/__init__.py`에 **꼭 등록** (등록 안 하면 Alembic이 못 봄)

```python
from app.models.entities import ..., NewThing
__all__ = [..., "NewThing"]
```

3. 마이그레이션 생성·적용

```powershell
alembic revision --autogenerate -m "add new_thing table"
alembic upgrade head
```

---

## 자주 쓰는 Alembic 명령

```powershell
alembic current                 # 현재 DB가 적용한 마이그레이션 버전
alembic history                 # 마이그레이션 이력(체인) 보기
alembic revision --autogenerate -m "메시지"   # 모델 변경 감지 → 마이그레이션 생성
alembic upgrade head            # 최신까지 적용
alembic downgrade -1            # 한 단계 되돌리기 (주의)
```

---

## 주의사항

1. **`--autogenerate`가 완벽하지 않다**
   - 컬럼 이름 변경(rename)을 "삭제 + 추가"로 인식할 수 있음 → 데이터 손실 위험.
   - 그래서 3번(생성된 파일 확인)이 중요. 의도와 다르면 파일을 손으로 수정.

2. **마이그레이션 파일은 지우지 않는다**
   - 각 파일이 "변경 이력"이라 체인으로 이어짐. 현재: `2cdae4194444_create_entity_and_edge_tables.py`
   - 이미 공유(push)된 마이그레이션은 수정/삭제 금지. 되돌릴 땐 새 마이그레이션을 추가.

3. **적용 순서**
   - 스키마 변경은 브랜치 → PR → 머지 흐름으로. 협업자는 pull 후 반드시 `alembic upgrade head`.

---

## 요약

| 상황 | 할 것 |
|------|-------|
| 컬럼 추가/변경/삭제 | 모델 수정 → `revision --autogenerate` → `upgrade head` |
| 새 테이블 | 모델 클래스 + `__init__.py` 등록 → `revision` → `upgrade` |
| DB에서 직접 수정 | ❌ 금지 |
| 이미 push된 마이그레이션 | ❌ 수정/삭제 금지, 새 마이그레이션으로 |
