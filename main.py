#!/usr/bin/env python3
"""THE WORLD IN ONE PAGE — Wednesday 25 November 2026, FULL-DAY EDITION.

A newspaper front page drawn entirely in code. Python standard library only:
own 5x7 bitmap font, own PNG encoder, no photos, no network, deterministic
(two runs produce byte-identical output).

Run:  python3 main.py        -> writes entry.png (1024x1024)
"""

import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette ---
PAPER = (247, 243, 234)
INK = (26, 26, 26)
RED = (178, 34, 34)
BLUE = (28, 68, 128)
GREY = (110, 108, 100)
LIGHT = (232, 226, 212)
MID = (200, 192, 172)
GOLD = (176, 132, 30)
GREEN = (34, 110, 60)

# ------------------------------------------------------------- bitmap font --
# 5x7 glyphs, '#' = ink, '.' = blank. Rendered in ALL CAPS; the normaliser
# below folds accents and punctuation onto glyphs that exist.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),  # placeholder, replaced below
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '~': ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
}
# Em dash, en dash, middle dot and pound sign get their own glyphs.
FONT['—'] = ("00000", "00000", "00000", "11111", "00000", "00000", "00000")
FONT['–'] = ("00000", "00000", "00000", "01110", "00000", "00000", "00000")
FONT['·'] = ("00000", "00000", "00000", "00000", "01100", "01100", "00000")
FONT['£'] = ("00110", "01001", "01000", "11110", "01000", "01001", "11111")

FOLD = {
    'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A', 'Ã': 'A', 'Å': 'A',
    'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
    'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
    'Ó': 'O', 'Ò': 'O', 'Ô': 'O', 'Ö': 'O', 'Õ': 'O',
    'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
    'Ý': 'Y', 'Ñ': 'N', 'Ç': 'C', 'Š': 'S', 'Ž': 'Z',
    'á': 'A', 'à': 'A', 'ä': 'A', 'â': 'A', 'ã': 'A', 'å': 'A',
    'é': 'E', 'è': 'E', 'ê': 'E', 'ë': 'E',
    'í': 'I', 'ì': 'I', 'î': 'I', 'ï': 'I',
    'ó': 'O', 'ò': 'O', 'ô': 'O', 'ö': 'O', 'õ': 'O',
    'ú': 'U', 'ù': 'U', 'û': 'U', 'ü': 'U',
    'ý': 'Y', 'ñ': 'N', 'ç': 'C', 'š': 'S', 'ž': 'Z',
    '’': "'", '‘': "'", '“': '"', '”': '"', '«': '"', '»': '"',
    '…': '.', '•': '·', '−': '-', '×': 'X',
}


def norm(text):
    out = []
    for ch in text:
        if ch in FOLD:
            out.append(FOLD[ch])
        elif ch in FONT:
            out.append(ch)
        elif ch.isalpha():
            out.append(ch.upper())
        else:
            out.append(' ')
    return ''.join(out)


# ---------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c, fill=True):
        if fill:
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self.set(xx, yy, c)
        else:
            for xx in range(x, x + w):
                self.set(xx, y, c)
                self.set(xx, y + h - 1, c)
            for yy in range(y, y + h):
                self.set(x, yy, c)
                self.set(x + w - 1, yy, c)

    def hline(self, x, y, w, c, t=1):
        for yy in range(y, y + t):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def vline(self, x, y, h, c, t=1):
        for xx in range(x, x + t):
            for yy in range(y, y + h):
                self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.set(xx, yy, c)

    def tri(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if den == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / den
                b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / den
                cc = 1 - a - b
                if a >= 0 and b >= 0 and cc >= 0:
                    self.set(xx, yy, c)


def text_w(s, scale):
    return len(norm(s)) * 6 * scale


def draw_text(cv, x, y, s, scale, color):
    s = norm(s)
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == '1':
                    for dy in range(scale):
                        for dx in range(scale):
                            cv.set(cx + col * scale + dx, y + row * scale + dy, color)
        cx += 6 * scale
    return cx


def draw_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, scale, max_w):
    """Greedy word wrap on the normalised text; returns list of lines."""
    s = norm(s)
    words = s.split(' ')
    lines, cur = [], ''
    for wd in words:
        trial = (cur + ' ' + wd).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, s, scale, max_w, color, leading=None):
    lh = leading if leading is not None else 9 * scale
    for ln in wrap(s, scale, max_w):
        draw_text(cv, x, y, ln, scale, color)
        y += lh
    return y


# -------------------------------------------------------------- PNG write ---
def write_png(cv, path):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack('>I', len(data)) + kind + data
        return c + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
           + chunk(b'IDAT', comp) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)

# ----------------------------------------------------------- illustrations --
def illo_ofgem(cv, x, y, w, h):
    """House, lightning bolt, rising bill arrow."""
    cv.rect(x, y, w, h, (255, 250, 235))
    cv.rect(x, y, w, h, MID, fill=False)
    # house
    hx, hy = x + 28, y + 58
    cv.line(hx, hy, hx + 52, hy - 34, INK)
    cv.line(hx + 52, hy - 34, hx + 104, hy, INK)
    cv.rect(hx + 8, hy, 88, 46, INK, fill=False)
    cv.rect(hx + 38, hy + 22, 28, 24, INK, fill=False)
    cv.rect(hx + 16, hy + 12, 18, 16, BLUE, fill=False)
    cv.rect(hx + 70, hy + 12, 18, 16, BLUE, fill=False)
    # lightning bolt
    bx, by = x + w - 78, y + 18
    cv.tri([(bx + 26, by), (bx + 2, by + 52), (bx + 20, by + 52)], GOLD)
    cv.tri([(bx + 14, by + 40), (bx + 38, by + 92), (bx + 20, by + 92)], GOLD)
    # rising arrow + bill
    ax, ay = x + w - 150, y + h - 30
    cv.line(ax, ay, ax + 46, ay - 52, RED)
    cv.tri([(ax + 46, ay - 52), (ax + 34, ay - 44), (ax + 52, ay - 38)], RED)
    draw_text(cv, x + 14, y + 8, "BILLS UP 26%", 2, RED)


def illo_tariffs(cv, x, y, w, h):
    """Cargo ship stacked with crates, big % sign."""
    cv.rect(x, y, w, h, (235, 242, 250))
    cv.rect(x, y, w, h, MID, fill=False)
    # sea
    cv.hline(x + 8, y + h - 22, w - 16, BLUE, 2)
    cv.hline(x + 30, y + h - 14, w - 60, BLUE, 2)
    # hull
    cv.tri([(x + 30, y + h - 34), (x + w - 30, y + h - 34),
            (x + w - 58, y + h - 20)], RED)
    cv.rect(x + 30, y + h - 48, w - 60, 14, RED)
    # crates
    cx0 = x + 52
    for i, (cw, chh) in enumerate([(46, 30), (46, 30), (46, 30)]):
        cv.rect(cx0 + i * 52, y + h - 48 - 34, cw, 30, GOLD, fill=False)
        cv.line(cx0 + i * 52, y + h - 48 - 34, cx0 + i * 52 + 46,
                y + h - 48 - 4, GOLD)
        cv.line(cx0 + i * 52 + 46, y + h - 48 - 34, cx0 + i * 52,
                y + h - 48 - 4, GOLD)
    # funnel + % flag
    cv.rect(x + w - 92, y + 16, 34, 34, INK)
    draw_text(cv, x + w - 88, y + 22, "%", 2, PAPER)
    draw_text(cv, x + 14, y + 8, "16 PARTNERS", 2, BLUE)


def illo_iowa(cv, x, y, w, h):
    """Earth-covered bunker, warning plume drifting south-west."""
    cv.rect(x, y, w, h, (240, 236, 222))
    cv.rect(x, y, w, h, MID, fill=False)
    # ground
    cv.hline(x + 8, y + h - 26, w - 16, INK, 2)
    # bunker mound (centred on the box bottom edge so nothing spills out)
    bx, by = x + 30, y + h
    for r, col in [(44, (120, 110, 90)), (34, (140, 130, 108)), (24, (160, 150, 126))]:
        cv.circle(bx + 60, by, r, col)
    cv.rect(bx, by - 4, 122, 4, INK)
    # warning triangle
    tx, ty = x + w - 96, y + 14
    cv.tri([(tx + 30, ty), (tx, ty + 52), (tx + 60, ty + 52)], GOLD)
    cv.tri([(tx + 30, ty + 8), (tx + 8, ty + 46), (tx + 52, ty + 46)], INK)
    draw_text(cv, tx + 25, ty + 18, "!", 2, GOLD)
    # plume dots drifting left-down
    for i, (px, py, pr) in enumerate([(x + 150, y + 34, 7), (x + 128, y + 52, 9),
                                      (x + 102, y + 70, 11), (x + 74, y + 88, 8)]):
        cv.circle(px, py, pr, GREY)
    draw_text(cv, x + 14, y + 8, "9 A.M. TODAY", 2, RED)


# ------------------------------------------------------------------ data ----
MASTHEAD = "THE WORLD IN ONE PAGE"
SUBTITLE = ("WEDNESDAY 25 NOVEMBER 2026  ·  FULL-DAY EDITION  —  "
            "VERIFIED TO 08:00 UTC")
STRIP = "27 STORIES  ·  3 LEADS  ·  10 SECONDARIES  ·  14 IN BRIEF  ·  8 PINS"

TIMELINE = [
    ("TUE 24 NOV 18:48", "Reuters: US set to unveil new tariffs"),
    ("TUE 24 NOV 23:32", "Abrego Garcia's departure for Spain first reported"),
    ("WED 25 NOV 00:18", "Shenzhou-24 lifts off with Pakistan's first astronaut"),
    ("WED 25 NOV 00:58", "Lamarre-Condon found guilty in Sydney"),
    ("WED 25 NOV 03:56", "Shenzhou-24 docks at Tiangong space station"),
    ("WED 25 NOV MORNING", "Ofgem raises UK price cap 26% to £2,166"),
]

LEADS = [
    dict(kicker="LEAD 1  ·  CONFIRMED TODAY  ·  LONDON",
         illo=illo_ofgem,
         head="UK ENERGY BILLS TO SOAR 26% FROM JANUARY",
         sub=("Ofgem lifts price cap to £2,166 — up £443, highest since "
              "spring 2023; 20m homes hit"),
         facts=[
             "Ofgem CONFIRMED on Wednesday it will raise the household "
             "energy price cap by 26% to £2,166 a year for typical use from "
             "January, up £443 from £1,723.",
             "About 20m households on variable tariffs hit, driven by "
             "soaring wholesale gas prices amid the Middle East conflict. "
             "Highest cap since spring 2023.",
             "Energy Secretary: most households will get £100 towards energy "
             "costs from January to help this winter.",
         ],
         tag="CONFIRMED TODAY",
         src="Sources: Reuters · The Times · Ofgem · BBC"),
    dict(kicker="LEAD 2  ·  EXPECTED  ·  WASHINGTON",
         illo=illo_tariffs,
         head="US SET TO UNVEIL NEW TARIFFS ON 16 PARTNERS",
         sub=("Section 301 probe into \"excess capacity\" — China, EU, India "
              "among targets; rates not settled"),
         facts=[
             "The Trump administration is poised to unveil findings of a probe "
             "into excess industrial capacity in 16 partners. Not announced "
             "by 08:00 UTC.",
             "Targets: China, EU, India, Japan, South Korea, Mexico, Vietnam, "
             "Taiwan, Thailand, Malaysia, Indonesia, Switzerland, Norway, "
             "Singapore, Bangladesh, Cambodia.",
             "Rates NOT settled; USTR to propose duties stacking on existing "
             "tariffs. Caps honoured: 15% EU/Japan/S. Korea, 19% Malaysia, "
             "20% China. Rates 15-25% proposed.",
         ],
         tag="EXPECTED — NOT YET ANNOUNCED",
         src="Sources: Reuters · Bloomberg · FT · Politico · BBC"),
    dict(kicker="LEAD 3  ·  SCHEDULED TODAY  ·  IOWA",
         illo=illo_iowa,
         head="ARMY TO DETONATE 5 TONS OF UNSTABLE EXPLOSIVE IN IOWA",
         sub=("Entire US stockpile of degraded lead azide — 68 drums — goes up "
              "Wednesday morning; court refused to stop it"),
         facts=[
             "Detonation at the Iowa Army Ammunition Plant, Middletown, Wed "
             "9 a.m. local (15:00 UTC), day before Thanksgiving, after a "
             "court refused to halt it.",
             "~5 tons / 68 drums of degraded lead azide, stored 20+ years; "
             "Army says destroying it is the safest option; EPA safeguards "
             "in place. Date moved 3 times.",
             "Governor's emergency proclamation covers 3 counties; residents "
             "in a 5-mile cone urged to relocate; plume may drift south-west "
             "into Missouri.",
         ],
         tag="SCHEDULED TODAY — NOT YET DONE",
         src="Sources: AP · NYT · NBC · Army.mil · Washington Post"),
]

SECONDARIES = [
    ("LEAKED RECORDS PUT RUSSIAN WAR DEAD NEAR 500,000",
     "Rosstat data breached 1 Nov, analysed by exiled outlets: 490,334 registered "
     "dead by end Sep 2026; ~720,000 with the missing. Two figures — do not merge. "
     "BBC · Meduza · Mediazona · The Insider · CNN"),
    ("SHENZHOU-24 DOCKS WITH PAKISTAN'S FIRST ASTRONAUT ABOARD",
     "Launched 00:18 GMT from Jiuquan, docked 03:56 GMT at Tiangong. Zeeshan Ali, "
     "40, first Pakistani in orbit and first foreign visitor to China's station. "
     "Reuters · Xinhua · Nature"),
    ("CHINA PROBES SHANGHAI PARTY BOSS CHEN JINING",
     "Politburo member under investigation for \"severe violations of discipline "
     "and laws\"; fourth Politburo member to fall since 2025; Shanghai leaders "
     "pledged loyalty on Wednesday. Xinhua · Reuters · CNN · WSJ"),
    ("ZELENSKY CONFIRMS UKRAINE HIT RUSSIAN SHIP IN BALTIC",
     "President says Ukraine struck the Sparta II in the Gulf of Finland on Sat "
     "21 Nov, calling it a legitimate target; Norway urges caution. "
     "Bloomberg · Reuters · Ukrinform"),
    ("ASIAN MARKETS CLOSE SHARPLY LOWER",
     "KOSPI -5.6% to 4,725.84, Nikkei -3.6% to 56,502.97, Taiex down over 6% as "
     "TSMC sank 8.1%; AI doubts return. Hang Seng +1% to 22,449.86. AP"),
    ("SYDNEY DOUBLE-MURDER VERDICT",
     "Ex-police officer Beau Lamarre-Condon found guilty of murdering Jesse Baird "
     "and Luke Davies; verdict 00:58 UTC. Guardian · ABC Australia · BBC"),
    ("ABREGO GARCIA LEAVES US FOR SPAIN",
     "Salvadoran whose removal case became a US immigration flashpoint has "
     "departed for Spain. WSJ · AP · NYT · BBC"),
    ("SENEGAL REINSTATED AS AFCON CHAMPIONS",
     "CAS overturns CAF ruling; Morocco vows to fight on. Reuters · BBC · ESPN"),
    ("HUAWEI GUILTY ON TRADE SECRETS, CLEARED OF RACKETEERING",
     "New York jury convicts on conspiracy to steal trade secrets and fraud; "
     "acquits on criminal racketeering. Al Jazeera · BBC"),
    ("CARTAGENA SUPERMARKET SIEGE ENDS",
     "About 25 hostages freed by police after armed men seized an Exito store "
     "fleeing a botched robbery. Straits Times · France 24 · Guardian"),
]

ALSO_ON = [
    "Riyadh — Houthi drone hits tallest tower, 11 wounded. (Reuters · WSJ)",
    "Washington — Democrats reach 259 House seats, most since 1990. (AP)",
    "Indonesia — ~26 miners trapped in flooded mine near Bogor. (Reuters)",
    "Spain — voters go to polls Sunday; PP leads ahead of 29 Nov vote. (CFR)",
    "Colombia — car bomb wounds 20+; president blames ex-FARC. (BBC)",
    "DR Congo — military aircraft missing, rebels claim shoot-down. (BBC)",
    "South Africa — man convicted of trying to join Russia's army. (BBC)",
    "Russia — Putin vows retaliation for refinery strikes. (Al Jazeera)",
    "Iraq — PM orders forces to take Kurdish oilfields. (Al Jazeera)",
    "Aviation — China Southern unit buys 50 Boeing 737-8s. (Al Jazeera)",
    "Nigeria — Emir of Daura, 92, suspended amid allegations. (BBC)",
    "France — Sarkozy and Bruni to face trial. (BBC)",
    "Turkiye — army helicopter crash kills five. (Al Jazeera)",
    "Iran — singer Parastoo Ahmadi given 74 lashes. (BBC · Al Jazeera)",
]

# (label, x fraction, y fraction on the map, short note)
PINS = [
    ("1", 0.22, 0.34, "Washington — tariffs"),
    ("2", 0.17, 0.44, "Iowa — blast"),
    ("3", 0.47, 0.22, "London — price cap"),
    ("4", 0.80, 0.30, "Jiuquan — Shenzhou"),
    ("5", 0.86, 0.52, "Shanghai — probe"),
    ("6", 0.93, 0.78, "Sydney — verdict"),
    ("7", 0.60, 0.48, "Riyadh — tower strike"),
    ("8", 0.92, 0.30, "Seoul/Tokyo — markets"),
]

DATE_CHECK = ("DATE CHECK — the stories below broke on other days and are NOT in "
              "this edition:  KOSPI +5.9% — 24 Nov Asian close  ·  Singapore Q3 GDP "
              "+6.1% — 24 Nov  ·  Nasdaq -1.5%, Nvidia -6% — 24 Nov US close  ·  "
              "Ifo 90.6 — 24 Nov  ·  Gaza strike — 24 Nov  ·  Hormuz tanker attacks "
              "— 24 Nov  ·  Jensen Huang returns as Nvidia CEO — 23 Nov  ·  Sparta II "
              "strike — 21 Nov  ·  Spain snap vote — 29 Nov, called 5 Oct.")

# ------------------------------------------------------------------ layout --
M = 22
CW = W - 2 * M  # 980


def ellipse(cv, cx, cy, rx, ry, c):
    for yy in range(cy - ry, cy + ry + 1):
        for xx in range(cx - rx, cx + rx + 1):
            if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1:
                cv.set(xx, yy, c)


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, (228, 236, 242))
    cv.rect(x, y, w, h, MID, fill=False)
    # Stylised continents (light grey blobs on a pale sea).
    land = (198, 192, 172)
    ellipse(cv, x + int(w * 0.17), y + int(h * 0.32), 52, 24, land)   # N America
    ellipse(cv, x + int(w * 0.27), y + int(h * 0.66), 22, 26, land)   # S America
    ellipse(cv, x + int(w * 0.48), y + int(h * 0.26), 22, 14, land)   # Europe
    ellipse(cv, x + int(w * 0.52), y + int(h * 0.58), 26, 26, land)   # Africa
    ellipse(cv, x + int(w * 0.70), y + int(h * 0.32), 78, 26, land)   # Asia
    ellipse(cv, x + int(w * 0.88), y + int(h * 0.74), 26, 12, land)   # Australia
    # Pins.
    for num, fx, fy, _note in PINS:
        px, py = x + int(w * fx), y + int(h * fy)
        cv.circle(px, py, 8, RED)
        cv.circle(px, py, 8, INK, fill=False)
        draw_text(cv, px - 3, py - 3, num, 1, PAPER)


def draw_lead(cv, x, y, w, lead):
    draw_text(cv, x, y, lead["kicker"], 1, RED)
    y += 12
    lead["illo"](cv, x, y, w, 112)
    y += 120
    y = draw_para(cv, x, y, lead["head"], 2, w, INK, leading=17)
    y += 4
    y = draw_para(cv, x, y, lead["sub"], 1, w, BLUE, leading=9)
    y += 6
    for fact in lead["facts"]:
        y = draw_para(cv, x, y, "·  " + fact, 1, w, INK, leading=9)
        y += 4
    y += 2
    draw_text(cv, x, y, lead["tag"], 1, RED)
    y += 11
    draw_text(cv, x, y, lead["src"], 1, GREY)
    return y + 9


def main():
    cv = Canvas(W, H, PAPER)
    # Outer frame.
    cv.rect(10, 10, W - 20, H - 20, INK, fill=False)
    cv.rect(13, 13, W - 26, H - 26, MID, fill=False)

    # Masthead.
    draw_centered(cv, W // 2, 20, MASTHEAD, 7, INK)
    draw_centered(cv, W // 2, 74, SUBTITLE, 2, INK)
    cv.hline(M, 96, CW, INK, 3)
    cv.hline(M, 101, CW, INK, 1)
    draw_centered(cv, W // 2, 110, STRIP, 2, RED)

    # Timeline strip.
    ty = 132
    cv.rect(M, ty, CW, 78, LIGHT)
    cv.rect(M, ty, CW, 78, MID, fill=False)
    draw_text(cv, M + 10, ty + 6, "THE DAY IN UTC", 2, INK)
    col_w = (CW - 20) // 2
    for i, (tm, ev) in enumerate(TIMELINE):
        col = i % 2
        row = i // 2
        ex = M + 10 + col * col_w
        ey = ty + 26 + row * 16
        draw_text(cv, ex, ey, tm, 1, RED)
        draw_text(cv, ex + text_w(tm + "  ", 1), ey, ev, 1, INK)

    # Leads.
    ly = 222
    cv.hline(M, 216, CW, INK, 2)
    colw = 316
    for i, lead in enumerate(LEADS):
        lx = M + i * (colw + 16)
        draw_lead(cv, lx, ly, colw, lead)
        if i < 2:
            cv.vline(lx + colw + 8, ly, 330, MID, 1)

    # Secondaries.
    sy = 566
    cv.hline(M, sy - 6, CW, INK, 2)
    draw_text(cv, M, sy, "MORE OF THE DAY", 2, INK)
    draw_text(cv, M + text_w("MORE OF THE DAY  ", 2), sy + 2,
              "TEN MORE STORIES FROM WEDNESDAY", 1, GREY)
    iy = sy + 22
    scolw = 480
    for i, (head, fact) in enumerate(SECONDARIES):
        col = i % 2
        row = i // 2
        sx = M + col * (scolw + 20)
        yy = iy + row * 42
        draw_text(cv, sx, yy, "%d." % (i + 1), 1, RED)
        draw_para(cv, sx + 18, yy, head, 1, scolw - 18, INK, leading=9)
        draw_para(cv, sx + 18, yy + 10, fact, 1, scolw - 18, GREY, leading=9)

    # Map + Also on.
    by = 806
    cv.hline(M, by - 6, CW, INK, 2)
    draw_text(cv, M, by, "WHERE IT HAPPENED", 2, INK)
    draw_text(cv, M + 500, by, "ALSO ON", 2, INK)
    draw_map(cv, M, by + 20, 470, 96)
    ly2 = by + 122
    for i, (_n, _fx, _fy, note) in enumerate(PINS):
        col = i % 2
        row = i // 2
        lx = M + col * 240
        lyy = ly2 + row * 9
        draw_text(cv, lx, lyy, note, 1, INK)
    # Also-on list, two columns of seven.
    for i, item in enumerate(ALSO_ON):
        col = i % 2
        row = i // 2
        ax = M + 500 + col * 250
        ay = by + 20 + row * 18
        draw_text(cv, ax, ay, "%d." % (i + 1), 1, RED)
        draw_para(cv, ax + 16, ay, item, 1, 234 - 16, INK, leading=9)

    # Date-check footer.
    fy = 972
    cv.hline(M, fy - 6, CW, INK, 2)
    draw_para(cv, M, fy, DATE_CHECK, 1, CW, RED, leading=10)

    n = write_png(cv, "entry.png")
    print("wrote entry.png (%d bytes)" % n)


if __name__ == "__main__":
    main()
