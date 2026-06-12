#!/bin/bash
# XFOLD LIVE 데일리 발행 — 피드 갱신 → 박제 → git 커밋·푸시 (타임스탬프 증명)
# xfold_daily.sh closing 단계에서 호출. 단독 실행도 가능.
set -e
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"

$PYTHON feed_generator.py --xfold "$HOME/xfold" --out ./data/board.json
$PYTHON snapshot.py || true        # 같은 날짜 재실행이면 박제 거부 (정상)

git add -A
if git diff --cached --quiet; then
  echo "변경 없음 — 발행 생략"
else
  git -c user.email="jhylim@gmail.com" -c user.name="XFOLD" \
    commit -m "seal: $(date +%Y-%m-%d) 데일리 박제"
  git push -q
  echo "✓ XFOLD LIVE 발행: $(date '+%Y-%m-%d %H:%M')"
fi
