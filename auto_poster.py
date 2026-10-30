import os
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image, ImageDraw, ImageFont

# Config
PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
ASSETS_DIR = "./assets"

def init_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    return client.open("Vasant_FB_Automation_Queue").sheet1

def render_post_image(row_data):
    """Dynamically overlays headline, logo, and footer on branded template."""
    base_bg = Image.open(f"{ASSETS_DIR}/templates_bg/bg_cyan.png").resize((1080, 1350))
    draw = ImageDraw.Draw(base_bg)
    
    font_head = ImageFont.truetype(f"{ASSETS_DIR}/fonts/Poppins-Bold.ttf", 64)
    font_sub = ImageFont.truetype(f"{ASSETS_DIR}/fonts/Poppins-Medium.ttf", 36)
    font_footer = ImageFont.truetype(f"{ASSETS_DIR}/fonts/Inter-Regular.ttf", 28)

    # 1. Overlay Logo
    logo = Image.open(f"{ASSETS_DIR}/logo/logo_vasant_white.png").convert("RGBA")
    logo.thumbnail((360, 100))
    base_bg.paste(logo, (540 - logo.width // 2, 70), logo)

    # 2. Draw Main Headline
    headline = row_data["Headline"]
    bbox = draw.textbbox((0, 0), headline, font=font_head)
    draw.text(((1080 - (bbox[2] - bbox[0])) // 2, 220), headline, fill=(255, 255, 255), font=font_head)

    # 3. Paste Footer Bar
    draw.rectangle([(0, 1220), (1080, 1350)], fill=(10, 25, 47))
    footer_text = f"{row_data['CTA_Text']}  |  {row_data['Phone_Number']}  |  {row_data['Location']}"
    f_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    draw.text(((1080 - (f_bbox[2] - f_bbox[0])) // 2, 1265), footer_text, fill=(255, 255, 255), font=font_footer)

    output_path = f"/tmp/{row_data['Post_ID']}.png"
    base_bg.save(output_path, quality=95)
    return output_path

def post_to_facebook(image_path, caption):
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos"
    with open(image_path, "rb") as img_file:
        payload = {
            "caption": caption,
            "access_token": FB_ACCESS_TOKEN
        }
        files = {"source": img_file}
        res = requests.post(url, data=payload, files=files)
        return res.json()

def process_queue():
    sheet = init_sheet()
    rows = sheet.get_all_records()

    for idx, row in enumerate(rows, start=2): # 1-indexed, header is row 1
        if row["Status"] == "Pending":
            img_file = render_post_image(row)
            fb_res = post_to_facebook(img_file, row["Caption_Text"])
            
            if "id" in fb_res:
                sheet.update_cell(idx, 10, "Posted")
                sheet.update_cell(idx, 11, f"https://facebook.com/{fb_res['id']}")
            else:
                sheet.update_cell(idx, 10, "Failed")
            break

if __name__ == "__main__":
    process_queue()
  
