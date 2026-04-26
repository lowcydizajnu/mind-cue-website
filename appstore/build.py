#!/usr/bin/env python3
"""
Build App Store screenshots at 1242×2688 (iPhone 6.5").
Each screenshot pairs a landing-page tagline with one of the app screenshots
inside a realistic phone mockup, on a brand-cream background.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEBSITE = ROOT.parent
SHOTS = WEBSITE / "screenshots"
FONTS = Path("/tmp/appstore-fonts")
OUT = ROOT

W, H = 1242, 2688

# Brand palette (from website/index.html design tokens)
CREAM = (250, 244, 236)         # background
SAND = (244, 232, 219)          # secondary
BRAND = (193, 83, 42)           # terracotta
BRAND_LT = (240, 144, 112)      # salmon
BRAND_PALE = (250, 234, 228)    # blush
TEXT = (26, 14, 8)              # near-black brown
MUTED = (122, 96, 85)           # muted brown

# macOS system fonts — Baskerville (serif) pairs nicely with Avenir Next (sans).
# Using ttc collections with explicit face indices.
FNT_SERIF_PATH = "/System/Library/Fonts/Supplemental/Baskerville.ttc"
FNT_SERIF_IDX = 0       # Regular
FNT_SERIF_IT_IDX = 2    # Italic

FNT_SANS_PATH = "/System/Library/Fonts/Avenir Next.ttc"
FNT_SANS_R_IDX = 7      # Regular
FNT_SANS_M_IDX = 5      # Medium
FNT_SANS_SB_IDX = 2     # Demi Bold


def serif(size, italic=False):
    return ImageFont.truetype(FNT_SERIF_PATH, size, index=FNT_SERIF_IT_IDX if italic else FNT_SERIF_IDX)


def sans(size, weight="r"):
    idx = {"r": FNT_SANS_R_IDX, "m": FNT_SANS_M_IDX, "sb": FNT_SANS_SB_IDX}[weight]
    return ImageFont.truetype(FNT_SANS_PATH, size, index=idx)


def draw_gradient_bg(img):
    """Subtle vertical cream→sand gradient with a soft brand-pale glow at top."""
    base = Image.new("RGB", (W, H), CREAM)
    grad = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        r = int(CREAM[0] * (1 - t) + SAND[0] * t)
        g = int(CREAM[1] * (1 - t) + SAND[1] * t)
        b = int(CREAM[2] * (1 - t) + SAND[2] * t)
        grad.putpixel((0, y), (r, g, b))
    base = grad.resize((W, H))

    # soft radial-ish glow near top (brand pale)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = W // 2, H // 5
    max_r = W
    for r in range(max_r, 0, -40):
        a = int(28 * (1 - r / max_r))
        if a <= 0:
            continue
        gd.ellipse(
            [cx - r, cy - r * 0.65, cx + r, cy + r * 0.65],
            fill=(BRAND_PALE[0], BRAND_PALE[1], BRAND_PALE[2], a),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    base = Image.alpha_composite(base.convert("RGBA"), glow)
    img.paste(base, (0, 0))


def draw_phone(img, screen_path, cx, cy, width):
    """Render a titanium iPhone mockup centered at (cx, cy) with given outer width."""
    aspect = 393 / 852
    height = int(width / aspect)

    # Outer phone body (titanium grey rounded rect with subtle highlight)
    phone = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pd = ImageDraw.Draw(phone)
    radius = int(width * 0.135)
    # frame gradient
    for y in range(height):
        t = y / height
        # sweep dark-light-dark
        if t < 0.5:
            k = t * 2
            r = int(58 + (110 - 58) * k)
        else:
            k = (t - 0.5) * 2
            r = int(110 + (50 - 110) * k)
        pd.line([(0, y), (width, y)], fill=(r, r, r + 2, 255))
    # mask to rounded rect
    mask = Image.new("L", (width, height), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, width, height], radius=radius, fill=255)
    phone.putalpha(mask)

    # Inner screen area
    inset = int(width * 0.025)
    sw = width - 2 * inset
    sh = height - 2 * inset
    s_radius = radius - inset

    # Load and crop the app screenshot to the screen aspect
    src = Image.open(screen_path).convert("RGB")
    src_ratio = src.width / src.height
    screen_ratio = sw / sh
    if src_ratio > screen_ratio:
        # crop sides
        new_w = int(src.height * screen_ratio)
        left = (src.width - new_w) // 2
        src = src.crop((left, 0, left + new_w, src.height))
    else:
        new_h = int(src.width / screen_ratio)
        top = 0  # keep top of UI visible
        src = src.crop((0, top, src.width, top + new_h))
    src = src.resize((sw, sh), Image.LANCZOS)

    screen = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    screen.paste(src, (0, 0))
    smask = Image.new("L", (sw, sh), 0)
    smd = ImageDraw.Draw(smask)
    smd.rounded_rectangle([0, 0, sw, sh], radius=s_radius, fill=255)
    screen.putalpha(smask)
    phone.alpha_composite(screen, (inset, inset))

    # Dynamic Island
    di_w = int(width * 0.30)
    di_h = int(di_w * 0.30)
    di_x = (width - di_w) // 2
    di_y = inset + int(height * 0.022)
    di = Image.new("RGBA", (di_w, di_h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(di)
    dd.rounded_rectangle([0, 0, di_w, di_h], radius=di_h // 2, fill=(0, 0, 0, 255))
    # camera dot
    dot_r = int(di_h * 0.22)
    dd.ellipse(
        [di_w - di_h + dot_r, di_h // 2 - dot_r, di_w - di_h + 3 * dot_r, di_h // 2 + dot_r],
        fill=(20, 30, 50, 255),
    )
    phone.alpha_composite(di, (di_x, di_y))

    # Drop shadow
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        [cx - width // 2 + 12, cy - height // 2 + 36,
         cx + width // 2 + 12, cy + height // 2 + 36],
        radius=radius, fill=(20, 10, 6, 110),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(38))
    img.alpha_composite(shadow)

    img.alpha_composite(phone, (cx - width // 2, cy - height // 2))


def wrap_text(text, font, max_w, draw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_centered_text(draw, text, font, y, color, max_w=None, line_gap=1.05):
    if max_w is None:
        max_w = W - 160
    lines = wrap_text(text, font, max_w, draw)
    sizes = [draw.textbbox((0, 0), ln, font=font) for ln in lines]
    line_hs = [s[3] - s[1] for s in sizes]
    total_h = sum(line_hs) + int(line_hs[0] * (line_gap - 1)) * (len(lines) - 1)
    cy = y
    for ln, lh in zip(lines, line_hs):
        w = draw.textlength(ln, font=font)
        draw.text(((W - w) / 2, cy), ln, font=font, fill=color)
        cy += int(lh * line_gap)
    return cy


def draw_eyebrow(draw, text, y):
    """All-caps tag pill above the headline."""
    f = sans(46, "sb")
    label = text.upper()
    # Add letter-spacing manually
    spacing = 4
    chars = list(label)
    # measure with spacing
    char_widths = [draw.textlength(c, font=f) for c in chars]
    tw = sum(char_widths) + spacing * (len(chars) - 1)
    pad_x, pad_y = 44, 26
    box_w = int(tw + pad_x * 2)
    box_h = 88
    box_x = (W - box_w) // 2
    box_y = y
    # solid pale brand pill
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        radius=box_h // 2,
        fill=BRAND_PALE,
        outline=(BRAND[0], BRAND[1], BRAND[2], 60),
        width=2,
    )
    # draw chars one by one with spacing
    cx = box_x + pad_x
    bbox = f.getbbox("M")
    text_h = bbox[3] - bbox[1]
    cy = box_y + (box_h - text_h) // 2 - bbox[1]
    for ch, cw in zip(chars, char_widths):
        draw.text((cx, cy), ch, font=f, fill=BRAND)
        cx += cw + spacing
    return box_y + box_h


def make_screen(out_name, eyebrow, headline, subtitle, screenshot, italic_word=None):
    img = Image.new("RGBA", (W, H), CREAM + (255,))
    draw_gradient_bg(img)
    draw = ImageDraw.Draw(img)

    # Top stack
    y = 180
    y = draw_eyebrow(draw, eyebrow, y) + 50

    # Headline (serif)
    f_head = serif(140)
    # Render line-by-line so the explicit \n in the data is respected
    for line in headline.split("\n"):
        y = draw_centered_text(draw, line, f_head, y, TEXT, max_w=W - 140, line_gap=1.0)
        y += 4
    y += 32

    # Subtitle (sans, muted)
    f_sub = sans(46, "r")
    y = draw_centered_text(draw, subtitle, f_sub, y, MUTED, max_w=W - 220, line_gap=1.25)

    # Phone mockup
    phone_w = 880
    phone_h = int(phone_w * 852 / 393)
    phone_cy = H - phone_h // 2 + 80  # let bottom of phone bleed off-screen
    draw_phone(img, screenshot, W // 2, phone_cy, phone_w)

    out_path = OUT / out_name
    img.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {out_path.name}  ({out_path.stat().st_size // 1024} KB)")


SCREENS = [
    {
        "out": "01-hero.png",
        "eyebrow": "Privacy-first · Evidence-based",
        "headline": "Prepare your mind\nfor what's next",
        "subtitle": "A behavioural-science companion that meets you before each event — not after.",
        "screenshot": "screen_home.png",
    },
    {
        "out": "02-technique.png",
        "eyebrow": "Right technique, right moment",
        "headline": "Science before\nevery meeting",
        "subtitle": "Breathing, framing, attention resets — matched to what you're walking into.",
        "screenshot": "screen_tip.png",
    },
    {
        "out": "03-learn.png",
        "eyebrow": "Built on peer-reviewed research",
        "headline": "A library that\nrespects your time",
        "subtitle": "Short, evidence-based articles and techniques. No fluff, no streaks, no pressure.",
        "screenshot": "screen_learn.png",
    },
    {
        "out": "04-insights.png",
        "eyebrow": "Patterns you can act on",
        "headline": "Honest insights,\nnot dashboards",
        "subtitle": "See which moments cost you most — and which techniques actually help.",
        "screenshot": "screen_insights.png",
    },
    {
        "out": "05-privacy.png",
        "eyebrow": "On-device by default",
        "headline": "Your day, your data",
        "subtitle": "Journal entries never leave your iPhone. AES-256 encrypted, end-to-end private.",
        "screenshot": "screen_home.png",
    },
]


def main():
    print(f"Building 5 App Store screenshots at {W}×{H}…")
    for s in SCREENS:
        make_screen(
            s["out"],
            s["eyebrow"],
            s["headline"],
            s["subtitle"],
            SHOTS / s["screenshot"],
        )
    print("Done.")


if __name__ == "__main__":
    main()
