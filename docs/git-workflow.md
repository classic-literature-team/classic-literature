# Git 워크플로 (GitHub Flow)
ㅅ
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

## 브랜치 이름 컨벤션

```
song/feature-chat     기능 추가
song/fix-scroll       버그 수정
song/docs-readme      문서
song/chore-ci         설정/빌드
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
git status                 # 현재 상태 확인
git branch -vv             # 로컬 브랜치 + 추적 원격 확인
git log --oneline --graph --all -15   # 히스토리 그래프
git switch main            # = git checkout main (최신 git)
git restore <파일>         # 워킹트리 변경 되돌리기
```

## 브랜치 삭제 정리

- 원격(GitHub): PR 머지 화면의 "Delete branch" 버튼
- 로컬 브랜치: `git branch -d <브랜치>` (머지 안 됐으면 -D 강제)
- 로컬의 원격 추적 참조 정리: `git fetch --prune`
