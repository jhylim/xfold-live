# XFOLD LIVE — 아키텍처 & 로드맵 (v0.2)

**컨셉**: 수익률로만 말하는 곳. AI 방장 XFOLD가 매일 자기 성적표를 플립 전광판에 박제하고, 검증되면 유저들이 도전하는 배틀로얄 플랫폼.
**브랜드 확정 (2026-06-12)**: **XFOLD LIVE** — 본질이 "XFOLD라는 AI의 검증 쇼 → 팔로워 확보"이므로 캐릭터 중심 네이밍. Phase 2 유저 대결 = **THE ARENA**.
(이름 이력: FLIPTICKER 폐기 — fliptickerapp.com 선점 / XFOLD LIVE 폐기 — 어감 / 도메인 후보: xfold.live)
**브랜드 교체**: `index.html` 상단 CSS 주석 블록 + JS `const BRAND` 한 곳.

## Phase 1 — XFOLD 솔로 PoC (지금)
- 정적 사이트: index.html (전광판) + data/board.json (피드)
- 피드: `feed_generator.py` — xfold 파이프라인 산출물에서 생성, **거래 로그 재계산으로 NAV 교차검증** (master_portfolio.json NAV 버그 교훈: -39.94% vs 실제 -1.36%)
- 하루 3회 판단(08:30/12:30/15:40) 노출 + 마감 시 박제
- 박제: 매일 board.json을 `archive/YYYY-MM-DD.json`으로 복사 + git commit (git 이력 = 조작 불가 증명)
- 배포: 새 GitHub repo + Cloudflare Pages (xfold 저장소와 완전 분리 — 비공개 운용 데이터 격리)

## Phase 1.5 — 신뢰 강화
- KIS 모의계좌 연동 → "증권사 체결 기록" 기반 수익률 (시뮬 → 모의 → 실계좌 공언 로드맵 자체가 콘텐츠)
- 데일리 스냅샷 이미지 자동 생성 (밈·공유용) + 커뮤니티 게시판 박제
- 이메일 통지 (의사결정 3회 + 마감 박제) → jhylim@gmail.com

## Phase 2 — 오픈 배틀로얄 (트랙레코드 확보 후)
- Supabase: 유저 가입 + 포트폴리오 등록 (증권사 연동 or 스크린샷 검증)
- 랭킹 전광판: 닉네임 · 종목 · 수익률(%)만 — 금액 블라인드
- 유저별 보드 페이지 (XFOLD와 동일한 전광판 1인 1보드) + 히스토리 팝업
- 수익화: 프리미엄 구독(분석 리포트·AI 툴) / 전광판 스킨 / 제휴 CPA — 유사투자자문업 신고 후

## 법적 가드 (기획서 §5 박제)
- 절대 단방향: 1:1 상담·비밀 채팅 기능 구현 금지
- 도박성 차단: 참가비→상금 풀 금지, 무료 가상 포인트만
- 면책 문구: 모든 페이지 푸터 고정 ("본 전광판의 데이터와 AI 분석은 확률적 결과물이며...")

## 데이터 계약 (board.json)
```
brand/owner/tagline/as_of/season
total_return_pct (거래로그 재계산) + total_note
positions[]: code/name/weight_pct/return_pct/status(RUN)
recent_exits[]: code/name/return_pct/hold_days/exit/status(EXIT|STOP)
decisions_today[]: time/action/note   ← 하루 3회 판단
disclaimer
```

## 다음 할 일
1. 사용자 디자인 확인 → 톤 조정 (플립 애니메이션·사운드·홀 배경)
2. 새 GitHub repo 생성 + CF Pages 연결 (사용자 1회: repo 생성 권한)
3. xfold_daily.sh 5d 단계로 feed_generator + 아카이브 commit 연결
4. 데일리 박제 게시판 페이지 (archive.html)
5. 이름 최종 확정 시 KIPRIS 상표 검색 + 도메인 등록
