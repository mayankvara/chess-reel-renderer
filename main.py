import os
from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# Import the laundry flyer module
from flyer_service import (
    BusinessFlyerRequest,
    ChessQuoteFlyerRequest,
    LaundryFlyerRequest,
    render_business_flyer_image,
    render_chess_quote_image,
    render_laundry_flyer_image,
)

app = FastAPI(
    title="Vasant Power Laundry & Media Renderer Service",
    description="Automated rendering engine for laundry care tips and flyers",
    version="1.0.0"
)

# Enable CORS for API integrations (Make.com, webhooks, dashboards)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "chess-reel-renderer",
        "endpoints": [
            "/debug",
            "/render-laundry-flyer",
            "/docs"
        ]
    }


@app.post("/render-laundry-flyer")
@app.post("/render-flyer")
async def render_laundry_flyer_endpoint(req: LaundryFlyerRequest):
    img_bytes = render_laundry_flyer_image(req)
    return Response(content=img_bytes, media_type="image/png")
    
@app.get("/debug")
def run_system_diagnostics():
    openai_key = os.getenv("OPENAI_API_KEY")

    # 1. Check OpenAI API Key & Live Quota Test
    openai_status = {
        "key_present": bool(openai_key),
        "key_prefix": openai_key[:7] + "..." if openai_key else None,
        "api_live_check": "not_tested"
    }

    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            client.models.list()
            openai_status["api_live_check"] = "SUCCESS (Key valid & active)"
        except Exception as e:
            openai_status["api_live_check"] = f"FAILED: {str(e)}"

    # 2. Check Assets Directory and Expected Files
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
        "assets/stickers_overlays/bubble_pattern.png"
    ]

    assets_check = {}
    missing_files = []

    for file_path in expected_files:
        exists = os.path.exists(file_path)
        assets_check[file_path] = "EXISTS" if exists else "MISSING"
        if not exists:
            missing_files.append(file_path)

    # 3. Overall Readiness Summary
    is_ready = (
        openai_status["key_present"]
        and "SUCCESS" in openai_status["api_live_check"]
        and len(missing_files) == 0
    )

    return {
        "status": "READY" if is_ready else "CONFIG_ISSUES_FOUND",
        "working_directory": os.getcwd(),
        "openai": openai_status,
        "missing_assets_count": len(missing_files),
        "missing_assets": missing_files,
        "all_assets": assets_check
    }
    
