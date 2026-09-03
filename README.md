# Classic Literature

고전 문학 탐색 서비스. React 프론트엔드와 FastAPI 백엔드로 구성된 모노레포입니다.

## 기술 스택

### Frontend (`frontend/`)

- React + TypeScript + Vite
- React Router (라우팅)
- Zustand (클라이언트 상태)
- TanStack Query (서버 상태/캐싱)
- shadcn/ui + Tailwind CSS (UI)
- React Hook Form + Zod (폼/검증)
- ESLint + Prettier (포맷팅)

### Backend (`backend/`)

- FastAPI
- OpenAI Agents SDK (tool calling)
- SQLAlchemy 2.0 + Alembic (ORM/마이그레이션)
- Pydantic / pydantic-settings (스키마/설정)
- PostgreSQL (psycopg v3)

## 사전 요구사항

- Node.js 20+
- Python 3.10+ (개발 환경 3.12)
- PostgreSQL 14+

## Frontend 실행

```bash
cd frontend
npm install
cp .env.example .env   # 필요 시 값 조정
npm run dev            # http://localhost:5173
```

주요 스크립트:

- `npm run dev` — 개발 서버
- `npm run build` — 타입체크 + 프로덕션 빌드
- `npm run lint` / `npm run lint:fix` — ESLint
- `npm run format` / `npm run format:check` — Prettier

개발 시 `/api` 요청은 `vite.config.ts`의 프록시를 통해 백엔드(`http://localhost:8000`)로 전달됩니다.

## Backend 실행

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements-dev.txt
copy .env.example .env             # 필요 시 값 조정

# DB 마이그레이션 (PostgreSQL 기동 후)
alembic revision --autogenerate -m "init"
alembic upgrade head

# 개발 서버
uvicorn app.main:app --reload      # http://localhost:8000
```

- API 문서: `http://localhost:8000/docs`
- 헬스체크: `http://localhost:8000/health`

주요 도구:

- `ruff check app` — 린트
- `pytest` — 테스트

## 프로젝트 구조

```
classic-literature/
├── frontend/
│   └── src/
│       ├── assets/         # 정적 리소스
│       │   ├── images/
│       │   ├── icons/
│       │   └── fonts/
│       ├── components/     # 공통 컴포넌트
│       │   └── ui/         # shadcn/ui 컴포넌트
│       ├── layouts/        # 레이아웃 컴포넌트 (RootLayout 등)
│       ├── pages/          # 라우트 페이지
│       ├── routes/         # 라우팅
│       │   ├── index.tsx       # 라우터 정의
│       │   ├── paths.ts        # 경로 상수
│       │   └── ProtectedRoute.tsx  # 인증 가드
│       ├── hooks/          # 커스텀 훅 (데이터 훅 등)
│       ├── stores/         # Zustand 스토어 (ui, auth)
│       ├── utils/          # api 클라이언트, query client 등
│       ├── lib/            # shadcn 유틸 (cn) — components.json 규약
│       ├── styles/
│       │   └── globals.css     # Tailwind + 테마
│       ├── App.tsx
│       └── main.tsx
└── backend/
    └── app/
        ├── agents/       # OpenAI Agents SDK (tool calling)
        ├── api/routes/   # 라우터 (books, chat)
        ├── core/         # 설정 (config)
        ├── db/           # SQLAlchemy base/session
        ├── models/       # ORM 모델
        ├── schemas/      # Pydantic 스키마
        └── main.py       # FastAPI 진입점
```

## 환경 변수

`.env` 파일은 커밋되지 않습니다. 각 디렉토리의 `.env.example`을 참고하세요.

- Frontend: `VITE_API_BASE_URL`
- Backend: `DATABASE_URL`, `CORS_ORIGINS`, `OPENAI_API_KEY`, `OPENAI_MODEL`

> `/api/chat` 엔드포인트는 `OPENAI_API_KEY`가 설정되어야 동작합니다. 키가 없으면 503을 반환합니다.
