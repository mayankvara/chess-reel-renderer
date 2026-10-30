import os
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = "assets"

def get_font(font_name: str, size: int):
    path = os.path.join(ASSETS_DIR, "fonts", font_name)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def render_post_image(row_data: dict) -> bytes:
    # 1. Base Dimensions (4:5 Portrait for FB/Instagram)
    width, height = 1080, 1350

    # 2. Base Canvas Layer: Load Background from /assets/templates_bg/
    design_type = row_data.get("design_type", "")
    bg_name = "bg_navy.png" if design_type in ["STAIN_BREAKDOWN", "SPLIT_BEFORE_AFTER"] else "bg_cyan.png"
    bg_path = os.path.join(ASSETS_DIR, "templates_bg", bg_name)

    if os.path.exists(bg_path):
        canvas = Image.open(bg_path).convert("RGBA").resize((width, height))
    else:
        # Fallback to solid cyan if file missing
        canvas = Image.new("RGBA", (width, height), (0, 180, 216, 255))

    draw = ImageDraw.Draw(canvas)

    # 3. Layer: Corner decorative bubbles / overlay
    bubble_path = os.path.join(ASSETS_DIR, "stickers_overlays", "bubble_pattern.png")
    if os.path.exists(bubble_path):
        bubbles = Image.open(bubble_path).convert("RGBA").resize((width, height))
        canvas.paste(bubbles, (0, 0), bubbles)

    # 4. Layer: Brand Logo (/assets/logo/logo_vasant_white.png)
    logo_path = os.path.join(ASSETS_DIR, "logo", "logo_vasant_white.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((380, 110))
        logo_x = (width - logo.width) // 2
        canvas.paste(logo, (logo_x, 70), logo)
    else:
        # Text logo fallback if image not found
        font_logo = get_font("Poppins-Bold.ttf", 40)
        draw.text(((width - 320) // 2, 80), "VASANT POWER LAUNDRY", fill=(255, 255, 255), font=font_logo)

    # 5. Layer: Headline (Wrapped dynamically)
    font_head = get_font("Poppins-Bold.ttf", 62)
    headline = row_data.get("headline", "FRESH CLOTHES, ZERO STRESS!").upper()
    wrapped_head = textwrap.wrap(headline, width=22)
    
    y_pos = 220
    for line in wrapped_head:
        bbox = draw.textbbox((0, 0), line, font=font_head)
        line_w = bbox[2] - bbox[0]
        draw.text(((width - line_w) // 2, y_pos), line, fill=(255, 255, 255), font=font_head)
        y_pos += 75

    # 6. Layer: Center Visual / Clipart Icon
    # Map design type to corresponding icon/illustration
    icon_map = {
        "RETRO_GAME": "ic_basket.png",
        "STAIN_BREAKDOWN": "ic_steam_iron.png",
        "REMINDER_CARD": "ic_clock.png",
        "STEAM_PRESS_SPOTLIGHT": "ic_steam_iron.png"
    }
    icon_file = icon_map.get(design_type, "ic_basket.png")
    icon_path = os.path.join(ASSETS_DIR, "icons", icon_file)
    
    if os.path.exists(icon_path):
        center_icon = Image.open(icon_path).convert("RGBA")
        center_icon.thumbnail((420, 420))
        icon_x = (width - center_icon.width) // 2
        canvas.paste(center_icon, (icon_x, 480), center_icon)

    # 7. Layer: Subheadline / Supporting Note (White Card or Floating text)
    subhead = row_data.get("subheadline", "")
    if subhead:
        font_sub = get_font("Poppins-Medium.ttf", 34)
        wrapped_sub = textwrap.wrap(subhead, width=38)
        y_sub = 960
        for line in wrapped_sub:
            bbox = draw.textbbox((0, 0), line, font=font_sub)
            line_w = bbox[2] - bbox[0]
            draw.text(((width - line_w) // 2, y_sub), line, fill=(255, 255, 255), font=font_sub)
            y_sub += 48

    # 8. Layer: Bottom Footer Bar (Call To Action & Contact Info)
    footer_bar_h = 130
    draw.rectangle([(0, height - footer_bar_h), (width, height)], fill=(10, 25, 47, 255)) # Deep Navy

    font_cta = get_font("Poppins-Bold.ttf", 28)
    font_contact = get_font("Inter-Regular.ttf", 26)

    # Real contact data from row
    cta_text = row_data.get("cta_text", "BOOK YOUR PICKUP NOW")
    phone = row_data.get("phone_number", "+91 9909460668")
    loc = row_data.get("location", "Porbandar")

    # CTA Button line
    bbox_cta = draw.textbbox((0, 0), cta_text, font=font_cta)
    draw.text(((width - (bbox_cta[2] - bbox_cta[0])) // 2, height - 110), cta_text, fill=(255, 255, 255), font=font_cta)

    # Phone & Location line with icons
    contact_str = f"📞 {phone}    📍 {loc}"
    bbox_cnt = draw.textbbox((0, 0), contact_str, font=font_contact)
    draw.text(((width - (bbox_cnt[2] - bbox_cnt[0])) // 2, height - 55), contact_str, fill=(200, 225, 255), font=font_contact)

    # 9. Return image bytes for FastAPI / Make.com response
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", quality=95)
    return buf.getvalue()
  
