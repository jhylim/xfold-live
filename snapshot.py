"""
XFOLD LIVE 데일리 박제 — board.json → 보드 이미지 PNG + 아카이브
================================================================
사용: python3 snapshot.py [--board ./data/board.json] [--font <ttf/ttc>]
산출:
  archive/YYYY-MM-DD.png   — 플립보드 이미지 (공유·게시판용)
  archive/YYYY-MM-DD.json  — 그날 원본 데이터 (감사용)
  archive/index.json       — 아카이브 목록 (archive.html이 읽음)
박제 원칙: 같은 날짜 파일이 이미 있으면 덮어쓰지 않음 (--force 필요) — 사후 수정 차단.
"""
import json, os, argparse, sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--board', default=os.path.join(HERE, 'data', 'board.json'))
ap.add_argument('--font', default='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
ap.add_argument('--font-mac', default='/System/Library/Fonts/AppleSDGothicNeo.ttc')
ap.add_argument('--force', action='store_true')
a = ap.parse_args()

d = json.load(open(a.board))
date = d.get('as_of', datetime.now().strftime('%Y-%m-%d'))
ARC = os.path.join(HERE, 'archive')
os.makedirs(ARC, exist_ok=True)
png_path = os.path.join(ARC, f'{date}.png')
if os.path.exists(png_path) and not a.force:
    print(f'⛔ {date} 박제가 이미 존재 — 사후 수정 차단 (--force로만 덮어쓰기)'); sys.exit(1)

# ---- 폰트 ----
font_path = a.font if os.path.exists(a.font) else a.font_mac
def F(size):
    return ImageFont.truetype(font_path, size)

# ---- 보드 그리기 (사이트와 동일한 플립 그리드 미감) ----
COLS, CW, CH, GAP, RGAP = 30, 46, 62, 4, 9
PAD = 36
W = PAD*2 + COLS*CW + (COLS-1)*GAP
AMBER=(255,197,66); TXT=(246,246,240); UP=(255,97,87); DOWN=(91,157,255); FLAT=(159,161,167); DIM=(78,80,86)

def ret_col(p):
    if p is None: return DIM
    return FLAT if abs(p) < 0.05 else (UP if p > 0 else DOWN)
def ret_txt(p, pad=7):
    return '--'.rjust(pad) if p is None else (('+' if p > 0 else '') + f'{p:.1f}%').rjust(pad)

rows = []  # 각 행 = [(char, color)] * COLS
def make_row(left_segs, right_segs=()):
    chars = []
    for t, c in left_segs:
        chars += [(ch, c) for ch in t] + [(' ', TXT)]
    right = []
    for t, c in right_segs:
        right += [(ch, c) for ch in t]
    padn = COLS - len(chars) - len(right)
    rows.append((chars + [(' ', TXT)]*max(0, padn) + right)[:COLS])

make_row([('XFOLD LIVE', AMBER)], [(d.get('season',''), AMBER)])
make_row([('XFOLD LIVE BOARD', TXT)], [(date, FLAT)])
rows.append(None)  # 간격
make_row([('ACTIVE POSITIONS', AMBER)])
pos = d.get('positions', [])
for p in pos:
    make_row([(p['code'], TXT), (p['name'], TXT)],
             [(ret_txt(p.get('return_pct')), ret_col(p.get('return_pct'))), (' '+p.get('status','RUN'), FLAT)])
for _ in range(len(pos), d.get('slots', 5)):
    make_row([])
rows.append(None)
avg = d.get('avg_open_return_pct')
if avg is None and pos:
    avg = sum(p.get('return_pct',0) for p in pos)/len(pos)
make_row([('현재 평균 수익률', AMBER)], [(ret_txt(avg, 8), ret_col(avg))])
make_row([('누적 수익률', AMBER)], [(ret_txt(d.get('total_return_pct'), 8), ret_col(d.get('total_return_pct')))])

H = PAD*2 + sum(CH+RGAP if r is not None else 18 for r in rows)
img = Image.new('RGB', (W+28, H+28), (10,11,13))            # 외곽 프레임
dr = ImageDraw.Draw(img)
dr.rounded_rectangle([14,14,W+14,H+14], radius=8, fill=(16,17,20))  # 베젤
f_cell = F(30); f_cell_kr = F(26)

y = 14 + PAD
for r in rows:
    if r is None:
        y += 18; continue
    x = 14 + PAD
    for ch, col in r:
        # 플랩 카드
        dr.rounded_rectangle([x, y, x+CW-2, y+CH], radius=4, fill=(34,36,40))
        dr.rectangle([x, y, x+CW-2, y+CH//2], fill=(42,44,50))           # 윗면 약간 밝게
        dr.line([x, y+CH//2, x+CW-2, y+CH//2], fill=(4,4,5), width=2)    # 힌지
        if ch != ' ':
            f = f_cell_kr if '가' <= ch <= '힣' else f_cell
            bb = dr.textbbox((0,0), ch, font=f)
            dr.text((x + (CW-2-(bb[2]-bb[0]))/2 - bb[0], y + (CH-(bb[3]-bb[1]))/2 - bb[1]), ch, font=f, fill=col)
        x += CW + GAP
    y += CH + RGAP
# 푸터 면책 (이미지에도 — 법적 가드)
foot = '본 데이터는 확률적 결과물이며 최종 투자 책임은 본인에게 있습니다 · XFOLD LIVE'
ff = F(16); bb = dr.textbbox((0,0), foot, font=ff)
dr.text(((img.width-(bb[2]-bb[0]))/2, img.height-24), foot, font=ff, fill=(110,112,118))

img.save(png_path)
# 데이터 박제 + 인덱스
json.dump(d, open(os.path.join(ARC, f'{date}.json'), 'w'), ensure_ascii=False, indent=1)
idx_p = os.path.join(ARC, 'index.json')
try: idx = json.load(open(idx_p))
except Exception: idx = []
idx = [e for e in idx if e.get('date') != date]
idx.append({'date': date, 'total_return_pct': d.get('total_return_pct'),
            'avg_open_return_pct': avg, 'n_positions': len(pos)})
idx.sort(key=lambda e: e['date'], reverse=True)
json.dump(idx, open(idx_p, 'w'), ensure_ascii=False, indent=1)
print(f'✓ 박제 완료: archive/{date}.png + .json (누적 {d.get("total_return_pct")}%)')
