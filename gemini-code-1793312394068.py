import io
import os
import textwrap
from typing import Tuple, Union
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

# Category Color Accents (Luxury Dark / Modern Fresh Palette)
CATEGORY_THEMES = {
    "SILK & SAREES": {"accent": "#F59E0B", "pill_bg": "#78350F", "border": "#D97706"},
    "BRIDAL & LEHENGAS": {"accent": "#EC4899", "pill_bg": "#831843", "border": "#DB2777"},
    "FORMAL SHIRTS": {"accent": "#38BDF8", "pill_bg": "#075985", "border": "#0284C7"},
    "CURTAINS & DRAPES": {"accent": "#10B981", "pill_bg": "#064E3B", "border": "#059669"},
    "STAIN RESCUE": {"accent": "#EF4444", "pill_bg": "#7F1D1D", "border": "#DC2626"},
    "LAUNDRY WISDOM": {"accent": "#818CF8", "pill_bg": "#312E81", "border": "#6366F1"},
}

DEFAULT_THEME = {"accent": "#06B6D4", "pill_bg": "#164E63", "border": "#0891B2"}


def get_font(size: int, bold: bool = False):
    """Finds available system fonts on Linux/Render or local machines with safe fallbacks."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "arial.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def safe_rounded_rectangle(draw: ImageDraw.Draw, xy, radius=12, fill=None, outline=None, width=1):
    """Safely renders rounded rectangles or falls back gracefully on older Pillow builds."""
    try:
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    except Exception:
        draw.rectangle(xy, fill=fill, outline=outline, width=width)


class LaundryFlyerRequest(BaseModel):
    tip_number: Union[int, str] = 1
    category: str = "SILK & SAREES"
    headline: str = "Never Spray Perfume Directly on Pure Zari Silk"
    body_text: str = "Alcohol dissolves delicate metallic coatings and causes permanent tarnishing. Mist your scent on skin first, wait 2 minutes, then drape your saree."
    pro_takeaway: str = "Pro Fix: Dry clean pure Zari every 3 wears & store in breathable cotton muslin."
    brand_name: str = "VASANT POWER LAUNDRY"
    brand_tagline: str = "Porbandar's Trusted Garment Care Since 1995"
    cta_text: str = "[ >> ] DROP OFF TODAY & FEEL THE FRESHNESS [ << ]"
    canvas_size: Tuple[int, int] = (1080, 1080)


def generate_laundry_flyer(req: LaundryFlyerRequest) -> io.BytesIO:
    width, height = req.canvas_size

    # 1. Base Canvas (Deep Navy Midnight Luxury Background)
    img = Image.new("RGB", (width, height), color="#0A1128")
    draw = ImageDraw.Draw(img)

    category_key = req.category.strip().upper()
    theme = CATEGORY_THEMES.get(category_key, DEFAULT_THEME)

    # 2. Subtle Geometric Grid Lines for Texture
    grid_spacing = 60
    for gx in range(0, width, grid_spacing):
        draw.line([(gx, 0), (gx, height)], fill="#101D42", width=1)
    for gy in range(0, height, grid_spacing):
        draw.line([(0, gy), (width, gy)], fill="#101D42", width=1)

    # 3. Outer Frame & Glass Border
    margin = 44
    safe_rounded_rectangle(
        draw,
        [(margin, margin), (width - margin, height - margin)],
        radius=28,
        fill="#121F45",
        outline="#1C2D5A",
        width=3
    )
    # Thin Inner Neon Accent
    safe_rounded_rectangle(
        draw,
        [(margin + 6, margin + 6), (width - margin - 6, height - margin - 6)],
        radius=22,
        outline=theme["accent"],
        width=1
    )

    # 4. Top Category & Tip Number Pill (No Emoji Characters)
    top_y = margin + 38
    tip_str = f"TIP #{str(req.tip_number).strip()}  |  {category_key}"
    top_font = get_font(22, bold=True)
    tbbox = draw.textbbox((0, 0), tip_str, font=top_font)
    tw = tbbox[2] - tbbox[0]
    pill_w = tw + 60
    pill_h = 50
    pill_x = (width - pill_w) // 2

    # Drop shadow for top badge
    safe_rounded_rectangle(
        draw,
        [(pill_x + 3, top_y + 4), (pill_x + pill_w + 3, top_y + pill_h + 4)],
        radius=25,
        fill="#050B18"
    )
    safe_rounded_rectangle(
        draw,
        [(pill_x, top_y), (pill_x + pill_w, top_y + pill_h)],
        radius=25,
        fill=theme["pill_bg"],
        outline=theme["border"],
        width=2
    )
    # Left accent indicator dot
    draw.ellipse([(pill_x + 20, top_y + 17), (pill_x + 36, top_y + 33)], fill=theme["accent"])
    draw.text((pill_x + 48, top_y + 13), tip_str, fill="#FFFFFF", font=top_font)

    # 5. Hero Headline
    cur_y = top_y + pill_h + 42
    title_font = get_font(44, bold=True)
    headline_lines = textwrap.wrap(req.headline, width=28)
    for line in headline_lines:
        lbox = draw.textbbox((0, 0), line, font=title_font)
        lw = lbox[2] - lbox[0]
        # Headline drop shadow
        draw.text(((width - lw) // 2 + 2, cur_y + 2), line, fill="#050B18", font=title_font)
        draw.text(((width - lw) // 2, cur_y), line, fill="#FFFFFF", font=title_font)
        cur_y += 56

    # 6. Central Main Body Content Card
    card_margin_x = margin + 40
    card_w = width - (card_margin_x * 2)
    card_y = cur_y + 20
    card_h = 320

    safe_rounded_rectangle(
        draw,
        [(card_margin_x + 4, card_y + 6), (card_margin_x + card_w + 4, card_y + card_h + 6)],
        radius=20,
        fill="#070D1D"
    )
    safe_rounded_rectangle(
        draw,
        [(card_margin_x, card_y), (card_margin_x + card_w, card_y + card_h)],
        radius=20,
        fill="#0F1A3A",
        outline="#243767",
        width=2
    )

    # Body Text (Wrapped paragraph)
    body_font = get_font(26, bold=False)
    body_lines = textwrap.wrap(req.body_text, width=44)
    text_y = card_y + 32
    for bline in body_lines:
        bbox = draw.textbbox((0, 0), bline, font=body_font)
        bw = bbox[2] - bbox[0]
        draw.text(((width - bw) // 2, text_y), bline, fill="#E2E8F0", font=body_font)
        text_y += 38

    # Pro Tip Divider & Highlight Box inside the Card
    pro_box_y = text_y + 14
    pro_box_w = card_w - 50
    pro_box_x = (width - pro_box_w) // 2
    safe_rounded_rectangle(
        draw,
        [(pro_box_x, pro_box_y), (pro_box_x + pro_box_w, card_y + card_h - 24)],
        radius=12,
        fill="#1C2D5A",
        outline=theme["accent"],
        width=1
    )
    pro_font = get_font(21, bold=True)
    pro_lines = textwrap.wrap(req.pro_takeaway, width=50)
    py = pro_box_y + 14
    for pline in pro_lines:
        pbox = draw.textbbox((0, 0), pline, font=pro_font)
        pw = pbox[2] - pbox[0]
        draw.text(((width - pw) // 2, py), pline, fill=theme["accent"], font=pro_font)
        py += 28

    # 7. Action CTA Banner
    cta_w, cta_h = 680, 66
    cta_x = (width - cta_w) // 2
    cta_y = height - margin - 150

    safe_rounded_rectangle(
        draw,
        [(cta_x + 3, cta_y + 4), (cta_x + cta_w + 3, cta_y + cta_h + 4)],
        radius=33,
        fill="#050B18"
    )
    safe_rounded_rectangle(
        draw,
        [(cta_x, cta_y), (cta_x + cta_w, cta_y + cta_h)],
        radius=33,
        fill="#F59E0B"
    )
    cta_font = get_font(24, bold=True)
    cbox = draw.textbbox((0, 0), req.cta_text, font=cta_font)
    cw = cbox[2] - cbox[0]
    draw.text(((width - cw) // 2, cta_y + 19), req.cta_text, fill="#111827", font=cta_font)

    # 8. Branding & Footer Signoff
    brand_font = get_font(24, bold=True)
    br_box = draw.textbbox((0, 0), req.brand_name.upper(), font=brand_font)
    br_w = br_box[2] - br_box[0]
    draw.text(((width - br_w) // 2, height - margin - 62), req.brand_name.upper(), fill="#FFFFFF", font=brand_font)

    tag_font = get_font(18, bold=False)
    tag_box = draw.textbbox((0, 0), req.brand_tagline, font=tag_font)
    tag_w = tag_box[2] - tag_box[0]
    draw.text(((width - tag_w) // 2, height - margin - 32), req.brand_tagline, fill="#94A3B8", font=tag_font)

    # 9. Return Safe RGB Image
    if img.mode != "RGB":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf