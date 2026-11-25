#!/usr/bin/env python3
"""news-image-20261125, morning edition.

Draws a newspaper front page summing up Wednesday 25 November 2026
(morning edition, stories verified to 02:15 UTC) as a 1024x1024 PNG.
Pure Python standard library: own 5x7 bitmap font, own canvas, own
PNG encoder. No network, no files read, deterministic output.
Writes entry.png next to this script, or to $MAKEFUN_OUTPUT_DIR, or
to /output when that directory exists.
"""

import binascii
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font
# Each glyph: 7 rows of 5 cells, '#' = ink. Uppercase + digits + punct.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "$": ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
}


def glyph(ch):
    return FONT.get(ch, FONT["?"])


def text_w(s, sc):
    """Pixel width of string s at font scale sc."""
    if not s:
        return 0
    return len(s) * 6 * sc - sc


def wrap(s, maxw, sc):
    """Greedy word wrap; returns list of lines, each <= maxw px."""
    words = s.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = wd if not cur else cur + " " + wd
        if text_w(trial, sc) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
PAPER = (247, 242, 226)
INK = (25, 25, 25)
RED = (178, 35, 27)
GREY = (107, 107, 107)
SEA = (222, 233, 236)
LAND = (207, 224, 184)
RULE = (25, 25, 25)


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * w * h)

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            for xx in range(max(0, x), min(self.w, x + w)):
                self.px[base], self.px[base + 1], self.px[base + 2] = c
                base += 3

    def hline(self, x0, x1, y, c, th=1):
        self.rect(x0, y, x1 - x0, th, c)

    def vline(self, x, y0, y1, c, th=1):
        self.rect(x, y0, th, y1 - y0, c)

    def frame(self, x, y, w, h, c, th=1):
        self.hline(x, x + w, y, c, th)
        self.hline(x, x + w, y + h - th, c, th)
        self.vline(x, y, y + h, c, th)
        self.vline(x + w - th, y, y + h, c, th)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
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
                d = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
                if fill:
                    if d <= r * r:
                        self.put(xx, yy, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.put(xx, yy, c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon."""
        pts = [(int(px), int(py)) for px, py in pts]
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.put(x, y, c)

    def text(self, x, y, s, sc, c, align="l"):
        s = s.upper()
        if align == "c":
            x -= text_w(s, sc) // 2
        elif align == "r":
            x -= text_w(s, sc)
        cx = x
        for ch in s:
            g = glyph(ch)
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.rect(cx + col * sc, y + row * sc, sc, sc, c)
            cx += 6 * sc
        return cx

    def para(self, x, y, s, maxw, sc, c, lh=None):
        """Wrapped paragraph; returns y after the last line."""
        if lh is None:
            lh = 7 * sc + 2
        for ln in wrap(s, maxw, sc):
            self.text(x, y, ln, sc, c)
            y += lh
        return y


# ---------------------------------------------------------------- png
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    return out + struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", ihdr)
    data += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


# ---------------------------------------------------------------- content
# All facts from the morning-edition spec (verified to 02:15 UTC).
# Text is upper-cased at draw time where needed; keep strings short so
# they wrap to the planned number of lines at scale 2.

LEADS = [
    {
        "kicker": "TARIFFS - UNITED STATES",
        "head": "US SET TO UNVEIL NEW TARIFFS ON 16 PARTNERS",
        "sub": "Section 301 probe. China, EU, India targeted.",
        "facts": [
            "Trump team poised to unveil probe findings.",
            "Rates not settled. USTR to propose new duties.",
            "Caps kept: 15% EU, Japan, S. Korea; 19% Malaysia.",
        ],
        "tag": "EXPECTED - NOT ANNOUNCED",
        "src": "REUTERS - BLOOMBERG - FT - POLITICO - BBC",
        "art": "bars",
    },
    {
        "kicker": "BLAST - IOWA, USA",
        "head": "ARMY TO DETONATE 5 TONS OF EXPLOSIVE",
        "sub": "68 drums of degraded lead azide go up Wed. a.m.",
        "facts": [
            "Controlled blast at Iowa plant, 9 a.m. local.",
            "Court refused a bid to halt it. Governor acted.",
            "Plume maps: lead dust may drift to Missouri.",
        ],
        "tag": "SCHEDULED TODAY, NOT DONE",
        "src": "AP - NYT - NBC - ARMY.MIL - WASHINGTON POST",
        "art": "bunker",
    },
    {
        "kicker": "WAR DEAD - RUSSIA",
        "head": "LEAKED RECORDS PUT RUSSIAN WAR DEAD NEAR 500,000",
        "sub": "Hacked Rosstat data. 490,334 registered dead.",
        "facts": [
            "Breach 1 Nov by Cyber Partisans, Silent Crow.",
            "490,334 dead to Sep 2026. With missing, 720,000.",
            "Rosstat denies breach. CNN cannot verify alone.",
        ],
        "tag": "LEAKED DATA - 5 NEWSROOMS",
        "src": "BBC - MEDUZA - MEDIAZONA - THE INSIDER - CNN",
        "art": "ledger",
    },
]

# Secondaries: (headline, fact, source). Fact wraps to 2 lines.
SECONDARIES = [
    ("SYDNEY VERDICT",
     "Ex-officer Lamarre-Condon guilty of murdering Jesse Baird and Luke Davies.",
     "GUARDIAN - ABC - BBC"),
    ("ABREGO GARCIA LEAVES US",
     "Salvadoran at the centre of a US immigration fight has left for Spain.",
     "WSJ - AP - NYT - BBC"),
    ("EISENKOT FINDS PARTNER",
     "Yashar signs a coalition pact with Lieberman's Yisrael Beiteinu in Israel.",
     "AP - AL JAZEERA"),
    ("SENEGAL CHAMPIONS AGAIN",
     "CAS restores Senegal as AFCON winners. Morocco to fight on.",
     "REUTERS - BBC - ESPN"),
    ("HUAWEI: GUILTY, THEN NOT",
     "Jury convicts on trade-secret conspiracy, acquits on racketeering.",
     "AL JAZEERA - BBC"),
    ("CARTAGENA SIEGE ENDS",
     "About 25 hostages freed after gunmen seized an Exito supermarket.",
     "STRAITS TIMES - FRANCE 24"),
    ("ALASKA ENDS VOTER DEAL",
     "State stops sharing voter rolls with the Trump Justice Department.",
     "ABC - DEMOCRACY DOCKET"),
    ("OFGEM CAP DUE TODAY",
     "UK regulator sets January cap. Analysts see a 26% rise, bill GBP 2,166.",
     "BBC - INDEPENDENT"),
    ("ASIAN MARKETS OPEN LOWER",
     "Nikkei -2.99% at 56,889; KOSPI -4.72% at 4,770. Mid-session, not closes.",
     "YAHOO FINANCE"),
    ("HOUTHIS THREATEN PORTS",
     "Houthis say they will hit Jeddah and Saudi Red Sea ports if Hodeidah is hit.",
     "ANI - AL JAZEERA - UNCONFIRMED"),
]

TIMELINE = [
    ("TUE 18:48", "REUTERS: US SET TO UNVEIL NEW TARIFFS"),
    ("TUE 22:34", "JURY RETIRES IN SYDNEY MURDER TRIAL"),
    ("TUE 23:32", "ABREGO GARCIA DEPARTURE FIRST REPORTED"),
    ("WED 00:27", "PLUME MAPS: DUST MAY REACH MO."),
    ("WED 00:58", "LAMARRE-CONDON FOUND GUILTY IN SYDNEY"),
    ("WED 02:07", "WAPO: DANGER SIGNS AT IOWA PLANT"),
]

ALSO = [
    "COLOMBIA: CAR BOMB WOUNDS 20+. EX-FARC BLAMED.",
    "DR CONGO: MILITARY PLANE MISSING. REBELS CLAIM IT.",
    "S. AFRICA: MAN HELD OVER RUSSIA FIGHT PLAN.",
    "PUTIN: RETALIATION INEVITABLE AFTER OIL STRIKES.",
    "IRAQ: PM ORDERS TROOPS TO TAKE KURDISH OILFIELDS.",
    "AVIATION: CHINA SOUTHERN TO BUY 50 BOEING 737-8S.",
    "NIGERIA: EMIR OF DAURA, 92, SUSPENDED OVER CLAIMS.",
    "FRANCE: SARKOZY AND BRUNI TO FACE TRIAL IN NEW CASE.",
    "TURKIYE: ARMY HELICOPTER CRASH KILLS FIVE.",
    "IRAN: SINGER AND 3 MUSICIANS GET 74 LASHES.",
    "BANGLADESH: HASINA SAYS SHE WILL RETURN 16 DEC.",
    "NATO: CHIEF VOWS SPACE DEFENCE AFTER WARHEAD TALK.",
    "SYRIA: LAND-MINE VICTIMS SOAR, 1,000 CHILDREN HIT.",
    "ISRAEL: POLICE SEIZE MOSQUE SPEAKERS IN PRAYER ROW.",
]

# Map pins: (number, label, lon, lat)
PINS = [
    (1, "WASHINGTON", -77, 39),
    (2, "IOWA", -93, 42),
    (3, "MOSCOW", 37, 56),
    (4, "SYDNEY", 151, -34),
    (5, "CARTAGENA", -75, 10),
    (6, "DAKAR", -17, 15),
    (7, "LONDON", 0, 51),
    (8, "TOKYO/SEOUL", 133, 37),
]

DATECHECK = [
    "KOSPI +5.9% - 24 NOV",
    "SINGAPORE GDP +6.1% - 24 NOV",
    "NASDAQ -1.5%, NVIDIA -6% - 24 NOV",
    "IFO 90.6 - 24 NOV",
    "GAZA STRIKE - 24 NOV",
    "HORMUZ TANKERS - 24 NOV",
    "HUANG RETURNS AS NVIDIA CEO - 23 NOV",
]


# ---------------------------------------------------------------- layout
MX = 16          # left margin (inside the frame)
CW = 320         # lead column width
COLX = [16, 348, 680]


def draw_bars(cv, x, y, w, h):
    """16 partner bars, red for the three biggest, grey for the rest."""
    cv.frame(x, y, w, h, INK)
    heights = [16, 22, 13, 25, 19, 10, 21, 15, 27, 18, 12, 24, 9, 19, 13, 16]
    bw = 12
    for i, hh in enumerate(heights):
        bx = x + 6 + i * 18
        col = RED if i in (3, 8, 11) else GREY
        cv.rect(bx, y + h - 4 - hh, bw, hh, col)
    cv.hline(x, x + w, y + h - 4, INK)
    cv.text(x + w - 52, y + 4, "16", 2, RED)


def draw_bunker(cv, x, y, w, h):
    """Earth-covered magazine, drums, warning triangle, plume arrow."""
    cv.frame(x, y, w, h, INK)
    cv.rect(x + 8, y + 22, 90, h - 26, (90, 70, 50))
    cv.poly([(x + 8, y + 22), (x + 53, y + 4), (x + 98, y + 22)], (120, 95, 65))
    for r in range(2):
        for c in range(4):
            cv.circle(x + 22 + c * 20, y + 30 + r * 9, 4, (40, 40, 40))
    cx, cy = x + 186, y + 18
    cv.poly([(cx, cy - 10), (cx + 12, cy + 10), (cx - 12, cy + 10)], RED)
    cv.text(cx - 2, cy - 4, "!", 1, (255, 255, 255))
    cv.text(x + 124, y + 26, "68 DRUMS", 1, INK)
    cv.line(x + 210, y + 24, x + 300, y + 24, GREY)
    cv.line(x + 300, y + 24, x + 292, y + 19, GREY)
    cv.line(x + 300, y + 24, x + 292, y + 29, GREY)
    cv.text(x + 210, y + 30, "PLUME TO MO.", 1, GREY)


def draw_ledger(cv, x, y, w, h):
    """Registry ledger rows with the two toll figures."""
    cv.frame(x, y, w, h, INK)
    for r in range(4):
        yy = y + 6 + r * 9
        cv.hline(x + 8, x + w - 8, yy, GREY)
    cv.text(x + 10, y + 4, "490,334", 3, RED)
    cv.text(x + 150, y + 12, "REGISTERED DEAD", 1, INK)
    cv.text(x + 10, y + 26, "ABOUT 720,000 WITH MISSING", 1, GREY)


ART = {"bars": draw_bars, "bunker": draw_bunker, "ledger": draw_ledger}


def draw_lead(cv, lead, x, y0):
    cv.text(x, y0 + 2, lead["kicker"], 2, RED)
    y = y0 + 20
    for ln in wrap(lead["head"], CW, 3):
        cv.text(x, y, ln, 3, INK)
        y += 22
    y += 2
    y = cv.para(x, y, lead["sub"], CW, 2, INK, lh=16)
    y += 2
    ART[lead["art"]](cv, x, y, CW, 32)
    y += 36
    for f in lead["facts"]:
        y = cv.para(x, y, f, CW, 2, INK, lh=16)
    y += 2
    cv.text(x, y, lead["tag"], 2, RED)
    y += 16
    cv.text(x, y, lead["src"], 1, GREY)
    return y + 11


def draw_secondaries(cv, y0):
    cols = [16, 520]
    for i, (head, fact, src) in enumerate(SECONDARIES):
        col = i % 2
        row = i // 2
        x = cols[col]
        y = y0 + row * 58
        cv.text(x, y, head, 2, INK)
        y += 16
        y = cv.para(x, y, fact, 488, 2, INK, lh=15)
        cv.text(x, y + 3, src, 1, GREY)


def draw_timeline(cv, y0):
    cv.text(16, y0, "THE DAY IN UTC", 2, RED)
    for i, (tm, txt) in enumerate(TIMELINE):
        col = i % 3
        row = i // 3
        x = [16, 348, 680][col]
        y = y0 + 18 + row * 31
        lines = wrap(tm + " - " + txt, 320, 2)
        yy = y
        for ln in lines:
            cv.text(x, yy, ln, 2, INK)
            yy += 15


# Coarse continent outlines in (lon, lat), equirectangular.
NA = [(-168, 66), (-150, 70), (-130, 71), (-110, 72), (-95, 69), (-85, 66),
      (-76, 60), (-65, 60), (-60, 47), (-70, 42), (-76, 35), (-81, 26),
      (-84, 30), (-90, 21), (-97, 16), (-105, 20), (-114, 28), (-124, 40),
      (-124, 48), (-135, 58), (-155, 58), (-165, 60)]
SA = [(-79, 9), (-72, 4), (-60, -2), (-50, -5), (-40, -8), (-35, -18),
      (-40, -28), (-48, -32), (-58, -38), (-65, -45), (-70, -52),
      (-72, -42), (-74, -30), (-78, -18), (-81, -8), (-80, 2)]
AF = [(-17, 33), (-10, 35), (-2, 35), (9, 37), (20, 32), (30, 31),
      (36, 27), (43, 12), (48, 11), (42, 2), (40, -8), (36, -18),
      (32, -28), (26, -33), (18, -35), (14, -28), (12, -18), (9, -4),
      (9, 4), (-8, 5), (-14, 11)]
EUAS = [(-9, 37), (-2, 43), (0, 46), (8, 44), (12, 44), (18, 40),
        (23, 36), (28, 36), (30, 41), (36, 36), (42, 41), (48, 44),
        (52, 46), (58, 50), (66, 54), (72, 58), (80, 62), (90, 68),
        (100, 72), (110, 73), (125, 72), (140, 72), (155, 70), (170, 67),
        (178, 65), (170, 60), (162, 56), (158, 50), (150, 45), (142, 42),
        (135, 38), (127, 35), (122, 30), (118, 25), (110, 20), (108, 12),
        (104, 8), (100, 7), (97, 10), (94, 16), (90, 22), (86, 20),
        (80, 15), (77, 8), (74, 15), (70, 20), (66, 25), (60, 25),
        (56, 27), (52, 28), (50, 30), (48, 38), (44, 41), (40, 44),
        (36, 36), (30, 40), (26, 38), (22, 36), (18, 40), (12, 44),
        (8, 38), (2, 37), (-6, 36)]
AU = [(113, -22), (114, -30), (120, -34), (129, -32), (137, -35),
      (142, -38), (150, -37), (153, -27), (146, -19), (142, -11),
      (136, -12), (130, -13), (124, -14), (117, -20)]


def draw_map(cv, x0, y0, w, h):
    cv.frame(x0, y0, w, h, INK)
    cv.rect(x0 + 1, y0 + 1, w - 2, h - 2, SEA)

    def proj(lon, lat):
        return (x0 + 4 + (lon + 170) / 360.0 * (w - 8),
                y0 + 4 + (75 - lat) / 135.0 * (h - 28))

    for cont in (NA, SA, AF, EUAS, AU):
        cv.poly([proj(lo, la) for lo, la in cont], LAND)
    for num, _name, lon, lat in PINS:
        px, py = proj(lon, lat)
        px, py = int(px), int(py)
        cv.circle(px, py, 8, RED)
        cv.circle(px, py, 8, INK, fill=False)
        cv.text(px - 3, py - 3, str(num), 1, (255, 255, 255))
    return y0 + h


def build():
    cv = Canvas(W, H, PAPER)
    cv.frame(8, 8, W - 16, H - 16, INK, 2)
    cv.frame(12, 12, W - 24, H - 24, INK, 1)

    # Masthead.
    cv.text(W // 2, 20, "THE WORLD IN ONE DAY", 3, INK, align="c")
    cv.text(W // 2, 44, "WEDNESDAY 25 NOVEMBER 2026", 5, RED, align="c")
    cv.text(W // 2, 86, "MORNING EDITION - STORIES VERIFIED TO 02:15 UTC - ALL TIMES UTC",
            2, GREY, align="c")
    cv.text(W // 2, 104, "27 STORIES - 6 CONTINENTS - 3 LEADS - 10 SECONDARIES - 14 ALSO ON",
            2, INK, align="c")
    cv.hline(16, 1008, 120, INK, 2)

    # Timeline.
    draw_timeline(cv, 126)
    cv.hline(16, 1008, 206, INK, 2)

    # Three leads.
    for lead, x in zip(LEADS, COLX):
        draw_lead(cv, lead, x, 212)
    cv.hline(16, 1008, 496, INK, 2)

    # Secondaries, two columns x five rows.
    draw_secondaries(cv, 502)
    cv.hline(16, 1008, 794, INK, 2)

    # Map + ALSO.
    cv.text(16, 800, "WHERE IT HAPPENED", 2, RED)
    draw_map(cv, 16, 816, 352, 156)
    cv.text(20, 940, "1 WASHINGTON  2 IOWA  3 MOSCOW  4 SYDNEY", 1, INK)
    cv.text(20, 950, "5 CARTAGENA  6 DAKAR  7 LONDON  8 TOKYO/SEOUL", 1, INK)
    cv.text(392, 800, "ALSO ON THIS DAY", 2, RED)
    for i, item in enumerate(ALSO):
        col = i // 7
        row = i % 7
        x = 392 + col * 308
        y = 818 + row * 22
        lines = wrap("%d. %s" % (i + 1, item), 304, 1)
        yy = y
        for ln in lines[:2]:
            cv.text(x, yy, ln, 1, INK)
            yy += 10

    # Date check footer.
    cv.hline(16, 1008, 976, INK, 2)
    cv.text(16, 980, "DATE CHECK - NOT TODAY, LEFT OUT ON PURPOSE (ALL 24 NOV, HUANG 23 NOV)",
            2, RED)
    cv.text(16, 998, "KOSPI +5.9% / SINGAPORE GDP +6.1% / NASDAQ -1.5% / IFO 90.6 / GAZA STRIKE / HORMUZ TANKERS / HUANG RETURNS AS NVIDIA CEO",
            1, INK)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else "."
    path = os.path.join(outdir, "entry.png")
    cv = build()
    n = write_png(cv, path)
    print("wrote %s (%d bytes)" % (path, n))


if __name__ == "__main__":
    main()
