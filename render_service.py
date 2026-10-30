import os
import io
import base64
import tempfile
import textwrap
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.parse

from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

# Google Gen AI SDK for Imagen 3
from google import genai
from google.genai import types

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

    return {
        "status": "READY" if len(missing_files) == 0 else "CONFIG_ISSUES_FOUND",
        "working_directory": project_root,
        "engine": "Pollinations FLUX.1 (Direct)",
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

def _generate_imagen_art(prompt_query: str) -> Image.Image:
    """
    Generates visual artwork with an automatic fallback to ensure
    the service never fails with 402 or 500 errors.
    """
    refined_prompt = (
        f"{prompt_query}, "
        "flat vector illustration, modern clean advertising art style, "
        "solid turquoise background, centered subject, sharp crisp details, "
        "completely isolated, strictly no text, no words, no letters, no logos"
    )
    encoded_prompt = urllib.parse.quote(refined_prompt)
    
    # 1. Attempt unmetered turbo model
    pollinations_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width=768&height=768&model=turbo&nologo=true&seed=42"
    )
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        req = urllib.request.Request(pollinations_url, headers=headers)
        with urllib.request.urlopen(req, timeout=25) as response:
            raw_bytes = response.read()
    except Exception as exc:
        print(f"Pollinations generation failed ({exc}). Using curated high-res fallback graphic.")
        # 2. Reliable royalty-free laundry hero image fallback
        fallback_url = "https://images.unsplash.com/photo-1545173168-9f1947eebb7f?w=800&q=80"
        req = urllib.request.Request(fallback_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as fb_response:
            raw_bytes = fb_response.read()

    return Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
    

def _render_dynamic_post(payload: PostPayload) -> bytes:
    project_root = os.path.dirname(os.path.abspath(__file__))
    canvas_w, canvas_h = 1080, 1350

    # 1. Solid Navy Base Canvas (Full Opacity - No Checkerboard)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (11, 27, 53, 255))

    # 2. Bubble Overlay with proper alpha blending
    bubble_path = os.path.join(project_root, "assets", "stickers_overlays", "bubble_pattern.png")
    if os.path.exists(bubble_path):
        try:
            with Image.open(bubble_path) as overlay:
                overlay_resized = overlay.convert("RGBA").resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
                canvas = Image.alpha_composite(canvas, overlay_resized)
        except Exception as e:
            print(f"Warning: bubble overlay failed to load: {e}")

    draw = ImageDraw.Draw(canvas)

    # 3. Logo (Masked paste prevents black boxes)
    logo_path = os.path.join(project_root, "assets", "logo", "logo_vasant_white.png")
    if os.path.exists(logo_path):
        try:
            with Image.open(logo_path) as logo:
                logo_rgba = logo.convert("RGBA")
                logo_rgba.thumbnail((380, 110), Image.Resampling.LANCZOS)
                logo_x = (canvas_w - logo_rgba.width) // 2
                canvas.paste(logo_rgba, (logo_x, 70), mask=logo_rgba)
        except Exception as e:
            print(f"Warning: logo failed to load: {e}")

    # 4. Large Headline (Explicit fallback chain)
    headline_font = None
    for font_candidate in [
        os.path.join(project_root, "assets", "fonts", "Poppins-Bold.ttf"),
        os.path.join(project_root, "assets", "fonts", "Poppins-Medium.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]:
        if os.path.exists(font_candidate):
            try:
                headline_font = ImageFont.truetype(font_candidate, size=56)
                break
            except Exception:
                continue

    if not headline_font:
        headline_font = ImageFont.load_default()

    wrapped_headline = textwrap.wrap(payload.headline.strip().upper(), width=22)
    y_pos = 210
    for line in wrapped_headline[:3]:
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        line_w = bbox[2] - bbox[0]
        draw.text(((canvas_w - line_w) // 2, y_pos), line, fill=(255, 255, 255), font=headline_font)
        y_pos += 68

    # 5. Center Image (Rounded corners & proper sizing)
    art = _generate_imagen_art(payload.primary_visual_query)
    art_w, art_h = 720, 520
    art_resized = art.convert("RGBA").resize((art_w, art_h), Image.Resampling.LANCZOS)
    
    # Paste centered
    art_x = (canvas_w - art_w) // 2
    art_y = 440
    canvas.paste(art_resized, (art_x, art_y), mask=art_resized)

    # 6. Bottom Contact Footer Bar
    footer_h = 140
    footer_y = canvas_h - footer_h
    draw.rectangle([(0, footer_y), (canvas_w, canvas_h)], fill=(10, 25, 47, 255))

    contact_font = None
    for font_candidate in [
        os.path.join(project_root, "assets", "fonts", "Inter-Regular.ttf"),
        os.path.join(project_root, "assets", "fonts", "Poppins-Medium.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]:
        if os.path.exists(font_candidate):
            try:
                contact_font = ImageFont.truetype(font_candidate, size=32)
                break
            except Exception:
                continue

    if not contact_font:
        contact_font = ImageFont.load_default()

    contact_text = f"📞 {payload.phone_number}   📍 {payload.location}"
    bbox = draw.textbbox((0, 0), contact_text, font=contact_font)
    contact_w = bbox[2] - bbox[0]
    draw.text(((canvas_w - contact_w) // 2, canvas_h - 85), contact_text, fill=(207, 218, 255), font=contact_font)

    # 7. Convert to standard RGB JPEG/PNG (Removes any alpha checkerboards)
    final_canvas = Image.new("RGB", (canvas_w, canvas_h), (11, 27, 53))
    final_canvas.paste(canvas, (0, 0), mask=canvas.split()[3])

    buf = io.BytesIO()
    final_canvas.save(buf, format="PNG", optimize=True)
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


class ReelRequest(BaseModel):
    title: str = "Chess Tactics"
    moves: List[str]
    fontSize: Optional[int] = 30
    readStyle: Optional[str] = "short"


@app.post("/render")
def render_reel(req: ReelRequest):
    if not req.moves:
        raise HTTPException(status_code=400, detail="Move list cannot be empty.")

    board = chess.Board()
    temp_dir = tempfile.mkdtemp()
    frame_paths = []

    try:
        svg_start = chess.svg.board(board=board, size=720)
        start_frame_path = os.path.join(temp_dir, "frame_000.png")
        cairosvg.svg2png(bytestring=svg_start.encode("utf-8"), write_to=start_frame_path)
        frame_paths.append(start_frame_path)

        for idx, uci_move in enumerate(req.moves):
            try:
                move = chess.Move.from_uci(uci_move)
                if move not in board.legal_moves:
                    continue

                arrows = [chess.svg.Arrow(move.from_square, move.to_square, color="#ffaa00cc")]
                board.push(move)

                svg_board = chess.svg.board(board=board, size=720, arrows=arrows)
                frame_path = os.path.join(temp_dir, f"frame_{idx + 1:03d}.png")
                cairosvg.svg2png(bytestring=svg_board.encode("utf-8"), write_to=frame_path)
                frame_paths.append(frame_path)
            except Exception:
                continue

        if not frame_paths:
            raise HTTPException(status_code=500, detail="Failed to render move frames.")

        frame_paths.extend([frame_paths[-1]] * 3)

        output_video_path = os.path.join(temp_dir, "chess_reel.mp4")
        clip = ImageSequenceClip(frame_paths, fps=1.2)

        if os.path.exists("move.wav"):
            try:
                audio = AudioFileClip("move.wav")
                clip = clip.set_audio(audio)
            except Exception:
                pass

        clip.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="ultrafast",
            threads=2,
            logger=None,
        )

        return FileResponse(output_video_path, media_type="video/mp4", filename=f"{req.title}.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render-flyer")
def render_business_flyer(req: BusinessFlyerRequest):
    try:
        png_bytes = render_business_flyer_image(req)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flyer rendering error: {str(e)}")


@app.get("/render-flyer")
def render_business_flyer_get(
    business_name: str = Query("Vasant Power Laundry"),
    headline: str = Query("Premium Laundry & Steam Pressing"),
    cta_text: str = Query("Drop Off Today"),
):
    req = BusinessFlyerRequest(
        business_name=business_name, 
        headline=headline, 
        cta_text=cta_text
    )
    png_bytes = render_business_flyer_image(req)
    return Response(content=png_bytes, media_type="image/png")
