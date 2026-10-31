import io
import math
import textwrap
import urllib.parse
from typing import List, Optional, Tuple, Union

from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

try:
    import qrcode
except ImportError:
    qrcode = None


# ==========================================
# 1. Pydantic Models
# ==========================================

class LaundryFlyerRequest(BaseModel):
    tip_number: Union[int, str] = 1
    category: str = "સિલ્ક અને સાડી"
    headline: str = "અસલી ઝરીવાળી સિલ્ક સાડી પર ક્યારેય સીધો પરફ્યુમ ન છાંટો"
    body_text: str = (
        "પરફ્યુમમાં રહેલ આલ્કોહોલ ઝરીના નાજુક મેટાલિક કોટિંગને નુકસાન પહોંચાડે છે અને કાળી પાડી દે છે. "
        "સુગંધ પહેલા શરીર પર લગાવો, ૨ મિનિટ પછી સાડી પહેરો."
    )
    pro_takeaway: str = (
        "ખાસ ટીપ: અસલી ઝરીને દર ૩-૪ વપરાશ પછી ડ્રાય ક્લીન કરાવો અને સુતરાઉ કપડામાં લપેટીને સાચવો."
    )
    brand_name: str = "વસંત પાવર લોન્ડ્રી"
    brand_tagline: str = "૧૯૯૫થી વિશ્વસનીય ગુણવત્તા અને સંભાળ"
    phone_number: str = "9033281622"
    shop_address: str = "વાઘેશ્વરી પ્લોટ, પોરબંદર"
    canvas_size: Tuple[int, int] = (1080, 1440)


class BusinessFlyerRequest(BaseModel):
    business_name: str = "Vasant Power Laundry"
    tagline: str = "Crisp • Clean • Express Care"
    headline: str = "Premium Laundry & Steam Pressing"
    subheadline: str = "Fast turnaround, hygienic washing, and door-to-door convenience."
    services: List[str] = [
        "Wash & Fold",
        "Steam Ironing / Pressing",
        "Dry Cleaning Care",
        "Curtain & Blanket Deep Clean"
    ]
    offer_badge: str = "Starting at ₹99 / Month / Plans Available"
    phone_or_whatsapp: str = "+91 9033281622"
    address_line: str = "Wagheshwari Plot, Porbandar"
    cta_text: str = "Drop Off Today / WhatsApp for Pickup"
    canvas_size: Tuple[int, int] = (1080, 1080)


class ChessQuoteFlyerRequest(BaseModel):
    quote: str
    player: str
    designation: str = "World Champion"
    branding: str = "Chess Players Ahmedabad"
    canvas_size: Tuple[int, int] = (1080, 1080)


# ==========================================
# 2. Font Loader with Gujarati Unicode Support
# ==========================================

def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        # Gujarati Noto Fonts (Linux / Render standard)
        "/usr/share/fonts/truetype/noto/NotoSansGujarati-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansGujarati-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansGujarati-Medium.ttf",
        "/usr/share/fonts/truetype/lohit-gujarati/Lohit-Gujarati.ttf",
        "/usr/share/fonts/truetype/samyak-fonts/Samyak-Gujarati.ttf",
        "assets/fonts/NotoSansGujarati-Bold.ttf" if bold else "assets/fonts/NotoSansGujarati-Regular.ttf",
        "NotoSansGujarati-Bold.ttf" if bold else "NotoSansGujarati-Regular.ttf",
        # Windows Gujarati system fonts
        "C:\\Windows\\Fonts\\shrutib.ttf" if bold else "C:\\Windows\\Fonts\\shruti.ttf",
        "C:\\Windows\\Fonts\\shruti.ttf",
        # Latin fallbacks
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf"
    ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# ==========================================
# 3. Vector Math & Scannable QR Code Helpers
# ==========================================

def quad_bezier(p0, p1, p2, steps: int = 30):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def generate_scannable_qr(data_url: str, size: int = 115) -> Image.Image:
    if qrcode is not None:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=2,
        )
        qr.add_data(data_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        return img.resize((size, size), Image.NEAREST)

    try:
        import cv2
        import numpy as np

        encoder = cv2.QRCodeEncoder.create()
        mat = encoder.encode(data_url)
        img_arr = np.where(mat == 255, 0, 255).astype(np.uint8) if mat[0, 0] == 255 else np.where(mat == 1, 0, 255).astype(np.uint8)
        qr_raw = Image.fromarray(img_arr, mode="L")
        padded = Image.new("L", (qr_raw.width + 4, qr_raw.height + 4), color=255)
        padded.paste(qr_raw, (2, 2))
        return padded.resize((size, size), Image.NEAREST).convert("RGB")
    except Exception:
        return Image.new("RGB", (size, size), color=(255, 255, 255))


# ==========================================
# 4. Master Gujarati Ornate Flyer Generator
# ==========================================

def render_laundry_flyer_image(req: LaundryFlyerRequest) -> bytes:
    width, height = req.canvas_size
    img = Image.new("RGB", (width, height), color="#060E22")
    draw = ImageDraw.Draw(img)

    for y in range(height):
        dy = abs(y - height // 2) / (height // 2)
        r = int(6 + (1 - dy) * 10)
        g = int(14 + (1 - dy) * 18)
        b = int(34 + (1 - dy) * 44)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    GOLD_LIGHT = (255, 242, 175)
    GOLD_CORE  = (226, 178, 48)
    GOLD_MED   = (188, 142, 32)
    GOLD_DARK  = (135, 96, 18)
    GOLD_DEEP  = (75, 50, 10)

    # 5-Tier Framing Rails
    draw.rectangle([28, 28, width - 28, height - 28], outline=GOLD_DEEP, width=1)
    draw.rectangle([34, 34, width - 34, height - 34], outline=GOLD_DARK, width=1)
    draw.rectangle([44, 44, width - 44, height - 44], outline=GOLD_CORE, width=3)
    draw.rectangle([54, 54, width - 54, height - 54], outline=GOLD_DARK, width=1)
    draw.rectangle([60, 60, width - 60, height - 60], outline=GOLD_DEEP, width=1)

    pearl_margin = 44
    for px in range(210, width - 210, 20):
        draw.ellipse([px - 2, pearl_margin - 2, px + 2, pearl_margin + 2], fill=GOLD_LIGHT, outline=GOLD_DARK)
        draw.ellipse([px - 2, height - pearl_margin - 2, px + 2, height - pearl_margin + 2], fill=GOLD_LIGHT, outline=GOLD_DARK)
    for py in range(210, height - 210, 20):
        draw.ellipse([pearl_margin - 2, py - 2, pearl_margin + 2, py + 2], fill=GOLD_LIGHT, outline=GOLD_DARK)
        draw.ellipse([width - pearl_margin - 2, py - 2, width - pearl_margin + 2, py + 2], fill=GOLD_LIGHT, outline=GOLD_DARK)

    # Corner Medallions & Stepped Brackets
    def draw_corner_ornament(cx, cy, sx, sy):
        draw.line([(cx, cy + sy * 16), (cx + sx * 135, cy + sy * 16)], fill=GOLD_CORE, width=2)
        draw.line([(cx + sx * 16, cy), (cx + sx * 16, cy + sy * 135)], fill=GOLD_CORE, width=2)
        draw.line([(cx, cy + sy * 24), (cx + sx * 105, cy + sy * 24)], fill=GOLD_DARK, width=1)
        draw.line([(cx + sx * 24, cy), (cx + sx * 24, cy + sy * 105)], fill=GOLD_DARK, width=1)

        pts_arc1 = quad_bezier((cx + sx * 16, cy + sy * 95), (cx + sx * 40, cy + sy * 40), (cx + sx * 95, cy + sy * 16))
        draw.line(pts_arc1, fill=GOLD_LIGHT, width=2)
        pts_arc2 = quad_bezier((cx + sx * 24, cy + sy * 75), (cx + sx * 45, cy + sy * 45), (cx + sx * 75, cy + sy * 24))
        draw.line(pts_arc2, fill=GOLD_MED, width=1)

        draw.line([(cx + sx * 16, cy + sy * 16), (cx + sx * 80, cy + sy * 80)], fill=GOLD_CORE, width=2)
        draw.line([(cx + sx * 80, cy + sy * 80), (cx + sx * 120, cy + sy * 120)], fill=GOLD_DARK, width=1)

        dia_cx, dia_cy = cx + sx * 34, cy + sy * 34
        for d_sz, fill_col, out_col in [(16, GOLD_DEEP, GOLD_CORE), (11, GOLD_CORE, GOLD_DARK), (6, GOLD_LIGHT, None)]:
            poly = [(dia_cx, dia_cy - d_sz), (dia_cx + d_sz, dia_cy), (dia_cx, dia_cy + d_sz), (dia_cx - d_sz, dia_cy)]
            draw.polygon(poly, fill=fill_col, outline=out_col)

        for dist_s in [72, 110]:
            draw.ellipse([cx + sx * dist_s - 3, cy + sy * 16 - 3, cx + sx * dist_s + 3, cy + sy * 16 + 3], fill=GOLD_LIGHT, outline=GOLD_DARK)
            draw.ellipse([cx + sx * 16 - 3, cy + sy * dist_s - 3, cx + sx * 16 + 3, cy + sy * dist_s + 3], fill=GOLD_LIGHT, outline=GOLD_DARK)

        j_x, j_y = cx + sx * 6, cy + sy * 6
        draw.polygon([(j_x, j_y - 6), (j_x + 6, j_y), (j_x, j_y + 6), (j_x - 6, j_y)], fill=GOLD_LIGHT, outline=GOLD_CORE)

    corner_inset = 44
    draw_corner_ornament(corner_inset, corner_inset, 1, 1)
    draw_corner_ornament(width - corner_inset, corner_inset, -1, 1)
    draw_corner_ornament(corner_inset, height - corner_inset, 1, -1)
    draw_corner_ornament(width - corner_inset, height - corner_inset, -1, -1)

    # Ornate Separators
    def draw_ornate_separator(y_pos, span=380):
        mid_x = width // 2
        draw.polygon([(mid_x, y_pos - 12), (mid_x + 14, y_pos), (mid_x, y_pos + 12), (mid_x - 14, y_pos)], fill=GOLD_DEEP, outline=GOLD_CORE)
        draw.polygon([(mid_x, y_pos - 7), (mid_x + 8, y_pos), (mid_x, y_pos + 7), (mid_x - 8, y_pos)], fill=GOLD_LIGHT)

        for dir_val in [-1, 1]:
            s_pts = quad_bezier((mid_x + dir_val * 16, y_pos), (mid_x + dir_val * 32, y_pos - 10), (mid_x + dir_val * 48, y_pos))
            draw.line(s_pts, fill=GOLD_LIGHT, width=2)
            for dx in [28, 48, 64]:
                r = 4 if dx == 28 else (3 if dx == 48 else 2)
                draw.ellipse([mid_x + dir_val * dx - r, y_pos - r, mid_x + dir_val * dx + r, y_pos + r], fill=GOLD_CORE, outline=GOLD_DARK)

            draw.line([(mid_x + dir_val * 76, y_pos), (mid_x + dir_val * span, y_pos)], fill=GOLD_CORE, width=2)
            draw.line([(mid_x + dir_val * 90, y_pos + 4), (mid_x + dir_val * (span - 30), y_pos + 4)], fill=GOLD_DARK, width=1)
            tip_x = mid_x + dir_val * span
            draw.polygon([(tip_x, y_pos - 4), (tip_x + dir_val * 5, y_pos), (tip_x, y_pos + 4), (tip_x - dir_val * 5, y_pos)], fill=GOLD_LIGHT)

    font_crest = get_font(36, bold=True)
    font_pill = get_font(24, bold=True)
    font_head = get_font(40, bold=True)
    font_body = get_font(26, bold=False)
    font_pro = get_font(23, bold=True)
    font_cta = get_font(26, bold=True)
    font_contact_title = get_font(24, bold=True)
    font_contact_sub = get_font(20, bold=False)
    font_qr_label = get_font(12, bold=True)

    # Monogram Shield
    crest_cy = 118
    draw.polygon(
        [
            (width // 2, crest_cy - 44),
            (width // 2 + 48, crest_cy - 8),
            (width // 2 + 34, crest_cy + 38),
            (width // 2, crest_cy + 50),
            (width // 2 - 34, crest_cy + 38),
            (width // 2 - 48, crest_cy - 8),
        ],
        fill=(10, 26, 60),
        outline=GOLD_CORE,
        width=2,
    )
    draw.line([(width // 2 - 18, crest_cy - 12), (width // 2, crest_cy + 22)], fill=GOLD_LIGHT, width=3)
    draw.line([(width // 2, crest_cy + 22), (width // 2 + 18, crest_cy - 12)], fill=GOLD_LIGHT, width=3)

    for ci in [-3, -2, -1, 0, 1, 2, 3]:
        cx_c = width // 2 + ci * 14
        cy_c = crest_cy - 48 - (5 if ci == 0 else (2 if abs(ci) == 1 else -3))
        draw.ellipse([cx_c - 3, cy_c - 3, cx_c + 3, cy_c + 3], fill=GOLD_LIGHT, outline=GOLD_DARK)

    # Brand Title
    draw_ornate_separator(184, span=330)
    brand_text = req.brand_name
    bbox = draw.textbbox((0, 0), brand_text, font=font_crest)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2 + 2, 202), brand_text, fill=(0, 0, 0), font=font_crest)
    draw.text(((width - tw) // 2, 200), brand_text, fill=GOLD_LIGHT, font=font_crest)

    # Tip Pill
    pill_y = 268
    tip_text = f"ટીપ નં. {str(req.tip_number).strip()}  |  {req.category}"
    tbox = draw.textbbox((0, 0), tip_text, font=font_pill)
    ptw = tbox[2] - tbox[0]
    pill_w = max(560, ptw + 60)
    pill_h = 56
    px = (width - pill_w) // 2
    draw.rounded_rectangle([px, pill_y, px + pill_w, pill_y + pill_h], radius=16, fill=(15, 34, 75), outline=GOLD_CORE, width=2)
    draw.rounded_rectangle([px + 4, pill_y + 4, px + pill_w - 4, pill_y + pill_h - 4], radius=12, outline=GOLD_MED, width=1)
    draw.polygon([(px - 14, pill_y + pill_h // 2), (px, pill_y + 14), (px, pill_y + pill_h - 14)], fill=GOLD_DARK, outline=GOLD_CORE)
    draw.polygon([(px + pill_w + 14, pill_y + pill_h // 2), (px + pill_w, pill_y + 14), (px + pill_w, pill_y + pill_h - 14)], fill=GOLD_DARK, outline=GOLD_CORE)
    draw.text(((width - ptw) // 2, pill_y + 13), tip_text, fill=GOLD_LIGHT, font=font_pill)

    # Headline
    head_y = 358
    head_lines = textwrap.wrap(req.headline, width=26)
    for hline in head_lines:
        hbox = draw.textbbox((0, 0), hline, font=font_head)
        hw = hbox[2] - hbox[0]
        draw.text(((width - hw) // 2 + 2, head_y + 2), hline, fill=(0, 0, 0), font=font_head)
        draw.text(((width - hw) // 2, head_y), hline, fill=(255, 255, 255), font=font_head)
        head_y += 56

    # Content Box
    box_w = 900
    box_h = 405
    bx1 = (width - box_w) // 2
    by1 = head_y + 24
    bx2 = bx1 + box_w
    by2 = by1 + box_h

    draw.rectangle([bx1, by1, bx2, by2], fill=(7, 20, 48), outline=GOLD_DARK, width=1)
    draw.rectangle([bx1 + 8, by1 + 8, bx2 - 8, by2 - 8], outline=GOLD_CORE, width=2)
    draw.rectangle([bx1 + 14, by1 + 14, bx2 - 14, by2 - 14], outline=GOLD_DEEP, width=1)

    for cx_b, cy_b, sx, sy in [
        (bx1 + 8, by1 + 8, 1, 1),
        (bx2 - 8, by1 + 8, -1, 1),
        (bx1 + 8, by2 - 8, 1, -1),
        (bx2 - 8, by2 - 8, -1, -1),
    ]:
        draw.line([(cx_b, cy_b + sy * 6), (cx_b + sx * 36, cy_b + sy * 6)], fill=GOLD_LIGHT, width=2)
        draw.line([(cx_b + sx * 6, cy_b), (cx_b + sx * 6, cy_b + sy * 36)], fill=GOLD_LIGHT, width=2)
        cd_x, cd_y = cx_b + sx * 16, cy_b + sy * 16
        draw.polygon([(cd_x, cd_y - 4), (cd_x + 4, cd_y), (cd_x, cd_y + 4), (cd_x - 4, cd_y)], fill=GOLD_LIGHT, outline=GOLD_CORE)

    cur_by = by1 + 42
    body_lines = textwrap.wrap(req.body_text, width=42)
    for bline in body_lines:
        bbox = draw.textbbox((0, 0), bline, font=font_body)
        bw = bbox[2] - bbox[0]
        draw.text(((width - bw) // 2, cur_by), bline, fill=(235, 242, 255), font=font_body)
        cur_by += 44

    # Pro-Tip Plaque
    pro_y = cur_by + 20
    pro_w = box_w - 90
    pro_h = 100
    pro_x = (width - pro_w) // 2
    draw.rounded_rectangle([pro_x, pro_y, pro_x + pro_w, pro_y + pro_h], radius=10, fill=(14, 32, 72), outline=GOLD_CORE, width=2)
    draw.rounded_rectangle([pro_x + 3, pro_y + 3, pro_x + pro_w - 3, pro_y + pro_h - 3], radius=7, outline=GOLD_MED, width=1)

    pro_lines = textwrap.wrap(req.pro_takeaway, width=44)
    pty = pro_y + 16
    for pl in pro_lines:
        pbox = draw.textbbox((0, 0), pl, font=font_pro)
        pw = pbox[2] - pbox[0]
        draw.text(((width - pw) // 2, pty), pl, fill=GOLD_LIGHT, font=font_pro)
        pty += 34

    # CTA Ribbon
    draw_ornate_separator(by2 + 32, span=380)

    cta_y = by2 + 64
    cta_w = 780
    cta_h = 64
    cx = (width - cta_w) // 2

    draw.polygon([(cx - 24, cta_y + cta_h // 2), (cx, cta_y - 5), (cx, cta_y + cta_h + 5)], fill=GOLD_DEEP, outline=GOLD_DARK)
    draw.polygon([(cx + cta_w + 24, cta_y + cta_h // 2), (cx + cta_w, cta_y - 5), (cx + cta_w, cta_y + cta_h + 5)], fill=GOLD_DEEP, outline=GOLD_DARK)
    draw.rounded_rectangle([cx, cta_y, cx + cta_w, cta_y + cta_h], radius=6, fill=GOLD_CORE, outline=GOLD_LIGHT, width=2)
    cta_label = "આજે જ પધારો અને કપડાંને આપો રોયલ ફ્રેશનેસ"
    ctabox = draw.textbbox((0, 0), cta_label, font=font_cta)
    cw = ctabox[2] - ctabox[0]
    draw.text(((width - cw) // 2 + 1, cta_y + 17), cta_label, fill=(0, 0, 0), font=font_cta)

    draw_ornate_separator(cta_y + cta_h + 30, span=390)

    # Contact Card Container
    contact_panel_y = cta_y + cta_h + 48
    contact_panel_w = 840
    contact_panel_h = 185
    cpx = (width - contact_panel_w) // 2

    draw.rounded_rectangle(
        [cpx, contact_panel_y, cpx + contact_panel_w, contact_panel_y + contact_panel_h],
        radius=14,
        fill=(10, 24, 56),
        outline=GOLD_CORE,
        width=2,
    )
    draw.rounded_rectangle(
        [cpx + 4, contact_panel_y + 4, cpx + contact_panel_w - 4, contact_panel_y + contact_panel_h - 4],
        radius=10,
        outline=GOLD_DARK,
        width=1,
    )

    digits = "".join(filter(str.isdigit, str(req.phone_number)))
    if len(digits) == 10:
        clean_phone = f"91{digits}"
    elif len(digits) == 12 and digits.startswith("91"):
        clean_phone = digits
    else:
        clean_phone = digits if digits.startswith("91") else f"91{digits}"

    wa_msg = f"નમસ્તે {req.brand_name}, મારે કપડાંની લોન્ડ્રી અને ડ્રાય ક્લીનિંગ સર્વિસ વિશે પૂછપરછ કરવી છે."
    wa_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(wa_msg)}"
    qr_img = generate_scannable_qr(wa_url, size=115)

    qr_x = cpx + contact_panel_w - 150
    qr_y = contact_panel_y + 16
    draw.rectangle([qr_x - 3, qr_y - 3, qr_x + 115 + 3, qr_y + 115 + 3], fill=(255, 255, 255), outline=GOLD_CORE, width=2)
    img.paste(qr_img, (qr_x, qr_y))

    # Badge below QR code
    qr_badge_w = 125
    qr_badge_h = 24
    qbx = qr_x - 5
    qby = qr_y + 122
    draw.rounded_rectangle([qbx, qby, qbx + qr_badge_w, qby + qr_badge_h], radius=3, fill=GOLD_CORE)
    qr_tag_txt = "સ્કેન વોટ્સએપ"
    q_bbox = draw.textbbox((0, 0), qr_tag_txt, font=font_qr_label)
    qw = q_bbox[2] - q_bbox[0]
    draw.text((qbx + (qr_badge_w - qw) // 2, qby + 4), qr_tag_txt, fill=(0, 0, 0), font=font_qr_label)

    # Contact Info
    text_left_x = cpx + 32
    t_start_y = contact_panel_y + 22

    draw.text((text_left_x, t_start_y), f"કોલ / વોટ્સએપ:  +91 {digits[-10:]}", fill=GOLD_LIGHT, font=font_contact_title)
    draw.text((text_left_x, t_start_y + 38), f"દુકાનનું સરનામું:  {req.shop_address}", fill=(240, 245, 255), font=font_contact_sub)
    draw.text((text_left_x, t_start_y + 72), "પોરબંદરમાં ઘરબેઠા પીકઅપ અને ડિલિવરી સુવિધા", fill=GOLD_MED, font=font_contact_sub)
    draw.text((text_left_x, t_start_y + 106), f"{req.brand_name}  -  {req.brand_tagline}", fill=(175, 195, 230), font=font_contact_sub)

    if img.mode != "RGB":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


# Compatibility alias for laundry flyers
def render_business_flyer_image(req: Union[LaundryFlyerRequest, BusinessFlyerRequest]) -> bytes:
    if isinstance(req, LaundryFlyerRequest):
        return render_laundry_flyer_image(req)
    mapped_req = LaundryFlyerRequest(
        tip_number=1,
        category="General Care",
        headline=req.headline,
        body_text=req.subheadline,
        pro_takeaway=f"Offer: {req.offer_badge}",
        brand_name=req.business_name,
        brand_tagline=req.tagline,
        phone_number=req.phone_or_whatsapp,
        shop_address=req.address_line,
        canvas_size=req.canvas_size
    )
    return render_laundry_flyer_image(mapped_req)


# ==========================================
# 5. Chess Master Quote Flyer Generator (Retained)
# ==========================================

def render_chess_quote_image(req: ChessQuoteFlyerRequest) -> bytes:
    width, height = req.canvas_size
    img = Image.new("RGB", (width, height), color="#0F172A")
    draw = ImageDraw.Draw(img)

    margin = 48
    draw.rounded_rectangle(
        [(margin, margin), (width - margin, height - margin)],
        radius=24,
        outline="#334155",
        width=3
    )

    quote_mark_font = get_font(180, bold=True)
    draw.text((margin + 40, margin + 20), "“", fill="#F59E0B", font=quote_mark_font)

    quote_clean = req.quote.strip('“”"')
    font_size = 56 if len(quote_clean) < 95 else 44
    font_quote = get_font(font_size, bold=True)

    wrap_width = 28 if font_size == 56 else 34
    lines = textwrap.wrap(quote_clean, width=wrap_width)
    wrapped_text = "\n".join(f'"{line}' if i == 0 else line for i, line in enumerate(lines))
    if not wrapped_text.endswith('"'):
        wrapped_text += '"'

    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font_quote, spacing=18)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    quote_x = (width - text_w) // 2
    quote_y = 360 - (text_h // 3)

    draw.multiline_text(
        (quote_x, quote_y),
        wrapped_text,
        fill="#FFFFFF",
        font=font_quote,
        spacing=18,
        align="center"
    )

    author_y = quote_y + text_h + 70
    line_w = 80
    draw.line(
        [((width - line_w) // 2, author_y), ((width + line_w) // 2, author_y)],
        fill="#F59E0B",
        width=4
    )

    font_author = get_font(40, bold=True)
    author_name = req.player.upper()
    abbox = draw.textbbox((0, 0), author_name, font=font_author)
    draw.text(((width - (abbox[2] - abbox[0])) // 2, author_y + 24), author_name, fill="#FBBF24", font=font_author)

    if req.designation:
        font_desig = get_font(26, bold=False)
        dbbox = draw.textbbox((0, 0), req.designation, font=font_desig)
        draw.text(((width - (dbbox[2] - dbbox[0])) // 2, author_y + 76), req.designation, fill="#94A3B8", font=font_desig)

    font_brand = get_font(26, bold=True)
    brand_text = f"♟ {req.branding.upper()} • DAILY INSPIRATION"
    bbbox = draw.textbbox((0, 0), brand_text, font=font_brand)
    bw, bh = bbbox[2] - bbbox[0], bbbox[3] - bbbox[1]

    pill_y = height - margin - 75
    draw.rounded_rectangle(
        [((width - bw) // 2 - 24, pill_y - 8), ((width + bw) // 2 + 24, pill_y + bh + 8)],
        radius=14,
        fill="#1E293B"
    )
    draw.text(((width - bw) // 2, pill_y), brand_text, fill="#E2E8F0", font=font_brand)

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()
    
