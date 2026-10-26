import io
import os
import textwrap
import uuid
from PIL import Image, ImageDraw, ImageFont
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class FlyerRequest(BaseModel):
    title: str
    headline: str
    subtext: str

def get_font(size, bold=False):
    """Load system font with clean scaling."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def draw_pill(draw, box, fill_color, radius=18):
    draw.rounded_rectangle(box, radius=radius, fill=fill_color)

@app.post("/render-flyer")
def render_flyer(req: FlyerRequest):
    try:
        # High-res Instagram/Facebook Portrait Canvas (1080 x 1350)
        width, height = 1080, 1350
        canvas = Image.new("RGBA", (width, height), (10, 17, 40, 255)) # Deep Royal Navy
        draw = ImageDraw.Draw(canvas)

        # 1. Subtle Outer Border & Gold Accent Accents
        draw.rounded_rectangle([(40, 40), (width - 40, height - 40)], radius=36, outline=(218, 165, 32, 200), width=4)
        draw.rounded_rectangle([(52, 52), (width - 52, height - 52)], radius=28, outline=(255, 255, 255, 40), width=2)

        # 2. Header Branding Pill
        draw_pill(draw, [(140, 100), (width - 140, 180)], fill_color=(19, 31, 66, 255), radius=22)
        brand_font = get_font(38, bold=True)
        draw.text((width // 2, 140), "✨ VASANT POWER LAUNDRY", fill=(245, 197, 24), anchor="mm", font=brand_font)

        # 3. Category / Topic Tag
        category_font = get_font(28, bold=True)
        topic_tag = f"• {req.title.upper()} •"
        draw.text((width // 2, 240), topic_tag, fill=(180, 200, 240), anchor="mm", font=category_font)

        # 4. Central Graphic Card Container (Warm Contrast Container)
        card_box = [(90, 300), (width - 90, 1020)]
        draw.rounded_rectangle(card_box, radius=30, fill=(18, 26, 54, 255), outline=(218, 165, 32, 120), width=2)

        # Central Accent Icon / Motif
        icon_font = get_font(72, bold=True)
        draw.text((width // 2, 410), "🛡️ 👔 ✨", fill=(255, 255, 255), anchor="mm", font=icon_font)

        # 5. Bold Dynamic Headline (Auto text-wrapping)
        headline_font = get_font(52, bold=True)
        wrapped_headline = textwrap.fill(req.headline, width=24)
        draw.text((width // 2, 580), wrapped_headline, fill=(255, 255, 255), anchor="mm", font=headline_font, align="center")

        # 6. Supporting Subtext / Customer Assurance
        subtext_font = get_font(34, bold=False)
        wrapped_subtext = textwrap.fill(req.subtext, width=36)
        draw.text((width // 2, 850), wrapped_subtext, fill=(210, 222, 245), anchor="mm", font=subtext_font, align="center")

        # 7. Footer: Trust Badges & Porbandar Address
        footer_pill_box = [(120, 1070), (width - 120, 1250)]
        draw.rounded_rectangle(footer_pill_box, radius=24, fill=(14, 21, 46, 255), outline=(218, 165, 32, 180), width=2)

        footer_title = get_font(32, bold=True)
        draw.text((width // 2, 1120), "100% Pocket Custody Guarantee • Smart WhatsApp Slips", fill=(245, 197, 24), anchor="mm", font=footer_title)

        address_font = get_font(26, bold=False)
        address_text = "📍 Wagheshwari Plot, Porbandar (360575) | 7 Days Open"
        draw.text((width // 2, 1190), address_text, fill=(220, 230, 245), anchor="mm", font=address_font)

        # Save to temporary buffer
        output_path = f"/tmp/{uuid.uuid4().hex[:8]}.png"
        canvas.convert("RGB").save(output_path, "PNG", quality=95)

        return FileResponse(output_path, media_type="image/png", filename="vasant_flyer.png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
