"""
XFOLD LIVE 피드 생성기 — XFOLD 파이프라인 산출물 → board.json
==============================================================
사용: python3 feed_generator.py [--xfold ~/xfold] [--out ./data/board.json]
연동: xfold_daily.sh 5d 단계로 추가 (15:40 마감 리딩 후 실행 → 박제)

데이터 무결성 원칙 (2026-06-12 버그 교훈):
  master_portfolio.json의 NAV를 그대로 믿지 않는다.
  → 거래 로그(master_trades.json)에서 실현손익을 재계산해 교차 검증.
  → 두 값이 2%p 이상 어긋나면 보드에 '정합 점검 중' 표시 + stderr 경고.
"""
import json, os, sys, argparse
from datetime import datetime

ap = argparse.ArgumentParser()
ap.add_argument('--xfold', default=os.path.expanduser('~/xfold'))
ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'board.json'))
a = ap.parse_args()
X = a.xfold

def j(name, default):
    try:
        return json.load(open(os.path.join(X, name)))
    except Exception:
        return default

trades = j('master_trades.json', {'trades': []}).get('trades', [])
master = j('master_portfolio.json', {})
bal = j('kis_balance.json', {'holdings': []})
trk = j('watchlist_tracking.json', {})
alpha = j('vnext_alpha.json', {})
gate = j('buy_gate_v3.json', {})

# ---- 누적 수익률: 거래 로그 재계산 (방어) ----
seed = master.get('seed', 100_000_000)
realized = sum(t.get('pnl', 0) or 0 for t in trades if t.get('exit_price') is not None)
total_pct = round(100 * realized / seed, 2)
master_pct = master.get('nav_pct')
mismatch = master_pct is not None and abs(master_pct - total_pct) > 2.0
if mismatch:
    print(f'⚠ NAV 불일치: master {master_pct}% vs 거래로그 재계산 {total_pct}% — 보드는 재계산값 사용', file=sys.stderr)

# ---- 보유 포지션 (KIS 잔고 우선, 없으면 마스터) ----
positions = []
for h in bal.get('holdings', []):
    positions.append({
        'code': str(h.get('ticker', ''))[:6], 'name': h.get('name', h.get('ticker', '?')),
        'weight_pct': 20, 'return_pct': round(h.get('pnl_pct', 0) or 0, 1), 'status': 'RUN'})
if not positions:
    for p in master.get('positions_detail', []):
        positions.append({
            'code': str(p.get('ticker', ''))[:6], 'name': p.get('name', '?'),
            'weight_pct': 20, 'return_pct': round(p.get('pnl_pct', 0) or 0, 1), 'status': 'RUN'})

# ---- 현재 평균 수익률 (보유 종목 평균, 무포지션이면 None) ----
avg_open = round(sum(p['return_pct'] for p in positions) / len(positions), 2) if positions else None

# ---- 오늘의 판단 (게이트 + 레짐) ----
reg = alpha.get('regime', {})
park = reg.get('park_pct')
n_go = len(gate.get('go', []) or []) + len(gate.get('go_limit', []) or [])
n_stopped = len(gate.get('stopped', []) or [])
base_note = f"매수 가능 {n_go}건 · 청산 관찰 {n_stopped}건"
park_note = f"현금 파킹 {park}%" if park is not None else "파킹 정보 없음"
action = '매수' if n_go > 0 else '관망'
decisions = [
    {'time': '08:30', 'action': action, 'note': f'{base_note} · {park_note}'},
    {'time': '12:30', 'action': action, 'note': f'중간 점검 · {base_note}'},
    {'time': '15:40', 'action': '박제', 'note': '장 마감 · 오늘의 보드 기록 확정'},
]

out = {
    'brand': 'XFOLD LIVE', 'owner': 'XFOLD',
    'tagline': 'AI가 매일 박제하는 진짜 수익률',
    'as_of': datetime.now().strftime('%Y-%m-%d'),
    'season': 'PRE-SEASON',
    'season_note': '시뮬 검증 구간 — KIS 모의계좌 연동 후 SEASON 1 시작',
    'total_return_pct': total_pct,
    'total_note': '누적 실현손익 기준 (거래 로그 재계산)' + (' · 정합 점검 중' if mismatch else ''),
    'avg_open_return_pct': avg_open,
    'slots': 5,
    'positions': positions,
    'decisions_today': decisions,
    'disclaimer': '본 전광판의 데이터와 AI 분석은 확률적 결과물이며, 최종 투자의 책임은 사용자 본인에게 있습니다.',
}
os.makedirs(os.path.dirname(a.out), exist_ok=True)
json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
print(f"✓ board.json 생성 — 누적 {total_pct}% · 현재평균 {avg_open} · 보유 {len(positions)}")

# ---- 라이브 차트 피드: 종목별 가격 시리즈 + 박제 목표가 + 설정일 ----
def build_charts():
    ledger_state = j('ledger_state.json', {}).get('tickers', {})
    gate = j('buy_gate_v3.json', {})
    diag = {r.get('ticker'): r for r in (j('signal_diagnose.json', []) or []) if isinstance(r, dict)}
    maxbt = j('max_backtest.json', {})
    grow = {}
    for grp in ['go', 'go_limit', 'wait', 'reject', 'stopped']:
        for r in gate.get(grp, []) or []:
            grow[r.get('ticker')] = {**r, '_grp': grp}
    cdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'charts')
    os.makedirs(cdir, exist_ok=True)
    listing = []
    for tk, rec in trk.items():
        pf = os.path.join(X, 'prices', f'{tk}.json')
        if not os.path.exists(pf):
            continue
        try:
            series = json.load(open(pf)).get('data', [])
        except Exception:
            continue
        fx = rec.get('fixed', {})
        st = rec.get('status', '') or ''
        levels = []
        sd = rec.get('signal_date', '')
        def L(key, label, color):
            v = fx.get(key)
            if v: levels.append({'price': v, 'label': label, 'set_date': sd, 'color': color})
        L('entry_1', '1차 매수', '#C0392B'); L('entry_2', '2차 매수', '#D98880'); L('entry_3', '3차 매수', '#E8B4AE')
        L('avg_cost', '평단', '#6B7280'); L('stop', '손절', '#B08D3C')
        L('target_1', '1차 익절', '#1F4E8C'); L('target_2', '2차 익절', '#7FA3D1'); L('target_3', '3차 익절', '#A9C4E3')
        # ---- 투자 근거 (공개용 — 구조는 공개, 세부 변수는 비공개 원칙) ----
        g = grow.get(tk, {})
        d = diag.get(tk, {})
        mb = maxbt.get(tk, {})
        nm = rec.get('name', tk)
        stage = d.get('stage') or g.get('stage') or ''
        checks = []
        if g:
            n_cyc, win, cum = g.get('n_cyc'), g.get('win'), g.get('cum')
            checks.append({'k': '패턴 자격', 'ok': bool(g.get('g1')),
                           't': (f"10년 사이클 {n_cyc}회 · 적중 {win:.0f}% · 누적 {cum}×"
                                 if g.get('g1') and n_cyc else '10년 검증 기준 미달')})
            checks.append({'k': '시동 신호', 'ok': bool(g.get('g2')),
                           't': '매집 종료 후 시동 신호 발화' if g.get('g2') else '시동 신호 대기 중'})
            checks.append({'k': '진입 타이밍', 'ok': bool(g.get('g3')),
                           't': '추격이 아닌 진입 구간' if g.get('g3')
                               else (f"현재 '{stage}' 구간 — 추격 매수 금지" if stage else '진입 구간 아님')})
            checks.append({'k': '시장 상태', 'ok': gate.get('slot_mode') != 'LIMIT',
                           't': f"거시 모드 {gate.get('slot_mode', '-')} · 동시 운용 {gate.get('slot_count', '-')}슬롯"})
        call = ''
        if mb:
            call = (f"{nm}은(는) 10년 데이터에서 매집→분출 사이클이 {mb.get('n_trades', '-')}회 반복된 종목. "
                    f"과거 사이클 평균 +{mb.get('avg_ret_pct', '-')}% · 최고 +{mb.get('best_ret_pct', '-')}% · "
                    f"평균 보유 {mb.get('avg_hold', '-')}일.")
        if sd:
            call += f" {sd} 신호 시점에 매수·목표·손절가가 박제되었다."
        rationale = {'engine': 'CYCLE', 'stage': stage, 'verdict': g.get('verdict'),
                     'call': call.strip(), 'checks': checks,
                     'weight_pct': 20,
                     'expected_hold': (f"{fx.get('hold_range_min')}~{fx.get('hold_range_max')}일"
                                       if fx.get('hold_range_min') else None)}
        json.dump({'ticker': tk, 'name': rec.get('name', tk), 'status': st,
                   'signal_date': sd, 'version': ledger_state.get(tk, {}).get('version', 1),
                   'levels': levels, 'rationale': rationale,
                   'hold_min': fx.get('hold_range_min'), 'hold_max': fx.get('hold_range_max'),
                   'data': series[-500:]},
                  open(os.path.join(cdir, tk.replace('.', '_') + '.json'), 'w'), ensure_ascii=False)
        listing.append({'ticker': tk, 'name': rec.get('name', tk), 'status': st})
    json.dump(listing, open(os.path.join(cdir, 'index.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'✓ 차트 피드 {len(listing)}종목')

trk = j('watchlist_tracking.json', {})
build_charts()
