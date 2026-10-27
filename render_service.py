import uuid
import textwrap
from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException
from fastapi.responses import FileResponse


def get_font(size: int, bold: bool = False, serif: bool = False):
    """Loads system font with fallback to default PIL font."""
    font_names = []
    if serif:
        font_names = [
            "DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf",
            "Times New Roman Bold.ttf" if bold else "Times New Roman.ttf",
            "Georgia Bold.ttf" if bold else "Georgia.ttf",
        ]
    else:
        font_names = [
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "Arial Bold.ttf" if bold else "Arial.ttf",
            "NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf",
        ]

    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_corner_fan(draw: ImageDraw.Draw, center: tuple, radius: int, quadrant: str):
    """Draws luxury gold corner fan / concentric accent arcs."""
    cx, cy = center
    gold_outer = (220, 175, 75, 230)
    gold_inner = (245, 210, 120, 160)
    
    # Angles for quadrants: 'TL', 'TR', 'BL', 'BR'
    angles = {
        'TL': (0, 90),
        'TR': (90, 180),
        'BL': (270, 360),
        'BR': (180, 270)
    }
    start_a, end_a = angles.get(quadrant, (0, 90))
    bbox_large = [(cx - radius, cy - radius), (cx + radius, cy + radius)]
    bbox_small = [(cx - radius * 0.6, cy - radius * 0.6), (cx + radius * 0.6, cy + radius * 0.6)]
    
    draw.arc(bbox_large, start=start_a, end=end_a, fill=gold_outer, width=5)
    draw.arc(bbox_small, start=start_a, end=end_a, fill=gold_inner, width=3)


def draw_notched_card(draw: ImageDraw.Draw, box: list, radius: int, fill: tuple, outline: tuple, width: int = 2):
    """Draws luxury container card with inner border."""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    # Hairline inner border
    inner_box = [(box[0][0] + 6, box[0][1] + 6), (box[1][0] - 6, box[1][1] - 6)]
    inner_gold = (outline[0], outline[1], outline[2], 90 if len(outline) > 3 else outline[0])
    draw.rounded_rectangle(inner_box, radius=max(4, radius - 4), outline=inner_gold, width=1)


def render_flyer(req: FlyerRequest):
    try:
        width, height = 1080, 1440  # Standard 3:4 high-res poster ratio (or 1080x1350 for 4:5)
        canvas = Image.new("RGBA", (width, height), (11, 23, 48, 255))  # Deep Midnight Navy
        draw = ImageDraw.Draw(canvas)

        # ----------------------------------------------------
        # 1. Outer Double Borders & Gold Corner Accents
        # ----------------------------------------------------
        draw.rectangle([(32, 32), (width - 32, height - 32)], outline=(200, 155, 65, 220), width=3)
        draw.rectangle([(44, 44), (width - 44, height - 44)], outline=(140, 105, 45, 120), width=1)

        # Corner Fans (Top-Left, Top-Right, Bottom-Left, Bottom-Right)
        fan_r = 52
        draw_corner_fan(draw, (44, 44), fan_r, 'TL')
        draw_corner_fan(draw, (width - 44, 44), fan_r, 'TR')
        draw_corner_fan(draw, (44, height - 44), fan_r, 'BL')
        draw_corner_fan(draw, (width - 44, height - 44), fan_r, 'BR')

        # ----------------------------------------------------
        # 2. Header Branding Emblem Plaque
        # ----------------------------------------------------
        plaque_w, plaque_h = 420, 110
        plaque_x1 = (width - plaque_w) // 2
        plaque_y1 = 80
        plaque_box = [(plaque_x1, plaque_y1), (plaque_x1 + plaque_w, plaque_y1 + plaque_h)]
        
        draw_notched_card(draw, plaque_box, radius=18, fill=(35, 43, 50, 255), outline=(218, 172, 78, 240), width=2)

        vasant_font = get_font(42, bold=True, serif=True)
        draw.text((width // 2, plaque_y1 + 42), "VASANT", fill=(245, 204, 110), anchor="mm", font=vasant_font)

        sub_brand_font = get_font(20, bold=True, serif=True)
        draw.text((width // 2, plaque_y1 + 80), "POWER LAUNDRY", fill=(215, 175, 85), anchor="mm", font=sub_brand_font)

        # ----------------------------------------------------
        # 3. Category Pill (Solid Metallic Gold Fill)
        # ----------------------------------------------------
        pill_w, pill_h = 580, 60
        pill_x1 = (width - pill_w) // 2
        pill_y1 = 225
        pill_box = [(pill_x1, pill_y1), (pill_x1 + pill_w, pill_y1 + pill_h)]

        draw.rounded_rectangle(pill_box, radius=30, fill=(235, 185, 75, 255), outline=(255, 220, 130, 200), width=2)
        
        pill_tag = f"• {req.title.upper()} •"
        category_font = get_font(25, bold=True, serif=False)
        draw.text((width // 2, pill_y1 + pill_h // 2), pill_tag, fill=(11, 23, 48), anchor="mm", font=category_font)

        # ----------------------------------------------------
        # 4. Central Graphic Card Container (Dark Slate)
        # ----------------------------------------------------
        card_box = [(120, 320), (width - 120, 940)]
        draw_notched_card(draw, card_box, radius=24, fill=(36, 44, 52, 255), outline=(218, 172, 78, 230), width=3)

        # Headline (Elegant Serif, White, Large)
        headline_font = get_font(52, bold=True, serif=True)
        wrapped_headline = textwrap.fill(req.headline, width=22)
        draw.text((width // 2, 500), wrapped_headline, fill=(255, 255, 255), anchor="mm", font=headline_font, align="center")

        # Subtext / Offer Details (Clean Sans, Off-White)
        subtext_font = get_font(28, bold=False, serif=False)
        wrapped_subtext = textwrap.fill(req.subtext, width=34)
        draw.text((width // 2, 750), wrapped_subtext, fill=(220, 230, 245), anchor="mm", font=subtext_font, align="center")

        # ----------------------------------------------------
        # 5. Dual Trust Badges (Side-by-Side Cards)
        # ----------------------------------------------------
        badge_y1 = 980
        badge_h = 160
        gap = 36
        badge_w = (width - 240 - gap) // 2  # 382px each
        
        # Left Badge: 100% Pocket Custody Guarantee
        b1_x1 = 120
        b1_box = [(b1_x1, badge_y1), (b1_x1 + badge_w, badge_y1 + badge_h)]
        draw_notched_card(draw, b1_box, radius=18, fill=(33, 40, 48, 255), outline=(218, 172, 78, 220), width=2)

        badge_font = get_font(24, bold=True, serif=True)
        b1_text = "100% Pocket\nCustody\nGuarantee"
        draw.text((b1_x1 + badge_w // 2, badge_y1 + badge_h // 2), b1_text, fill=(245, 204, 110), anchor="mm", font=badge_font, align="center")

        # Right Badge: Smart WhatsApp Slips
        b2_x1 = b1_x1 + badge_w + gap
        b2_box = [(b2_x1, badge_y1), (b2_x1 + badge_w, badge_y1 + badge_h)]
        draw_notched_card(draw, b2_box, radius=18, fill=(33, 40, 48, 255), outline=(218, 172, 78, 220), width=2)

        b2_text = "Smart\nWhatsApp\nSlips"
        draw.text((b2_x1 + badge_w // 2, badge_y1 + badge_h // 2), b2_text, fill=(245, 204, 110), anchor="mm", font=badge_font, align="center")

        # ----------------------------------------------------
        # 6. Bottom Full-Width Location Strip
        # ----------------------------------------------------
        strip_y = height - 100
        draw.line([(32, strip_y), (width - 32, strip_y)], fill=(190, 145, 60, 180), width=2)

        address_font = get_font(22, bold=False, serif=False)
        address_text = "Wagheshwari Plot, Porbandar (360575)  |  7 Days Open"
        draw.text((width // 2, height - 52), address_text, fill=(240, 245, 255), anchor="mm", font=address_font)

        # ----------------------------------------------------
        # 7. Export PNG
        # ----------------------------------------------------
        output_path = f"/tmp/{uuid.uuid4().hex[:8]}.png"
        canvas.convert("RGB").save(output_path, "PNG", quality=95)
        return FileResponse(output_path, media_type="image/png", filename="vasant_flyer.png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
