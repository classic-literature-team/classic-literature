# 개발 환경 셋업 가이드 (처음부터 끝까지)

이 문서는 **처음 프로젝트를 받는 사람**이 컴퓨터에 개발 환경을 만들고,
DB 테이블까지 만드는 것을 목표로 합니다. 개발 경험이 없어도 **위에서부터 순서대로**
따라 하면 됩니다.

> 💡 명령어는 **PowerShell**(Windows 기본 터미널)에 한 줄씩 붙여넣고 Enter를 누르세요.
> PowerShell 여는 법: 시작 메뉴 → "PowerShell" 검색 → 실행.

---

## 0. 준비물 한눈에 보기

이 프로젝트를 돌리려면 아래 4가지가 필요합니다. 다음 장에서 하나씩 설치를 확인합니다.

| 프로그램 | 용도 | 확인 명령 |
|----------|------|-----------|
| Git | 소스코드 받기 | `git --version` |
| Node.js | 프론트엔드(화면) 실행 | `node --version` |
| Python | 백엔드(서버) 실행 | `python --version` |
| PostgreSQL | 데이터베이스 | `psql --version` |

**"확인 명령"을 터미널에 치면:**
- 버전 숫자가 나오면 → 이미 설치됨 (설치 건너뛰기)
- `... is not recognized ...` 같은 에러가 나오면 → 아직 없음 (설치 필요)

---

## 1. Git 설치 확인

```powershell
git --version
```

- 버전이 나오면 통과.
- 없으면 설치: https://git-scm.com/download/win 에서 다운로드 후 기본값으로 설치.
- 설치 후 **PowerShell을 껐다가 다시 열어야** 인식됩니다.

---

## 2. 소스코드 받기

원하는 폴더에서 (예: 문서 폴더) 아래를 실행합니다.

```powershell
git clone <저장소 주소>
cd classic-literature
```

> `<저장소 주소>`는 GitHub 저장소 페이지의 초록색 "Code" 버튼에서 복사한 주소입니다.
> 예: `https://github.com/classic-literature-team/classic-literature.git`

이후 모든 명령은 이 `classic-literature` 폴더 안에서 실행합니다.

---

## 3. 프론트엔드(화면) 셋업

### 3-1. Node.js 설치 확인

```powershell
node --version
npm --version
```

- 둘 다 버전이 나오면 통과. (Node는 20 이상 권장)
- 없으면 설치: https://nodejs.org 에서 **LTS 버전** 다운로드 후 설치.
- 설치 후 PowerShell을 껐다가 다시 여세요.

### 3-2. 프론트엔드 패키지 설치

```powershell
cd frontend
npm install
```

- 인터넷에서 필요한 라이브러리를 받아옵니다. 몇 분 걸릴 수 있어요.
- 끝나면 `frontend` 폴더 안에 `node_modules` 폴더가 생깁니다.

### 3-3. 환경설정 파일 만들기

```powershell
Copy-Item .env.example .env
```

- 프론트엔드는 특별히 고칠 값이 없으면 그대로 두면 됩니다.

### 3-4. 프론트엔드 실행 테스트

```powershell
npm run dev
```

- `http://localhost:5173` 주소가 나오면 성공. 브라우저에서 열어 화면이 뜨는지 확인하세요.
- 종료는 터미널에서 `Ctrl + C`.

> 여기까지 되면 프론트엔드는 완료. 다음은 백엔드로 넘어갑니다.
> (`cd ..` 를 쳐서 상위 폴더로 돌아가세요.)

---

## 4. 데이터베이스(PostgreSQL) 셋업

### 4-1. PostgreSQL 설치 확인

```powershell
psql --version
```

- 버전(예: `psql (PostgreSQL) 16.x`)이 나오면 통과.
- 없으면 설치: https://www.postgresql.org/download/windows/ 에서 설치.
  - 설치 중 **비밀번호**를 정하라고 나옵니다. 이 비밀번호를 꼭 기억하세요. (뒤에서 씁니다)
  - 설치 후 PowerShell을 껐다가 다시 여세요.

### 4-2. 프로젝트용 데이터베이스 만들기

이 프로젝트는 `CLL`이라는 이름의 데이터베이스를 사용합니다. 아래로 만듭니다.

```powershell
psql -U postgres -c "CREATE DATABASE \"CLL\";"
```

- 비밀번호를 물어보면 4-1에서 정한 비밀번호를 입력합니다. (입력 시 화면에 안 보이는 게 정상)
- `CREATE DATABASE` 라고 나오면 성공.
- 이미 있다는 에러가 나오면 이미 만들어진 것이니 넘어가도 됩니다.

---

## 5. 백엔드(서버) 셋업

### 5-1. Python 설치 확인

```powershell
python --version
```

- `Python 3.10` 이상이면 통과. (권장 3.12)
- 없으면 설치: https://www.python.org/downloads/ 에서 설치.
  - 설치 첫 화면에서 **"Add python.exe to PATH"** 체크박스를 꼭 켜세요.
  - 설치 후 PowerShell을 껐다가 다시 여세요.

### 5-2. 백엔드 폴더로 이동 + 가상환경 만들기

가상환경(venv)은 이 프로젝트 전용 파이썬 공간입니다. 다른 프로젝트와 안 섞이게 해줍니다.

```powershell
cd backend
python -m venv .venv
```

- `backend` 안에 `.venv` 폴더가 생기면 성공.

### 5-3. 가상환경 켜기

```powershell
.\.venv\Scripts\Activate.ps1
```

- 성공하면 줄 맨 앞에 `(.venv)` 가 붙습니다. **이게 붙어 있어야** 이후 명령이 제대로 됩니다.
- 만약 "실행할 수 없습니다 / 보안 정책" 에러가 나면, 아래를 한 번 실행하고 다시 시도하세요.

  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

### 5-4. 백엔드 패키지 설치

```powershell
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

- 서버에 필요한 라이브러리를 받아옵니다. 몇 분 걸릴 수 있어요.

### 5-5. 환경설정 파일(.env) 만들기

```powershell
Copy-Item .env.example .env
```

그다음 `backend\.env` 파일을 **메모장이나 편집기로 열어서** 아래 줄을 본인 환경에 맞게 고칩니다.

```
DATABASE_URL=postgresql+psycopg://postgres:여기에_본인_비밀번호@localhost:5432/CLL
```

이 한 줄의 의미 (아주 중요):

```
postgresql+psycopg://[아이디]:[비밀번호]@[주소]:[포트]/[데이터베이스 이름]
                      postgres  본인비번   localhost 5432   CLL
```

- **아이디**: 보통 `postgres` (설치할 때 기본값)
- **비밀번호**: 4-1에서 정한 그 비밀번호로 바꾸기
- **포트**: 보통 `5432`
- **맨 뒤 CLL**: 4-2에서 만든 데이터베이스 이름 (그대로 두기)

> ⚠️ `OPENAI_API_KEY` 는 AI 채팅 기능에만 필요합니다. 지금 없어도 나머지는 다 동작합니다.
> 키가 있으면 넣고, 없으면 비워두세요. (이 값은 절대 외부에 공유하지 마세요.)

### 5-6. 데이터베이스 테이블 만들기 (마이그레이션)

이 프로젝트의 테이블 구조를 방금 만든 `CLL` 데이터베이스에 생성합니다.

```powershell
alembic upgrade head
```

- `Running upgrade ... create entity and edge tables` 같은 문구가 나오면 성공.
- 이 명령은 **`backend` 폴더 안에서, `(.venv)`가 켜진 상태**로 실행해야 합니다.

### 5-7. 테이블이 잘 만들어졌는지 확인

```powershell
psql -U postgres -d CLL -c "\dt"
```

- `book`, `character`, `scene`, `edge` 등 여러 테이블 목록이 나오면 **성공**입니다. (총 22개)

### 5-8. 백엔드 실행 테스트

```powershell
uvicorn app.main:app --reload
```

- `http://localhost:8000` 주소가 나오면 성공.
- 브라우저에서 `http://localhost:8000/docs` 를 열면 API 목록 화면이 보입니다.
- 종료는 `Ctrl + C`.

---

## 6. 완료 체크리스트

- [ ] `git --version` 됨
- [ ] `frontend`에서 `npm install` 완료
- [ ] `npm run dev` 로 화면(localhost:5173) 뜸
- [ ] `CLL` 데이터베이스 생성됨
- [ ] `backend`에서 가상환경 `(.venv)` 켜짐
- [ ] `pip install -r requirements-dev.txt` 완료
- [ ] `backend\.env`의 DATABASE_URL 을 본인 비밀번호로 수정함
- [ ] `alembic upgrade head` 로 테이블 생성됨
- [ ] `\dt` 로 테이블 22개 확인됨
- [ ] `uvicorn ...` 로 서버(localhost:8000/docs) 뜸

모두 체크되면 환경 셋업 완료입니다.

---

## 7. 자주 겪는 문제

**"...is not recognized..." 에러**
→ 해당 프로그램이 설치 안 됐거나, 설치 후 PowerShell을 다시 안 열어서 그렇습니다. PowerShell을 껐다가 다시 여세요.

**`(.venv)`가 안 붙어요 / activate 에러**
→ 5-3의 `Set-ExecutionPolicy ...` 명령을 실행한 뒤 다시 `Activate.ps1` 하세요.

**`alembic upgrade head` 가 연결 실패 / 비밀번호 오류**
→ `backend\.env`의 DATABASE_URL 안의 비밀번호·데이터베이스 이름(CLL)이 실제와 맞는지 확인하세요.
   `password 인증 실패` = 비밀번호 틀림, `"CLL" 데이터베이스 없음` = 4-2를 안 했거나 이름 오타.

**포트가 이미 사용 중이라고 나와요**
→ 이전에 켠 서버가 안 꺼진 것일 수 있어요. 해당 터미널에서 `Ctrl + C`로 종료 후 다시 실행하세요.

---

## (참고) Docker로 DB를 대신 쓰는 방법

PostgreSQL 직접 설치가 어렵고 Docker가 설치돼 있다면, 4장 대신 아래로 DB를 띄울 수 있습니다.

```powershell
docker compose up -d          # DB 컨테이너 실행 (포트 5433)
```

이 경우 `backend\.env`의 포트를 **5433**, 데이터베이스 이름을 **classic_literature**로 맞춰야 합니다.

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/classic_literature
```

나머지(5-6 마이그레이션 등)는 동일합니다.
