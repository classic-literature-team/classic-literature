# Git 워크플로 (GitHub Flow)

작업 하나 = 브랜치 하나 = PR 하나 = 머지 후 삭제.

## 핵심 규칙

1. `main`에서는 작업하지 않는다. `main`은 `pull`로 받기만 한다.
2. 브랜치는 작업 하나만 담고, 머지되면 삭제한다. (재사용 X)
3. 매 작업 시작 전 `git pull`로 최신 상태에서 시작한다.

## 반복 사이클

### ① 작업 시작 — 최신 main에서 새 브랜치

```bash
git checkout main
git pull
git checkout -b song/feature-작업이름
```

### ② 작업하며 의미 단위로 커밋

```bash
git add <바꾼 파일>
git commit -m "feat: 무엇을 했는지"
```

### ③ 원격에 올리기 (첫 push만 -u)

```bash
git push -u origin song/feature-작업이름
```

### ④ PR 생성 → 머지

- GitHub에서 Pull Request 생성
- GitHub Actions 체크(Frontend / Backend) 초록불 확인
- Merge pull request

### ⑤ 머지 후 정리 (매번)

```bash
git checkout main
git pull
git branch -d song/feature-작업이름
git fetch --prune
```

이후 다음 작업은 다시 ①로 돌아간다.

## git status 상태 값 읽기

`git status -sb`의 첫 줄(브랜치 라인)이 로컬과 원격의 관계를 알려준다.

| 표시 | 의미 | 할 일 |
|------|------|-------|
| `## main...origin/main` | 로컬 = 원격, 동기화됨 | 없음 (깨끗) |
| `## main...origin/main [ahead 1]` | 로컬에 원격이 모르는 커밋 1개 | `git push` (올리기) |
| `## main...origin/main [behind 2]` | 원격에 로컬이 모르는 커밋 2개 | `git pull` (받기) |
| `## main...origin/main [ahead 1, behind 2]` | 양쪽 다 갈라짐 (분기) | `git pull` 후 병합/리베이스 → push |
| `## feature/x` (원격 표시 없음) | 아직 원격에 push 안 된 로컬 전용 브랜치 | `git push -u origin feature/x` |

### ⚠️ 가장 중요한 함정: git status는 네트워크를 안 탄다

- `ahead` / `behind` 숫자는 **마지막으로 `git fetch`(또는 pull)한 시점 기준**이다.
- 방금 원격에 새 커밋이 올라왔어도, fetch 전에는 `git status`가 "동기화됨"으로 보일 수 있다.
- 따라서 **"받을 게 있는지" 정확히 확인하려면 먼저 fetch**한다:

```bash
git fetch          # 원격 최신 정보만 가져옴 (내 파일은 안 바뀜)
git status -sb     # 그 다음 상태 확인 → behind면 pull
```

- `git fetch` = 원격 정보만 내려받기 (안전, 워킹트리 변화 없음)
- `git pull` = `git fetch` + 실제 병합(merge) → 내 브랜치에 반영

### 상태별 대응 요약

- **ahead** → 올릴 게 있다 → `git push`
- **behind** → 받을 게 있다 → `git pull`
- **ahead + behind** → 갈라졌다 → `git pull`로 합친 뒤 `git push`
- **원격 표시 없음** → 아직 안 올린 브랜치 → `git push -u origin <브랜치>`

## 브랜치 이름 컨벤션

```
[name]/feature-chat     기능 추가
[name]/fix-scroll       버그 수정
[name]/docs-readme      문서
[name]/chore-ci         설정/빌드
```

## 커밋 메시지 컨벤션 (Conventional Commits)

```
feat:     새 기능
fix:      버그 수정
docs:     문서
refactor: 리팩터링
chore:    설정/빌드 등 잡무
style:    포맷/세미콜론 등 (동작 변화 없음)
test:     테스트 추가/수정
```

예: `feat: 키워드 검색 페이지 추가`, `fix: 채팅 자동 스크롤 오류 수정`

## 자주 쓰는 보조 명령

```bash
git status -sb             # 간결한 상태 + 브랜치 추적 정보
git fetch                  # 원격 최신 정보만 받기 (상태 확인 전에)
git branch -vv             # 로컬 브랜치 + 추적 원격 + ahead/behind
git log --oneline --graph --all -15   # 히스토리 그래프
git switch main            # = git checkout main (최신 git)
git restore <파일>         # 워킹트리 변경 되돌리기
```

## 브랜치 삭제 정리

- 원격(GitHub): PR 머지 화면의 "Delete branch" 버튼
- 로컬 브랜치: `git branch -d <브랜치>` (머지 안 됐으면 -D 강제)
- 로컬의 원격 추적 참조 정리: `git fetch --prune`
