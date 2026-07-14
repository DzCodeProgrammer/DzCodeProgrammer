"""
Generate dark.svg + light.svg in Sushmitadasari terminal style
using photo -> ASCII tspans, brown theme, DzCodeProgrammer info.
"""
from pathlib import Path
from html import escape
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import shutil

ROOT = Path(r"C:\Users\GAL'EN\DzCodeProgrammer")
ASSETS = ROOT / "assets"
PHOTO_CANDIDATES = [
    ASSETS / "profile-photo.png",
    Path(r"C:\Users\GAL'EN\.cursor\projects\c-Users-GAL-EN-DzCodeProgrammer\assets\c__Users_GAL_EN_AppData_Roaming_Cursor_User_workspaceStorage_fb88c5932fba3c5a398309dbceccaddc_images_image-b343e7b9-874a-4b4e-beaa-94e89853ceb6.png"),
]

# ASCII density matching reference (wide face)
COLS = 90
ROWS = 54
RAMP = " .:-=+*#%@"  # similar density to reference

def load_photo():
    for p in PHOTO_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("No profile photo found")

def photo_to_ascii(path: Path) -> list[str]:
    img = Image.open(path).convert("L")
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = ImageEnhance.Sharpness(img).enhance(1.2)
    # slightly taller crop bias to shoulders
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = max(0, int((h - side) * 0.05))
    img = img.crop((left, top, left + side, min(top + side, h)))
    img = img.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.25))
    px = img.load()
    lines = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = px[x, y]
            # dark -> denser glyph; gamma expands midtones (glasses/face)
            t = 1.0 - (lum / 255.0)
            t = t ** 0.85
            idx = min(len(RAMP) - 1, int(t * (len(RAMP) - 1) + 0.5))
            chars.append(RAMP[idx])
        lines.append("".join(chars).rstrip())
    return lines

def ascii_tspans(lines: list[str], start_x=30, start_y=79.98, line_h=7.55) -> str:
    out = []
    y = start_y
    for line in lines:
        out.append(
            f'<tspan x="{start_x}" y="{y:.2f}" xml:space="preserve">{escape(line)}</tspan>'
        )
        y += line_h
    return "\n".join(out)

def pad_dots(label: str, value: str, width: int = 42) -> str:
    """Build 'Key: .... Value' dots filler similar to reference."""
    # approximate visual padding for display in SVG only — fixed spaces already in template
    return value

def clip_paths(n=22) -> str:
    parts = []
    for i in range(n):
        y = 26.0 + i * 22.0
        begin = 0.75 + i * 0.115
        parts.append(
            f'<clipPath id="lc{i}"><rect x="500" y="{y:.2f}" width="0" height="24">'
            f'<animate attributeName="width" from="0" to="690" dur="0.38s" begin="{begin:.2f}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
    return "".join(parts)

def info_lines(mode: str) -> str:
    """Right panel lines with typing clip animation."""
    fill = "#dbeafe" if mode == "dark" else "#1E293B"
    rows = [
        ('head', 'dzcode@github', 'cc', ' ——————————————————————————————————————————-—-'),
        ('cc', '. ', 'key', 'Subject', 'cc', ': .......................... ', 'value', 'DzCodeProgrammer'),
        ('cc', '. ', 'key', 'Role', 'cc', ': ............................. ', 'value', 'Full-Stack Developer · Builder'),
        ('cc', '. ', 'key', 'Origin', 'cc', ': ........................... ', 'value', 'Indonesia'),
        ('cc', '. ', 'key', 'Focus', 'cc', ': ............................ ', 'value', 'Web · AI · Creative Systems'),
        ('cc', '. ', 'key', 'Status', 'cc', ': ............ ', 'value', 'Building • Learning • Shipping'),
        ('cc', '. ', 'key', 'ToolChain', 'cc', ': ................. ', 'value', 'VS Code, Cursor, Git, Docker'),
        ('cc', '. ',),
        ('cc', '. ', 'key', 'Core', 'cc', '.', 'key', 'Lang', 'cc', ': .......... ', 'value', 'HTML, CSS, JS, TS, Python, PHP'),
        ('cc', '. ', 'key', 'Core', 'cc', '.', 'key', 'Frontend', 'cc', ': ...... ', 'value', 'React, Vite, Tailwind, shadcn/ui'),
        ('cc', '. ', 'key', 'Core', 'cc', '.', 'key', 'Backend', 'cc', ': ....... ', 'value', 'Node.js, FastAPI, Laravel, REST'),
        ('cc', '. ', 'key', 'Core', 'cc', '.', 'key', 'Database', 'cc', ': ...... ', 'value', 'PostgreSQL, MySQL, Supabase'),
        ('cc', '. ', 'key', 'Core', 'cc', '.', 'key', 'Infra', 'cc', ': ......... ', 'value', 'Docker, GitHub Actions, Vercel'),
        ('cc', '. ',),
        ('accent', '- Contact', 'cc', ' ————————————————————————————————————————————-—-'),
        ('cc', '. ', 'key', 'Grid', 'cc', '.', 'key', 'Mail', 'cc', ': ....................... ', 'value', 'dzikrijombang@gmail.com'),
        ('cc', '. ', 'key', 'Grid', 'cc', '.', 'key', 'Portfolio', 'cc', ': .................. ', 'value', '3-d-portolio-for-me.vercel.app'),
        ('cc', '. ', 'key', 'Grid', 'cc', '.', 'key', 'LinkedIn', 'cc', ': ................... ', 'value', 'dzikri-employe-979742335'),
        ('cc', '. ', 'key', 'Grid', 'cc', '.', 'key', 'Github', 'cc', ': ..................... ', 'value', 'DzCodeProgrammer'),
        ('cc', '. ',),
        ('accent', '- Live Stats', 'cc', ' ————————————————————————————————————————————-—-'),
        ('cc', '. ', 'value', 'See live GitHub stats badges below in README ↓'),
    ]
    ys = [42 + i * 22 for i in range(len(rows))]
    chunks = []
    for i, (row, y) in enumerate(zip(rows, ys)):
        parts = []
        # row is alternating class, text
        it = iter(row)
        for cls, text in zip(it, it):
            parts.append(f'<tspan class="{cls}">{escape(text)}</tspan>')
        # first tspan needs x,y
        inner = "".join(parts)
        # inject x,y into first tspan
        inner = inner.replace("<tspan ", f'<tspan x="520" y="{y}" ', 1)
        chunks.append(
            f'<g clip-path="url(#lc{i})"><text x="520" y="0" fill="{fill}">{inner}</text></g>'
        )
    return "\n".join(chunks)

def build_svg(mode: str, ascii_block: str) -> str:
    # Brown / amber theme (user request) while keeping structure identical
    if mode == "dark":
        ascii0, ascii1 = "#C4A574", "#8B5A2B"
        ascii_anim_a = "#C4A574;#D2B48C;#A67C52;#C4A574"
        ascii_anim_b = "#8B5A2B;#C4A574;#D2B48C;#8B5A2B"
        border0, border1, border2 = "#8B5A2B", "#C4A574", "#A67C52"
        bg0, bg1 = "#1A120B", "#0C0906"
        scan0, scan_mid = "#C4A574", "#E8D5B5"
        scanline = "#D2B48C"
        key = "#C4A574"
        value_fill_note = "dark"
        head = "#D2B48C"
        accent = "#A67C52"
        term = "#8B7355"
        scan_lbl = "#F87171"
        panel = "#C4A574"
        cursor = "#C4A574"
        titlebar = "#1A120B"
        title_op = "0.85"
        panel_fill = "#1A120B"
        panel_op = "0.35"
        blend = "screen"
        scan_op = "0.7"
        border_op = "0.8"
        info = info_lines("dark")
        styles_key = key
        styles_value = "#E5E7EB"
        styles_cc = "#6B5B4F"
        styles_head = head
        styles_accent = "#D97706"
        styles_panel = panel
        styles_cursor = cursor
        light_dot_r, light_dot_y, light_dot_g = "#EF4444", "#F59E0B", "#10B981"
    else:
        ascii0, ascii1 = "#92400E", "#B45309"
        ascii_anim_a = "#92400E;#B45309;#D97706;#92400E"
        ascii_anim_b = "#B45309;#D97706;#92400E;#B45309"
        border0, border1, border2 = "#92400E", "#D97706", "#A67C52"
        bg0, bg1 = "#FFFBEB", "#F5F0E8"
        scan0, scan_mid = "#D97706", "#FBBF24"
        scanline = "#78716C"
        key = "#92400E"
        head = "#B45309"
        accent = "#B45309"
        term = "#78716C"
        scan_lbl = "#DC2626"
        panel = "#B45309"
        cursor = "#D97706"
        titlebar = "#FFFFFF"
        title_op = "0.9"
        panel_fill = "#FFFFFF"
        panel_op = "0.55"
        blend = "multiply"
        scan_op = "0.8"
        border_op = "0.75"
        info = info_lines("light")
        styles_key = "#92400E"
        styles_value = "#1E293B"
        styles_cc = "#94A3B8"
        styles_head = "#B45309"
        styles_accent = "#B45309"
        styles_panel = "#B45309"
        styles_cursor = "#D97706"
        light_dot_r, light_dot_y, light_dot_g = "#F87171", "#FBBF24", "#34D399"

    clips = clip_paths(22)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="610" viewBox="0 0 1180 610">
<defs>
  <linearGradient id="asciiGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{ascii0}">
      <animate attributeName="stop-color" values="{ascii_anim_a}" dur="9s" repeatCount="indefinite"/>
    </stop>
    <stop offset="100%" stop-color="{ascii1}">
      <animate attributeName="stop-color" values="{ascii_anim_b}" dur="9s" repeatCount="indefinite"/>
    </stop>
  </linearGradient>
  <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{border0}"/>
    <stop offset="50%" stop-color="{border1}"/>
    <stop offset="100%" stop-color="{border2}"/>
  </linearGradient>
  <radialGradient id="bgGlow" cx="30%" cy="20%" r="80%">
    <stop offset="0%" stop-color="{bg0}"/>
    <stop offset="100%" stop-color="{bg1}"/>
  </radialGradient>
  <linearGradient id="scanGrad" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="{scan0}" stop-opacity="0"/>
    <stop offset="45%" stop-color="{scan0}" stop-opacity="0.05"/>
    <stop offset="50%" stop-color="{scan_mid}" stop-opacity="0.65"/>
    <stop offset="55%" stop-color="{scan0}" stop-opacity="0.05"/>
    <stop offset="100%" stop-color="{border0}" stop-opacity="0"/>
  </linearGradient>
  <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="1" fill="{scanline}" opacity="0.05"/>
  </pattern>
  <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="4" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <mask id="revealMask" maskUnits="userSpaceOnUse" x="0" y="0" width="1180" height="620">
    <rect x="0" y="0" width="1180" height="0" fill="#fff">
      <animate attributeName="height" from="0" to="560" dur="2.6s" begin="0.2s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
    </rect>
  </mask>
  {clips}
  <style>
    .ascii  {{ font-family: 'Courier New', Consolas, monospace; font-size: 7.4px; fill: url(#asciiGrad); letter-spacing: -0.2px; }}
    .key    {{ font-family: 'Courier New', Consolas, monospace; font-size: 15px; fill: {styles_key}; font-weight: bold; }}
    .value  {{ font-family: 'Courier New', Consolas, monospace; font-size: 15px; fill: {styles_value}; }}
    .cc     {{ font-family: 'Courier New', Consolas, monospace; font-size: 15px; fill: {styles_cc}; }}
    .head   {{ font-family: 'Courier New', Consolas, monospace; font-size: 17px; fill: {styles_head}; font-weight: bold; }}
    .accent {{ font-family: 'Courier New', Consolas, monospace; font-size: 15px; fill: {styles_accent}; font-weight: bold; }}
    text, tspan {{ white-space: pre; }}
    .term-label {{ font-family: 'Courier New', Consolas, monospace; font-size: 12px; fill: {term}; letter-spacing: 0.5px; }}
    .scan-label {{ font-family: 'Courier New', Consolas, monospace; font-size: 10px; fill: {scan_lbl}; letter-spacing: 1px; }}
    .panel-title {{ font-family: 'Courier New', Consolas, monospace; font-size: 11px; fill: {styles_panel}; letter-spacing: 2px; opacity: 0.75; }}
    .cursor-blink {{ fill: {styles_cursor}; }}
  </style>
</defs>

<rect width="1180" height="610" rx="18" fill="url(#bgGlow)"/>
<rect width="1180" height="610" rx="18" fill="url(#scanlines)"/>

<g id="titlebar">
  <rect x="3" y="3" width="1174" height="34" rx="16" fill="{titlebar}" fill-opacity="{title_op}"/>
  <circle cx="24" cy="20" r="5" fill="{light_dot_r}"><animate attributeName="opacity" values="1;0.55;1" dur="4s" repeatCount="indefinite"/></circle>
  <circle cx="42" cy="20" r="5" fill="{light_dot_y}"><animate attributeName="opacity" values="1;0.55;1" dur="4s" begin="0.3s" repeatCount="indefinite"/></circle>
  <circle cx="60" cy="20" r="5" fill="{light_dot_g}"><animate attributeName="opacity" values="1;0.55;1" dur="4s" begin="0.6s" repeatCount="indefinite"/></circle>
  <text x="590" y="25" text-anchor="middle" class="term-label">dzcode@github ~ % ./profile.sh --live</text>
  <circle cx="1122" cy="20" r="4" fill="#F87171">
    <animate attributeName="opacity" values="1;0.15;1" dur="1.1s" repeatCount="indefinite"/>
  </circle>
  <text x="1132" y="24" class="scan-label">SCANNING</text>
</g>

<g transform="translate(0,38)">
  <rect x="14" y="26" width="488" height="468" rx="14" fill="{panel_fill}" fill-opacity="{panel_op}" stroke="url(#borderGrad)" stroke-width="1" opacity="0.4"/>
  <rect x="508" y="10" width="655" height="500" rx="14" fill="{panel_fill}" fill-opacity="{panel_op}" stroke="url(#borderGrad)" stroke-width="1" opacity="0.4"/>
  <text x="30" y="24" class="panel-title">VISUAL.MAP</text>
  <text x="524" y="24" class="panel-title">SYSTEM.INFO</text>

  <g mask="url(#revealMask)">
  <text x="30" y="0" class="ascii">
{ascii_block}
  </text>
  </g>

{info}

  <rect x="522" y="491.0" width="9" height="16" class="cursor-blink" opacity="0">
    <animate attributeName="opacity" values="0;0;1;0;1;0;1;0" keyTimes="0;0.01;0.02;0.3;0.5;0.7;0.85;1" dur="1.4s" begin="3.66s" repeatCount="indefinite"/>
  </rect>
</g>

<rect x="0" y="-70" width="1180" height="70" fill="url(#scanGrad)" opacity="{scan_op}" style="mix-blend-mode:{blend}">
  <animateTransform attributeName="transform" type="translate" from="0 -70" to="0 680" dur="4.2s" repeatCount="indefinite"/>
</rect>

<rect x="3" y="3" width="1174" height="604" rx="16" fill="none" stroke="url(#borderGrad)" stroke-width="2" opacity="{border_op}">
  <animate attributeName="opacity" values="0.5;0.95;0.5" dur="3.2s" repeatCount="indefinite"/>
</rect>
</svg>
'''

def main():
    photo = load_photo()
    dest_photo = ASSETS / "profile-photo.png"
    if photo.resolve() != dest_photo.resolve():
        shutil.copy2(photo, dest_photo)
    lines = photo_to_ascii(dest_photo)
    Path(r"C:\Temp\portrait.txt").write_text("\n".join(lines), encoding="utf-8")
    block = ascii_tspans(lines)
    for mode, name in [("dark", "dark.svg"), ("light", "light.svg")]:
        svg = build_svg(mode, block)
        out = ROOT / name
        out.write_text(svg, encoding="utf-8")
        print(f"Wrote {out} ({out.stat().st_size/1024:.1f} KB)")
    print(f"ASCII lines={len(lines)} cols~={len(lines[0]) if lines else 0}")

if __name__ == "__main__":
    main()
