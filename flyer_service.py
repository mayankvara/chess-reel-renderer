import io
import textwrap
from typing import List, Tuple, Optional
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont


# ==========================================
# 1. Pydantic Models
# ==========================================

class BusinessFlyerRequest(BaseModel):
    business_name: str = "Vasant Power Laundry"
    tagline: str = "Crisp • Clean • Express Care"
    headline: str = "Premium Laundry & Steam Pressing"
    subheadline: str = "Fast turnaround, hygienic washing, and door-to-door convenience."
    services: List[str] = [
        "Wash & Fold",
        "Steam Ironing / Pressing",
        "Dry Cleaning Care",
        "Curtain & Blanket Deep Clean"
    ]
    offer_badge: str = "Starting at ₹99 / Month / Plans Available"
    phone_or_whatsapp: str = "+91 XXXXXXXXXX"
    address_line: str = "Porbandar, Gujarat"
    cta_text: str = "Drop Off Today / WhatsApp for Pickup"
    canvas_size: Tuple[int, int] = (1080, 1080)


class ChessQuoteFlyerRequest(BaseModel):
    quote: str
    player: str
    designation: str = "World Champion"
    branding: str = "Chess Players Ahmedabad"
    canvas_size: Tuple[int, int] = (1080, 1080)


# ==========================================
# 2. Font Loading Helper (Render / Linux / Windows Safe)
# ==========================================

def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """
    Safely resolves system fonts across Render/Ubuntu, Debian, Windows, and macOS.
    Falls back gracefully without crashing.
    """
    candidates = [
        # Linux / Render standard DejaVu paths
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # Windows standard
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        # Generic name lookup
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf"
    ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue

    # Safe fallback if no true-type font found
    return ImageFont.load_default()


# ==========================================
# 3. Business Flyer Generator (Vasant Laundry)
# ==========================================

def render_business_flyer_image(req: BusinessFlyerRequest) -> bytes:
    width, height = req.canvas_size
    img = Image.new("RGB", (width, height), color="#F4F8FB")
    draw = ImageDraw.Draw(img)

    margin = 50

    # Top Brand Header Box
    header_h = 160
    draw.rectangle([(0, 0), (width, header_h)], fill="#0F2942")

    brand_font = get_font(46, bold=True)
    draw.text((margin, 35), req.business_name.upper(), fill="#FFFFFF", font=brand_font)

    tagline_font = get_font(24, bold=False)
    draw.text((margin, 95), req.tagline, fill="#38BDF8", font=tagline_font)

    # Offer Badge Banner
    if req.offer_badge:
        badge_y = header_h + 35
        badge_font = get_font(26, bold=True)
        draw.rounded_rectangle(
            [(margin, badge_y), (width - margin, badge_y + 55)],
            radius=12,
            fill="#F59E0B"
        )
        draw.text((margin + 20, badge_y + 12), req.offer_badge.upper(), fill="#0F172A", font=badge_font)

    # Headline & Subheadline
    content_y = header_h + 125
    head_font = get_font(44, bold=True)
    head_lines = textwrap.wrap(req.headline, width=28)
    for line in head_lines:
        draw.text((margin, content_y), line, fill="#0F2942", font=head_font)
        content_y += 55

    content_y += 10
    sub_font = get_font(24, bold=False)
    sub_lines = textwrap.wrap(req.subheadline, width=50)
    for line in sub_lines:
        draw.text((margin, content_y), line, fill="#475569", font=sub_font)
        content_y += 35

    # Services Checklist
    content_y += 20
    draw.text((margin, content_y), "OUR POPULAR SERVICES", fill="#00A896", font=get_font(26, bold=True))
    content_y += 45

    svc_font = get_font(28, bold=True)
    for svc in req.services:
        draw.text((margin + 10, content_y), "✓", fill="#00A896", font=svc_font)
        draw.text((margin + 45, content_y), svc, fill="#1E293B", font=svc_font)
        content_y += 48

    # Bottom Footer Card
    footer_h = 170
    footer_top = height - footer_h
    draw.rectangle([(0, footer_top), (width, height)], fill="#0F2942")

    # CTA Button
    cta_font = get_font(26, bold=True)
    cta_bbox = draw.textbbox((0, 0), req.cta_text, font=cta_font)
    cta_w = cta_bbox[2] - cta_bbox[0]
    draw.rounded_rectangle(
        [(margin, footer_top + 25), (margin + cta_w + 40, footer_top + 80)],
        radius=14,
        fill="#00A896"
    )
    draw.text((margin + 20, footer_top + 38), req.cta_text, fill="#FFFFFF", font=cta_font)

    # Contact & Address
    contact_font = get_font(26, bold=True)
    addr_font = get_font(22, bold=False)
    draw.text((margin, footer_top + 98), f"📞 {req.phone_or_whatsapp}", fill="#F8FAFC", font=contact_font)
    draw.text((margin + 360, footer_top + 101), f"📍 {req.address_line}", fill="#94A3B8", font=addr_font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


# ==========================================
# 4. Chess Master Quote Flyer Generator
# ==========================================

def render_chess_quote_image(req: ChessQuoteFlyerRequest) -> bytes:
    width, height = req.canvas_size
    img = Image.new("RGB", (width, height), color="#0F172A")  # Slate dark background
    draw = ImageDraw.Draw(img)

    margin = 48
    draw.rounded_rectangle(
        [(margin, margin), (width - margin, height - margin)],
        radius=24,
        outline="#334155",
        width=3
    )

    # Decorative Quotation Mark
    quote_mark_font = get_font(180, bold=True)
    draw.text((margin + 40, margin + 20), "“", fill="#F59E0B", font=quote_mark_font)

    # Auto-adjust Quote Font Size
    quote_clean = req.quote.strip('“”"')
    font_size = 56 if len(quote_clean) < 95 else 44
    font_quote = get_font(font_size, bold=True)

    wrap_width = 28 if font_size == 56 else 34
    lines = textwrap.wrap(quote_clean, width=wrap_width)
    wrapped_text = "\n".join(f'"{line}' if i == 0 else line for i, line in enumerate(lines))
    if not wrapped_text.endswith('"'):
        wrapped_text += '"'

    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font_quote, spacing=18)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    quote_x = (width - text_w) // 2
    quote_y = 360 - (text_h // 3)

    draw.multiline_text(
        (quote_x, quote_y),
        wrapped_text,
        fill="#FFFFFF",
        font=font_quote,
        spacing=18,
        align="center"
    )

    # Author & Accent Line
    author_y = quote_y + text_h + 70
    line_w = 80
    draw.line(
        [((width - line_w) // 2, author_y), ((width + line_w) // 2, author_y)],
        fill="#F59E0B",
        width=4
    )

    font_author = get_font(40, bold=True)
    author_name = req.player.upper()
    abbox = draw.textbbox((0, 0), author_name, font=font_author)
    draw.text(((width - (abbox[2] - abbox[0])) // 2, author_y + 24), author_name, fill="#FBBF24", font=font_author)

    if req.designation:
        font_desig = get_font(26, bold=False)
        dbbox = draw.textbbox((0, 0), req.designation, font=font_desig)
        draw.text(((width - (dbbox[2] - dbbox[0])) // 2, author_y + 76), req.designation, fill="#94A3B8", font=font_desig)

    # Footer Branding Tag
    font_brand = get_font(26, bold=True)
    brand_text = f"♟ {req.branding.upper()} • DAILY INSPIRATION"
    bbbox = draw.textbbox((0, 0), brand_text, font=font_brand)
    bw, bh = bbbox[2] - bbbox[0], bbbox[3] - bbbox[1]

    pill_y = height - margin - 75
    draw.rounded_rectangle(
        [((width - bw) // 2 - 24, pill_y - 8), ((width + bw) // 2 + 24, pill_y + bh + 8)],
        radius=14,
        fill="#1E293B"
    )
    draw.text(((width - bw) // 2, pill_y), brand_text, fill="#E2E8F0", font=font_brand)

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()
    
