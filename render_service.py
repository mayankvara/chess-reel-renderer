import os
import io
import base64
import tempfile
import textwrap
from typing import Any, Dict, List, Optional
import urllib.request

from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.responses import FileResponse
from openai import OpenAI
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

import chess
import chess.svg
import cairosvg
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip

from flyer_service import (
    BusinessFlyerRequest,
    ChessQuoteFlyerRequest,
    render_business_flyer_image,
    render_chess_quote_image,
)
from laundry_flyer_service import (
    LaundryFlyerRequest,
    generate_laundry_flyer,
)
from scrabble_service import (
    ScrabblePostRequest,
    render_scrabble_post,
)

app = FastAPI(title="Chess Reel & Flyer Renderer API")


class PostPayload(BaseModel):
    title: str = "Vasant Laundry Poster"
    headline: str = "Fresh, reliable care for your home"
    body: str = "Clean, crisp, and ready when you are."
    cta: str = "Book a pickup today"
    brand_name: str = "Vasant Laundry"
    accent_color: str = "#1d4ed8"
    phone_number: str = "+91 9909460668"
    location: str = "Porbandar"
    primary_visual_query: str = (
        "Premium laundry service hero illustration with folded clean white towels, steam iron, basket,"
        " polished modern laundry care scene, high-end lifestyle photography style"
    )


# 1. ALLOW BOTH GET AND HEAD (Fixes Render 405 ping shutdown)
@app.api_route("/", methods=["GET", "HEAD"])
def root() -> Dict[str, str]:
    return {"status": "ok", "service": "Vasant Laundry Poster Engine"}


@app.get("/debug")
def run_system_diagnostics() -> Dict[str, Any]:
    project_root = os.path.dirname(os.path.abspath(__file__))
    openai_key = os.getenv("OPENAI_API_KEY")

    openai_status: Dict[str, Any] = {
        "key_present": bool(openai_key),
        "key_prefix": openai_key[:7] + "..." if openai_key else None,
        "api_live_check": "not_tested",
    }

    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            client.models.list()
            openai_status["api_live_check"] = "SUCCESS (Key valid & active)"
        except Exception as exc:
            openai_status["api_live_check"] = f"FAILED: {str(exc)}"

    expected_files = [
        "assets/logo/logo_vasant_white.png",
        "assets/logo/logo_vasant_dark.png",
        "assets/fonts/Poppins-Bold.ttf",
        "assets/fonts/Poppins-Medium.ttf",
        "assets/fonts/Inter-Regular.ttf",
        "assets/icons/ic_phone.png",
        "assets/icons/ic_pin.png",
        "assets/icons/ic_clock.png",
        "assets/icons/ic_basket.png",
        "assets/icons/ic_steam_iron.png",
        "assets/icons/ic_sparkles.png",
        "assets/templates_bg/bg_cyan.png",
        "assets/templates_bg/bg_navy.png",
        "assets/templates_bg/bg_soft_ivory.png",
        "assets/stickers_overlays/notification_card.png",
        "assets/stickers_overlays/selection_box.png",
        "assets/stickers_overlays/bubble_pattern.png",
    ]

    assets_check: Dict[str, str] = {}
    missing_files: List[str] = []

    for file_path in expected_files:
        full_path = os.path.join(project_root, file_path)
        exists = os.path.exists(full_path)
        assets_check[file_path] = "EXISTS" if exists else "MISSING"
        if not exists:
            missing_files.append(file_path)

    is_ready = (
        openai_status["key_present"]
        and "SUCCESS" in openai_status["api_live_check"]
        and len(missing_files) == 0
    )

    return {
        "status": "READY" if is_ready else "CONFIG_ISSUES_FOUND",
        "working_directory": project_root,
        "openai": openai_status,
        "missing_assets_count": len(missing_files),
        "missing_assets": missing_files,
        "all_assets": assets_check,
    }


def _load_font(font_path: str, size: int) -> ImageFont.ImageFont:
    """Safely loads TrueType fonts with fallback to Poppins or system default."""
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception:
            pass
    # Fallback to Poppins-Medium if Inter is missing/corrupt
    alt_font = os.path.join(os.path.dirname(font_path), "Poppins-Medium.ttf")
    if os.path.exists(alt_font):
        try:
            return ImageFont.truetype(alt_font, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _get_text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    """Safe width calculation supporting both TrueType and default fallback fonts."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    except Exception:
        return len(text) * 12


def _render_dynamic_post(payload: PostPayload) -> bytes:
    project_root = os.path.dirname(os.path.abspath(__file__))
    canvas_w, canvas_h = 1080, 1350

    # Direct RGB background to conserve RAM on 512MB limit
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (11, 27, 53, 255))
    draw = ImageDraw.Draw(canvas)

    # 1. Bubble Overlay
    bubble_path = os.path.join(project_root, "assets", "stickers_overlays", "bubble_pattern.png")
    if os.path.exists(bubble_path):
        try:
            with Image.open(bubble_path) as overlay:
                overlay_resized = overlay.convert("RGBA").resize((canvas_w, canvas_h))
                canvas = Image.alpha_composite(canvas, overlay_resized)
                draw = ImageDraw.Draw(canvas)
        except Exception as e:
            print(f"Warning: bubble overlay failed to load: {e}")

    # 2. Logo
    logo_path = os.path.join(project_root, "assets", "logo", "logo_vasant_white.png")
    if os.path.exists(logo_path):
        try:
            with Image.open(logo_path) as logo:
                logo_copy = logo.convert("RGBA")
                logo_copy.thumbnail((380, 110), Image.Resampling.LANCZOS)
                logo_x = (canvas_w - logo_copy.width) // 2
                canvas.paste(logo_copy, (logo_x, 70), logo_copy)
        except Exception as e:
            print(f"Warning: logo failed to load: {e}")

    # 3. Dynamic Headline
    headline_font = _load_font(os.path.join(project_root, "assets", "fonts", "Poppins-Bold.ttf"), 62)
    wrapped_headline = textwrap.wrap(payload.headline.strip(), width=22)
    y_pos = 220
    for line in wrapped_headline[:3]:
        line_w = _get_text_width(draw, line, headline_font)
        draw.text(((canvas_w - line_w) // 2, y_pos), line, fill=(255, 255, 255), font=headline_font)
        y_pos += 78

    # 4. Generate AI Artwork using DALL-E 2
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY environment variable is not configured.")

    client = OpenAI(api_key=openai_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=(
            f"{payload.primary_visual_query}. "
            "Clean commercial advertising illustration, "
            "no text, no letters, no logos, centered composition."
        ),
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_data = response.data[0]
    if getattr(image_data, "url", None):
        req = urllib.request.Request(image_data.url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=45) as remote_image:
            art_bytes = remote_image.read()
    elif getattr(image_data, "b64_json", None):
        art_bytes = base64.b64decode(image_data.b64_json)
    else:
        raise ValueError("DALL-E 2 returned no valid URL or base64 data.")

    # 5. Composite Art
    with Image.open(io.BytesIO(art_bytes)) as art:
        art_rgba = art.convert("RGBA")
        art_rgba.thumbnail((560, 560), Image.Resampling.LANCZOS)
        art_x = (canvas_w - art_rgba.width) // 2
        art_y = 440
        canvas.paste(art_rgba, (art_x, art_y), art_rgba)

    # 6. Bottom Contact Footer
    footer_h = 140
    footer_y = canvas_h - footer_h
    draw.rectangle([(0, footer_y), (canvas_w, canvas_h)], fill=(10, 25, 47, 255))

    contact_text = f"📞 {payload.phone_number}   📍 {payload.location}"
    contact_font = _load_font(os.path.join(project_root, "assets", "fonts", "Inter-Regular.ttf"), 28)
    contact_w = _get_text_width(draw, contact_text, contact_font)
    draw.text(((canvas_w - contact_w) // 2, canvas_h - 85), contact_text, fill=(207, 218, 255), font=contact_font)

    # 7. Convert to RGB PNG buffer
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()


@app.post("/render-post")
def render_post(payload: PostPayload) -> Response:
    try:
        png_bytes = _render_dynamic_post(payload)
        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={"Content-Disposition": 'inline; filename="poster.png"'},
        )
    except Exception as exc:
        print(f"Render Error Trace: {repr(exc)}")
        raise HTTPException(status_code=500, detail=f"Poster rendering error: {str(exc)}")
        
