"""Builds the profile README's SVG assets with Iosevka outlined to paths.

Usage: python scripts/build.py assets

Needs fonttools and uharfbuzz (scripts/requirements.txt) and Iosevka Nerd Font in ~/Library/Fonts.
"""
import os
import re
import sys

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_DIR = os.path.expanduser("~/Library/Fonts")

# Catppuccin Macchiato (dark) and Latte (light). purple is mauve, cyan is sky,
# surface and ink are the agnoster segment background and text.
THEMES = {
    "dark": {
        "bg": "#24273a", "panel": "#1e2030", "line": "#363a4f", "fg": "#cad3f5",
        "comment": "#6e738d", "blue": "#8aadf4", "purple": "#c6a0f6", "cyan": "#91d7e3",
        "green": "#a6da95", "orange": "#f5a97f", "red": "#ed8796", "yellow": "#eed49f",
        "surface": "#494d64", "ink": "#181926", "sub": "#a5adcb",
        "glow": 0.26,
    },
    "light": {
        "bg": "#dce0e8", "panel": "#eff1f5", "line": "#ccd0da", "fg": "#4c4f69",
        "comment": "#9ca0b0", "blue": "#1e66f5", "purple": "#8839ef", "cyan": "#04a5e5",
        "green": "#40a02b", "orange": "#fe640b", "red": "#d20f39", "yellow": "#df8e1d",
        "surface": "#ccd0da", "ink": "#eff1f5", "sub": "#6c6f85",
        "glow": 0.20,
    },
}


class Face:
    def __init__(self, weight):
        path = os.path.join(FONT_DIR, f"IosevkaNerdFont-{weight}.ttf")
        self.tt = TTFont(path)
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        with open(path, "rb") as f:
            self.hb_font = hb.Font(hb.Face(f.read()))

    def _shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf, {"calt": False, "liga": False})
        return buf.glyph_infos, buf.glyph_positions

    def width(self, text, size):
        _, pos = self._shape(text)
        return sum(p.x_advance for p in pos) * size / self.upem

    def path(self, text, x, y, size):
        """Returns (svg path data, advance width) for text with its baseline at (x, y)."""
        infos, pos = self._shape(text)
        s = size / self.upem
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        cx = 0
        for info, p in zip(infos, pos):
            gx = x + (cx + p.x_offset) * s
            gy = y - p.y_offset * s
            self.glyphs[self.order[info.codepoint]].draw(TransformPen(pen, (s, 0, 0, -s, gx, gy)))
            cx += p.x_advance
        return pen.getCommands(), cx * s


REGULAR = Face("Regular")
BOLD = Face("Bold")


def text(face, s, x, y, size, fill, anchor="start"):
    if anchor == "middle":
        x -= face.width(s, size) / 2
    elif anchor == "end":
        x -= face.width(s, size)
    d, w = face.path(s, x, y, size)
    return f'<path fill="{fill}" d="{d}"/>', x + w


def runs(face, parts, x, y, size):
    """Draws coloured runs one after another on one line; returns (svg, end x)."""
    out = []
    for s, fill in parts:
        p, x = text(face, s, x, y, size, fill)
        out.append(p)
    return "".join(out), x


def agnoster(t, x, cy, size=20):
    """Draws an oh-my-zsh agnoster prompt (user@host, dir, git branch) centred on cy; returns (svg, end x)."""
    segs = [("sam@pariat", t["surface"], t["fg"]), ("~", t["blue"], t["ink"]), (" main", t["green"], t["ink"])]
    h, pad = 32, 12
    arrow = h / 2
    top, bottom = cy - h / 2, cy + h / 2
    base = cy + size * 0.36
    rects, arrows, labels = [], [], []
    for i, (s, bg, fg) in enumerate(segs):
        lead = arrow if i else 0
        w = lead + pad + REGULAR.width(s, size) + pad
        rects.append(f'<rect x="{x:.1f}" y="{top}" width="{w:.1f}" height="{h}" fill="{bg}"/>')
        labels.append(text(REGULAR, s, x + lead + pad, base, size, fg)[0])
        x += w
        arrows.append(f'<path fill="{bg}" d="M{x:.1f} {top}L{x + arrow:.1f} {cy}L{x:.1f} {bottom}z"/>')
    return "".join(rects + arrows + labels), x + arrow + 12


def svg(w, h, label, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{label}"><title>{label}</title>{body}</svg>'
    )


def banner(t):
    w, h = 1280, 360
    o = [
        "<defs>",
        f'<clipPath id="panel"><rect width="{w}" height="{h}" rx="28"/></clipPath>',
        f'<radialGradient id="glowA" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{t["blue"]}" stop-opacity="{t["glow"]}"/><stop offset="1" stop-color="{t["blue"]}" stop-opacity="0"/></radialGradient>',
        f'<radialGradient id="glowB" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{t["purple"]}" stop-opacity="{t["glow"]}"/><stop offset="1" stop-color="{t["purple"]}" stop-opacity="0"/></radialGradient>',
        f'<linearGradient id="name" x1="0" x2="1"><stop offset="0" stop-color="{t["blue"]}"/><stop offset="1" stop-color="{t["purple"]}"/></linearGradient>',
        f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.4" fill="{t["comment"]}" opacity="0.35"/></pattern>',
        "</defs>",
        '<g clip-path="url(#panel)">',
        f'<rect width="{w}" height="{h}" fill="{t["bg"]}"/>',
        f'<rect width="{w}" height="{h}" fill="url(#dots)"/>',
        '<ellipse cx="360" cy="150" rx="420" ry="220" fill="url(#glowA)"/>',
        '<ellipse cx="960" cy="230" rx="420" ry="200" fill="url(#glowB)"/>',
        "</g>",
    ]

    # Terminal window.
    tx, ty, tw, th = 80, 40, 1120, 280
    o.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="16" fill="{t["panel"]}" stroke="{t["line"]}" stroke-width="2"/>')
    o.append(f'<line x1="{tx}" y1="{ty + 44}" x2="{tx + tw}" y2="{ty + 44}" stroke="{t["line"]}" stroke-width="2"/>')
    for i, c in enumerate(("red", "yellow", "green")):
        o.append(f'<circle cx="{tx + 28 + i * 22}" cy="{ty + 22}" r="6.5" fill="{t[c]}"/>')
    o.append(text(REGULAR, "sam@pariat: ~", tx + tw / 2, ty + 28, 16, t["comment"], "middle")[0])

    # Left column: prompt, name, tagline, live prompt.
    lx = tx + 44
    p, end = agnoster(t, lx, 120)
    o.append(p)
    o.append(text(REGULAR, "whoami", end, 120 + 20 * 0.36, 20, t["fg"])[0])
    o.append(text(BOLD, "Sam Pariat", lx - 3, 206, 76, "url(#name)")[0])
    o.append(runs(REGULAR, [("Software engineer", t["fg"]), ("  /  ", t["comment"]), ("New Delhi", t["fg"])], lx, 244, 24)[0])
    p, end = agnoster(t, lx, 284)
    o.append(p)
    o.append(
        f'<rect x="{end:.1f}" y="272" width="12" height="24" fill="{t["fg"]}">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>'
    )

    # Right column: a fetch-style key/value block.
    sx = 740
    o.append(f'<line x1="{sx}" y1="{ty + 76}" x2="{sx}" y2="{ty + th - 32}" stroke="{t["line"]}" stroke-width="2"/>')
    kx, vx = sx + 44, sx + 44 + 92
    rows = [
        ("role", "SDE 1 @ Max Healthcare"),
        ("client", "TypeScript, React Native"),
        ("server", "Go, PostgreSQL"),
        ("theme", "Catppuccin Macchiato"),
        ("font", "Iosevka"),
    ]
    for i, (k, v) in enumerate(rows):
        y = 134 + i * 34
        o.append(text(REGULAR, k, kx, y, 20, t["blue"])[0])
        o.append(text(REGULAR, v, vx, y, 20, t["fg"])[0])
    for i, c in enumerate(("red", "orange", "yellow", "green", "cyan", "blue", "purple")):
        o.append(f'<rect x="{kx + i * 30}" y="{134 + 5 * 34 - 14}" width="22" height="12" rx="3" fill="{t[c]}"/>')

    return svg(w, h, "Sam Pariat, software engineer in New Delhi", "".join(o))


PROJECTS = {
    "roundup": {
        "title": "roundup", "repo": "SamPariat/roundup",
        "label": "roundup: the weekend planner for your squad",
        "pitch": ("The weekend planner for your squad: pick the place, see who's coming,",
                  "split the bill and remember the night."),
        "langs": ("go",),
        "chips": (("Go", "cyan"), ("Fiber", "blue"), ("PostgreSQL", "blue"), ("OpenAPI", "green"), ("Casbin", "orange"), ("Expo", "purple")),
    },
    "cinesuggest": {
        "title": "CineSuggest", "repo": "SamPariat/movie-recommendation-sm",
        "label": "CineSuggest: movie recommendations and review sentiment",
        "pitch": ("Movie recommendations by cosine similarity, with Bernoulli Naive Bayes",
                  "reading the sentiment of every review."),
        "langs": ("typescript", "python", "jupyter", "dart"),
        "chips": (("Python", "yellow"), ("scikit-learn", "orange"), ("NLTK", "green"), ("Flask", "cyan"), ("NestJS", "red"), ("Remix", "blue"), ("Flutter", "purple")),
    },
}


def frame(t, w, h):
    """The shared card panel: rounded fill, blue to mauve accent bar on the left, hairline border."""
    return [
        f'<defs><clipPath id="c"><rect width="{w}" height="{h}" rx="24"/></clipPath>'
        f'<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["blue"]}"/><stop offset="1" stop-color="{t["purple"]}"/></linearGradient></defs>',
        '<g clip-path="url(#c)">',
        f'<rect width="{w}" height="{h}" fill="{t["panel"]}"/>',
        f'<rect width="10" height="{h}" fill="url(#bar)"/>',
        "</g>",
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="23" fill="none" stroke="{t["line"]}" stroke-width="2"/>',
    ]


def card(theme, t, pr):
    w, h = 1280, 250
    o = frame(t, w, h)

    # Language icons, right-aligned on the title row, each in a rounded tile.
    tile, gap = 46, 12
    lx = w - 64 - len(pr["langs"]) * (tile + gap) + gap
    for i, lang in enumerate(pr["langs"]):
        x0 = lx + i * (tile + gap)
        o.append(f'<rect x="{x0}" y="46" width="{tile}" height="{tile}" rx="12" fill="{t["bg"]}" stroke="{t["line"]}" stroke-width="2"/>')
        o.append(icon(theme, t, lang, x0 + 11, 57, 24))
    x = 64
    p, end = text(BOLD, pr["title"], x, 88, 52, t["fg"])
    o.append(p)
    o.append(text(REGULAR, pr["repo"], end + 20, 88, 22, t["comment"])[0])
    for i, line in enumerate(pr["pitch"]):
        o.append(text(REGULAR, line, x, 134 + i * 32, 24, t["fg"])[0])

    cx = x
    for label, c in pr["chips"]:
        cw = REGULAR.width(label, 18) + 28
        o.append(f'<rect x="{cx:.1f}" y="190" width="{cw:.1f}" height="34" rx="17" fill="none" stroke="{t[c]}" stroke-width="2"/>')
        o.append(text(REGULAR, label, cx + 14, 213, 18, t[c])[0])
        cx += cw + 12
    o.append(text(REGULAR, "view repo ->", w - 64, 213, 20, t["blue"], "end")[0])
    return svg(w, h, pr["label"], "".join(o))


ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
FLAVOUR = {"dark": "macchiato", "light": "latte"}

# Catppuccin VSCode Icons has no Expo or LinkedIn icon, so they are drawn in the same 16px line style.
DRAWN = {
    "linkedin": '<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
                '<path stroke="{blue}" d="M3 .5h10A2.5 2.5 0 0 1 15.5 3v10a2.5 2.5 0 0 1-2.5 2.5H3A2.5 2.5 0 0 1 .5 13V3A2.5 2.5 0 0 1 3 .5"/>'
                '<path stroke="{fg}" d="M4.5 7v4.5m0-7v0m3 7V7m0 2a2 2 0 0 1 4 0v2.5"/></g>',
    "expo": '<path fill="none" stroke="{fg}" stroke-linecap="round" stroke-linejoin="round" '
            'd="M1.5 13.5 7.13 3.5a1 1 0 0 1 1.74 0l5.63 10M4.5 13.5l3.07-5.25a.5.5 0 0 1 .86 0l3.07 5.25"/>',
}

STACK = (
    ("client", "blue", (("TypeScript", "typescript"), ("JavaScript", "javascript"),
                        ("React Native", "typescript-react"), ("Expo", "expo"), ("Next.js", "next"),
                        ("Tailwind CSS", "tailwind"), ("Flutter", "flutter"))),
    ("backend", "cyan", (("Go", "go"), ("Node.js", "npm"), ("NestJS", "nest"), ("PostgreSQL", "database"))),
    ("infra", "purple", (("Docker", "docker"), ("AWS", "folder_aws"), ("Redis", "database"))),
)

EXPERIENCE = (
    ("Max Healthcare", "SDE 1", True),
    ("Infinite Locus", "Software engineer, after an internship", False),
    ("HCL InfoTech", "Intern, at a subsidiary of HCL InfoSystems", False),
)


def icon(theme, t, name, x, y, size):
    """Inlines a Catppuccin icon at (x, y), scaled from its viewBox to size."""
    vb = 16
    if name in DRAWN:
        inner = DRAWN[name].format(**t)
    else:
        with open(os.path.join(ICON_DIR, FLAVOUR[theme], f"{name}.svg")) as f:
            src = f.read()
        vb = float(re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+)', src).group(1))
        inner = src[src.index(">") + 1:src.rindex("</svg>")].strip()
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({size / vb:g})">{inner}</g>'


def stack(theme, t):
    w, h = 1280, 400
    o = frame(t, w, h)
    y = 74
    for label, c, items in STACK:
        p, end = text(BOLD, label, 64, y, 22, t[c])
        o.append(p)
        o.append(f'<line x1="{end + 16:.1f}" y1="{y - 7}" x2="{w - 64}" y2="{y - 7}" stroke="{t["line"]}" stroke-width="2"/>')
        cx = 64
        for name, ic in items:
            cw = 14 + 20 + 9 + REGULAR.width(name, 18) + 16
            o.append(f'<rect x="{cx:.1f}" y="{y + 20}" width="{cw:.1f}" height="44" rx="22" fill="{t["bg"]}" stroke="{t["line"]}" stroke-width="2"/>')
            o.append(icon(theme, t, ic, cx + 14, y + 32, 20))
            o.append(text(REGULAR, name, cx + 43, y + 48, 18, t["fg"])[0])
            cx += cw + 9
        assert cx <= w - 54, f"{label} row overflows: {cx:.0f}"
        y += 112
    names = ", ".join(n for _, _, items in STACK for n, _ in items)
    return svg(w, h, f"Stack: {names}", "".join(o))


def experience(t):
    w, h = 1280, 340
    rail = 88
    o = frame(t, w, h)
    rows = [84 + i * 96 for i in range(len(EXPERIENCE))]
    o.append(f'<line x1="{rail}" y1="{rows[0] - 8}" x2="{rail}" y2="{rows[-1] - 8}" stroke="{t["line"]}" stroke-width="2"/>')
    for (company, role, current), y in zip(EXPERIENCE, rows):
        dy = y - 9
        if current:
            o.append(
                f'<circle cx="{rail}" cy="{dy}" r="10" fill="{t["green"]}" opacity="0.35">'
                '<animate attributeName="r" values="10;18;10" dur="2.4s" repeatCount="indefinite"/>'
                '<animate attributeName="opacity" values="0.35;0;0.35" dur="2.4s" repeatCount="indefinite"/></circle>'
            )
            o.append(f'<circle cx="{rail}" cy="{dy}" r="9" fill="{t["green"]}"/>')
            pw = REGULAR.width("current", 18) + 32
            o.append(f'<rect x="{w - 64 - pw:.1f}" y="{dy - 17}" width="{pw:.1f}" height="34" rx="17" fill="none" stroke="{t["green"]}" stroke-width="2"/>')
            o.append(text(REGULAR, "current", w - 64 - pw + 16, dy + 6, 18, t["green"])[0])
        else:
            o.append(f'<circle cx="{rail}" cy="{dy}" r="8" fill="{t["panel"]}" stroke="{t["comment"]}" stroke-width="2.5"/>')
        o.append(text(BOLD, company, rail + 40, y, 30, t["fg"])[0])
        o.append(text(REGULAR, role, rail + 40, y + 34, 21, t["sub"])[0])
    label = "Experience: " + "; ".join(f"{c}, {r}" for c, r, _ in EXPERIENCE)
    return svg(w, h, label, "".join(o))


def link(theme, t):
    """A pill-shaped LinkedIn link in the card style."""
    h, size, pad = 64, 22, 26
    parts = [("LinkedIn", BOLD, t["fg"]), ("  /  ", REGULAR, t["comment"]), ("Sam Pariat", REGULAR, t["fg"]), ("   ->", REGULAR, t["blue"])]
    w = pad + 26 + 14 + sum(f.width(s, size) for s, f, _ in parts) + pad
    o = [f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2}" rx="{h / 2 - 1}" fill="{t["panel"]}" stroke="{t["line"]}" stroke-width="2"/>',
         icon(theme, t, "linkedin", pad, (h - 26) / 2, 26)]
    x = pad + 26 + 14
    for s, f, c in parts:
        p, x = text(f, s, x, h / 2 + size * 0.36, size, c)
        o.append(p)
    return svg(round(w), h, "LinkedIn: Sam Pariat", "".join(o))


NAV = ("experience", "stack", "featured")


def summary(t):
    """The one-line summary under the banner, as a wide card."""
    w, h, size = 1280, 104, 26
    o = frame(t, w, h)
    parts = [("Software engineer in New Delhi", BOLD, t["fg"]), (", building mobile clients and the services behind them.", REGULAR, t["sub"])]
    x = (w - sum(f.width(s, size) for s, f, _ in parts)) / 2
    for s, f, c in parts:
        p, x = text(f, s, x, h / 2 + size * 0.36, size, c)
        o.append(p)
    return svg(w, h, "Software engineer in New Delhi, building mobile clients and the services behind them.", "".join(o))


def nav(t, name):
    """One section link: a pill reading '# name'."""
    h, size, pad = 52, 22, 24
    w = pad + REGULAR.width("# ", size) + REGULAR.width(name, size) + pad
    o = [f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2}" rx="{h / 2 - 1}" fill="{t["panel"]}" stroke="{t["line"]}" stroke-width="2"/>']
    o.append(runs(REGULAR, [("# ", t["purple"]), (name, t["fg"])], pad, h / 2 + size * 0.36, size)[0])
    return svg(round(w), h, name.capitalize(), "".join(o))


def divider():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 6" width="1200" height="6" preserveAspectRatio="none" role="presentation">'
        '<defs><linearGradient id="g" x1="0" x2="1">'
        '<stop offset="0" stop-color="#8aadf4" stop-opacity="0"/><stop offset="0.2" stop-color="#8aadf4"/>'
        '<stop offset="0.5" stop-color="#c6a0f6"/><stop offset="0.8" stop-color="#91d7e3"/>'
        '<stop offset="1" stop-color="#91d7e3" stop-opacity="0"/></linearGradient></defs>'
        '<rect y="1" width="1200" height="4" rx="2" fill="url(#g)"/></svg>'
    )


def main(out):
    os.makedirs(out, exist_ok=True)
    files = {"divider.svg": divider()}
    for name, t in THEMES.items():
        files[f"banner-{name}.svg"] = banner(t)
        files[f"stack-{name}.svg"] = stack(name, t)
        files[f"experience-{name}.svg"] = experience(t)
        files[f"linkedin-{name}.svg"] = link(name, t)
        files[f"summary-{name}.svg"] = summary(t)
        for section in NAV:
            files[f"nav-{section}-{name}.svg"] = nav(t, section)
        for key, pr in PROJECTS.items():
            files[f"{key}-card-{name}.svg"] = card(name, t, pr)
    for fn, body in files.items():
        with open(os.path.join(out, fn), "w") as f:
            f.write(body)
        print(fn, len(body))


if __name__ == "__main__":
    main(sys.argv[1])
