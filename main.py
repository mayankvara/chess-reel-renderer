from fastapi import FastAPI, Response, HTTPException
from flyer_service import LaundryFlyerRequest, render_laundry_flyer_image

app = FastAPI()

@app.post("/render-flyer")
@app.post("/render-laundry-flyer")
async def render_laundry_flyer_endpoint(req: LaundryFlyerRequest):
    try:
        img_bytes = render_laundry_flyer_image(req)
        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
