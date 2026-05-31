# utils.py
from PIL import Image, ImageDraw, ImageFont
import io


def apply_watermark(image_bytes: bytes, watermark_text: str) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = image.size

    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = width - text_width - 40
    y = height - text_height - 40

    # draw shadow first so text sits on top
    draw.text((x + 2, y + 2), watermark_text, font=font, fill=(0, 0, 0, 100))
    draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))

    result = Image.alpha_composite(image, overlay).convert("RGB")

    output = io.BytesIO()
    result.save(output, format="JPEG", quality=95)
    return output.getvalue()