import io
import textwrap
from fastapi import FastAPI, HTTPException, Query, Response
from PIL import Image, ImageDraw
from pydantic import BaseModel

app = FastAPI()


class FlyerRequest(BaseModel):
    business_name: str = "Vasant Power Laundry"
    tagline: str = "Crisp • Clean • Express Care"
    headline: str = "Premium Laundry & Steam Pressing"
    subheadline: str = "Fast turnaround, hygienic washing, and door-to-door convenience."
    services: list[str] = [
        "Wash & Fold",
        "Steam Ironing / Pressing",
        "Dry Cleaning Care",
        "Curtain & Blanket Deep Clean",
    ]
    offer_badge: str = "Starting at ₹99 / Month / Plans Available"
    phone_or_whatsapp: str = "+91 XXXXXXXXXX"
    address_line: str = "Porbandar, Gujarat"
    cta_text: str = "Drop Off Today / WhatsApp for Pickup"
    canvas_size: tuple[int, int] = (1080, 1080)


def get_font(size: int, bold: bool = False):
    candidates = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
        "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        try:
            return __import__("PIL").ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return __import__("PIL").ImageFont.load_default()


def wrap_lines(draw: ImageDraw.Draw, text: str, font, max_width: int, max_lines: int = 3):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines - 1:
                break

    if current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        if len(last) > 18:
            lines[-1] = last[:15] + "..."

    return "\n".join(lines)


def draw_service_chip(draw: ImageDraw.Draw, x: int, y: int, w: int, h: int, label: str):
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=16, fill=(240, 250, 252), outline=(0, 168, 150), width=2)
    draw.text((x + 20, y + h / 2), "✓", fill=(0, 168, 150), anchor="lm", font=get_font(26, bold=True))
    label_font = get_font(22, bold=True)
    wrapped = wrap_lines(draw, label, label_font, w - 70, max_lines=2)
    draw.multiline_text((x + 52, y + 16), wrapped, fill=(15, 41, 66), font=label_font, spacing=2)


def generate_flyer_image(req: FlyerRequest) -> Image.Image:
    width, height = req.canvas_size
    canvas = Image.new("RGB", (width, height), "#F4F8FB")
    draw = ImageDraw.Draw(canvas)

    outer_pad = 42
    draw.rounded_rectangle([(outer_pad, outer_pad), (width - outer_pad, height - outer_pad)], radius=34, fill=(255, 255, 255), outline=(199, 218, 232), width=2)

    draw.rounded_rectangle([(70, 70), (width - 70, 200)], radius=24, fill=(15, 41, 66), outline=(15, 41, 66), width=2)
    draw.text((width / 2, 107), req.business_name.upper(), fill=(255, 255, 255), anchor="mm", font=get_font(38, bold=True))
    draw.text((width / 2, 150), req.tagline, fill=(123, 181, 214), anchor="mm", font=get_font(18, bold=True))

    draw.rounded_rectangle([(130, 225), (width - 130, 290)], radius=22, fill=(245, 158, 11), outline=(255, 216, 121), width=2)
    draw.text((width / 2, 257), req.offer_badge, fill=(255, 255, 255), anchor="mm", font=get_font(24, bold=True))

    draw.rounded_rectangle([(80, 330), (width - 80, 710)], radius=28, fill=(245, 248, 251), outline=(200, 216, 231), width=2)
    draw.ellipse([(760, 350), (980, 570)], fill=(2, 132, 199), outline=(0, 117, 180), width=2)
    draw.text((870, 460), "24H", fill=(255, 255, 255), anchor="mm", font=get_font(54, bold=True))

    headline_font = get_font(42, bold=True)
    headline_text = wrap_lines(draw, req.headline, headline_font, 540, max_lines=3)
    draw.multiline_text((100, 380), headline_text, fill=(15, 41, 66), font=headline_font, spacing=6)

    subheadline_font = get_font(23, bold=False)
    subheadline_text = wrap_lines(draw, req.subheadline, subheadline_font, 560, max_lines=4)
    draw.multiline_text((100, 515), subheadline_text, fill=(37, 66, 90), font=subheadline_font, spacing=4)

    draw.rounded_rectangle([(100, 640), (980, 820)], radius=26, fill=(255, 255, 255), outline=(214, 231, 239), width=2)
    for idx, service in enumerate(req.services[:4]):
        col = idx % 2
        row = idx // 2
        x = 130 + (col * 400)
        y = 670 + (row * 90)
        draw_service_chip(draw, x, y, 330, 64, service)

    draw.rounded_rectangle([(60, 845), (width - 60, 1010)], radius=30, fill=(15, 41, 66), outline=(15, 41, 66), width=2)
    draw.rounded_rectangle([(120, 882), (width - 120, 945)], radius=20, fill=(0, 168, 150), outline=(0, 168, 150), width=2)
    draw.text((width / 2, 913), req.cta_text.upper(), fill=(255, 255, 255), anchor="mm", font=get_font(24, bold=True))
    draw.text((width / 2, 968), req.phone_or_whatsapp, fill=(255, 255, 255), anchor="mm", font=get_font(20, bold=True))
    draw.text((width / 2, 994), req.address_line, fill=(206, 225, 239), anchor="mm", font=get_font(18, bold=False))

    return canvas


@app.post("/render-flyer")
def render_flyer(req: FlyerRequest):
    try:
        image = generate_flyer_image(req)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        return Response(content=buffer.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/render-flyer")
def render_flyer_get(
    business_name: str = Query(default="Vasant Power Laundry"),
    tagline: str = Query(default="Crisp • Clean • Express Care"),
    headline: str = Query(default="Premium Laundry & Steam Pressing"),
    subheadline: str = Query(default="Fast turnaround, hygienic washing, and door-to-door convenience."),
    services: str = Query(default="Wash & Fold,Steam Ironing / Pressing,Dry Cleaning Care,Curtain & Blanket Deep Clean"),
    offer_badge: str = Query(default="Starting at ₹99 / Month / Plans Available"),
    phone_or_whatsapp: str = Query(default="+91 XXXXXXXXXX"),
    address_line: str = Query(default="Porbandar, Gujarat"),
    cta_text: str = Query(default="Drop Off Today / WhatsApp for Pickup"),
):
    req = FlyerRequest(
        business_name=business_name,
        tagline=tagline,
        headline=headline,
        subheadline=subheadline,
        services=[item.strip() for item in services.split(",") if item.strip()],
        offer_badge=offer_badge,
        phone_or_whatsapp=phone_or_whatsapp,
        address_line=address_line,
        cta_text=cta_text,
    )
    return render_flyer(req)
