import io
import textwrap
from typing import Tuple

from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont


class LaundryFlyerRequest(BaseModel):
    tip_number: int = 1
    category: str = "Laundry Care"
    headline: str = "Smarter washing, fresher clothes"
    body_text: str = (
        "Separate colors from whites, treat stains before washing, and keep loads balanced "
        "for cleaner results and longer-lasting fabrics."
    )
    pro_takeaway: str = (
        "Pro tip: Pre-sort by fabric and color before loading to cut wear, save time, "
        "and get a better finish."
    )
    brand_name: str = "Vasant Power Laundry"
    brand_tagline: str = "Crisp • Clean • Express Care"
    canvas_size: Tuple[int, int] = (1080, 1080)


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
    ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue

    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, font: ImageFont.ImageFont):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if width <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    if not lines:
        lines = [text]

    return lines


def generate_laundry_flyer(req: LaundryFlyerRequest) -> bytes:
    width, height = req.canvas_size
    img = Image.new("RGB", (width, height), color="#F4EFE7")
    draw = ImageDraw.Draw(img)

    navy = (22, 45, 74)
    gold = (245, 178, 44)
    soft_blue = (141, 196, 255)
    slate = (68, 77, 96)
    cream = (245, 235, 215)

    draw.rounded_rectangle([(0, 0), (width, height)], radius=36, fill="#F4EFE7")
    draw.rounded_rectangle([(40, 40), (1040, 1040)], radius=34, fill="#FFFDF9", outline="#D9C7B3", width=3)

    # Top banner
    draw.rounded_rectangle([(70, 70), (1010, 260)], radius=26, fill=navy)

    tip_font = get_font(34, bold=True)
    category_font = get_font(24, bold=True)
    draw.rounded_rectangle([(95, 95), (300, 170)], radius=15, fill=gold)
    draw.text((125, 110), f"TIP #{req.tip_number}", fill=navy, font=tip_font)

    category_text = req.category.upper()
    cat_w = draw.textbbox((0, 0), category_text, font=category_font)[2]
    cat_x = width - cat_w - 120
    draw.rounded_rectangle([(cat_x - 16, 105), (cat_x + cat_w + 16, 160)], radius=15, fill=soft_blue)
    draw.text((cat_x, 110), category_text, fill=navy, font=category_font)

    draw.text((90, 205), "Vasant Power Laundry", fill="#DDEBFF", font=get_font(22, bold=True))

    # Headline
    title_font = get_font(64, bold=True)
    title_lines = _wrap_text(draw, req.headline, 760, title_font)
    title_y = 310
    for line in title_lines:
        draw.text((90, title_y), line, fill=navy, font=title_font)
        title_y += 72

    # Body text card
    body_card_y = title_y + 30
    draw.rounded_rectangle([(90, body_card_y), (990, body_card_y + 260)], radius=28, fill=cream, outline="#E3C29D", width=2)

    body_font = get_font(30, bold=False)
    body_lines = _wrap_text(draw, req.body_text, 760, body_font)
    body_y = body_card_y + 40
    for line in body_lines:
        draw.text((130, body_y), line, fill=slate, font=body_font)
        body_y += 46

    # Pro takeaway
    takeaway_y = body_card_y + 320
    draw.rounded_rectangle([(90, takeaway_y), (990, takeaway_y + 225)], radius=28, fill=gold)

    draw.text((125, takeaway_y + 28), "PRO TAKEAWAY", fill=navy, font=get_font(22, bold=True))

    takeaway_font = get_font(30, bold=True)
    takeaway_lines = _wrap_text(draw, req.pro_takeaway, 760, takeaway_font)
    takeaway_inner_y = takeaway_y + 82
    for line in takeaway_lines:
        draw.text((125, takeaway_inner_y), line, fill=navy, font=takeaway_font)
        takeaway_inner_y += 40

    # Footer branding
    footer_y = 940
    draw.rounded_rectangle([(90, footer_y), (990, 1015)], radius=18, fill=navy)

    draw.text((110, 962), req.brand_name.upper(), fill="#FFFFFF", font=get_font(30, bold=True))
    draw.text((width - draw.textbbox((0, 0), req.brand_tagline.upper(), font=get_font(20, bold=True))[2] - 120, 972),
              req.brand_tagline.upper(), fill=soft_blue, font=get_font(20, bold=True))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
