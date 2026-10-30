import os
import io
import base64
import tempfile
import textwrap
from typing import Any, Dict, List, Optional

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


@app.get("/")
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


def _load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size=size)
    return ImageFont.load_default()


def _render_dynamic_post(payload: PostPayload) -> bytes:
    project_root = os.path.dirname(os.path.abspath(__file__))
    canvas_w, canvas_h = 1080, 1350
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (7, 22, 44, 255))
    draw = ImageDraw.Draw(canvas)

    background = Image.new("RGBA", (canvas_w, canvas_h), (11, 27, 53, 255))
    canvas = Image.alpha_composite(background, canvas)

    bubble_path = os.path.join(project_root, "assets", "stickers_overlays", "bubble_pattern.png")
    if os.path.exists(bubble_path):
        overlay = Image.open(bubble_path).convert("RGBA").resize((canvas_w, canvas_h))
        canvas = Image.alpha_composite(canvas, overlay)

    logo_path = os.path.join(project_root, "assets", "logo", "logo_vasant_white.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((380, 110), Image.Resampling.LANCZOS)
        logo_x = (canvas_w - logo.width) // 2
        canvas.paste(logo, (logo_x, 70), logo)

    headline_font = _load_font(os.path.join(project_root, "assets", "fonts", "Poppins-Bold.ttf"), 62)
    wrapped_headline = textwrap.wrap(payload.headline.strip(), width=18)
    y_pos = 220
    for line in wrapped_headline[:3]:
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        line_w = bbox[2] - bbox[0]
        draw.text(((canvas_w - line_w) // 2, y_pos), line, fill=(255, 255, 255), font=headline_font)
        y_pos += 78

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=openai_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=payload.primary_visual_query,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_data = response.data[0]
    if getattr(image_data, "url", None):
        import urllib.request

        with urllib.request.urlopen(image_data.url) as remote_image:
            art_bytes = remote_image.read()
    elif getattr(image_data, "b64_json", None):
        art_bytes = base64.b64decode(image_data.b64_json)
    else:
        raise ValueError("DALL-E 3 did not return an image payload")

    art = Image.open(io.BytesIO(art_bytes)).convert("RGBA")
    target_w, target_h = 560, 560
    art.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
    art_x = (canvas_w - art.width) // 2
    art_y = 430
    canvas.paste(art, (art_x, art_y), art)

    footer_h = 140
    footer_y = canvas_h - footer_h
    draw.rectangle([(0, footer_y), (canvas_w, canvas_h)], fill=(10, 25, 47, 255))

    contact_text = f"📞 {payload.phone_number}   📍 {payload.location}"
    contact_font = _load_font(os.path.join(project_root, "assets", "fonts", "Inter-Regular.ttf"), 26)
    contact_bbox = draw.textbbox((0, 0), contact_text, font=contact_font)
    contact_w = contact_bbox[2] - contact_bbox[0]
    draw.text(((canvas_w - contact_w) // 2, canvas_h - 60), contact_text, fill=(207, 218, 255), font=contact_font)

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


@app.post("/render-post")
def render_post(payload: PostPayload) -> Response:
    try:
        png_bytes = _render_dynamic_post(payload)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as exc:
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
    req = BusinessFlyerRequest(business_name=business_name, headline=headline, cta_text=cta_text)
    png_bytes = render_business_flyer_image(req)
    return Response(content=png_bytes, media_type="image/png")


@app.post("/render-laundry-flyer")
def render_laundry_flyer(req: LaundryFlyerRequest):
    try:
        png_bytes = generate_laundry_flyer(req)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Laundry flyer rendering error: {str(e)}")


@app.get("/render-laundry-flyer")
def render_laundry_flyer_get(
    tip_number: int = Query(1),
    category: str = Query("Laundry Care"),
    headline: str = Query("Smarter washing, fresher clothes"),
    body_text: str = Query(
        "Separate colors from whites, treat stains before washing, and keep loads balanced for cleaner results and longer-lasting fabrics."
    ),
    pro_takeaway: str = Query(
        "Pro tip: Pre-sort by fabric and color before loading to cut wear, save time, and get a better finish."
    ),
    brand_name: str = Query("Vasant Power Laundry"),
    brand_tagline: str = Query("Crisp • Clean • Express Care"),
):
    req = LaundryFlyerRequest(
        tip_number=tip_number,
        category=category,
        headline=headline,
        body_text=body_text,
        pro_takeaway=pro_takeaway,
        brand_name=brand_name,
        brand_tagline=brand_tagline,
    )
    png_bytes = generate_laundry_flyer(req)
    return Response(content=png_bytes, media_type="image/png")


@app.post("/render-quote-flyer")
def render_quote_flyer(req: ChessQuoteFlyerRequest):
    try:
        png_bytes = render_chess_quote_image(req)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote flyer rendering error: {str(e)}")


@app.post("/render-scrabble-post")
def render_scrabble_post_route(req: ScrabblePostRequest):
    try:
        return render_scrabble_post(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scrabble post rendering error: {str(e)}")


@app.get("/render-scrabble-post")
def render_scrabble_post_get(
    rack_letters: str = Query("Q, U, I, Z, Z, E, D"),
    hook_title: str = Query("Can you find a 35-point word?"),
    points: int = Query(35),
    hint: str = Query("Uses double Z and Q!"),
    branding: str = Query("Word Masters Club"),
):
    req = ScrabblePostRequest(
        rack_letters=rack_letters,
        hook_title=hook_title,
        points=points,
        hint=hint,
        branding=branding,
    )
    return render_scrabble_post(req)
