#!/bin/bash
# XFOLD LIVE 발행 — 피드 갱신 → (마감에만) 박제 → git 커밋·푸시 (타임스탬프 증명)
# xfold_daily.sh가 모든 모드에서 호출 (codex ↔ live 싱크). 단독 실행도 가능.
# 사용: ./publish_live.sh [morning|midday|closing]   (기본 closing)
set -e
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
MODE="${1:-closing}"

$PYTHON feed_generator.py --xfold "$HOME/xfold" --out ./data/board.json

# 박제 PNG는 '장 마감 보드'만 — 아침·중간 리딩은 피드 갱신만 하고 봉인하지 않는다
if [ "$MODE" = "closing" ]; then
  $PYTHON snapshot.py || true      # 같은 날짜 재실행이면 박제 거부 (정상)
fi

git add -A
if git diff --cached --quiet; then
  echo "변경 없음 — 발행 생략"
else
  if [ "$MODE" = "closing" ]; then MSG="seal: $(date +%Y-%m-%d) 데일리 박제"; else MSG="sync: $(date '+%Y-%m-%d %H:%M') ${MODE} 리딩 반영"; fi
  git -c user.email="jhylim@gmail.com" -c user.name="XFOLD" commit -m "$MSG"
  git pull --rebase --autostash -q || true
  git push -q
  echo "✓ XFOLD LIVE 발행($MODE): $(date '+%Y-%m-%d %H:%M')"
fi
