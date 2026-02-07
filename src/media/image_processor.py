"""
🎨 Processador de Imagens Aesthetic
"""
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class AestheticImageProcessor:
    def __init__(self, max_images: int = 6, target_size: tuple = (1200, 1500)):
        self.max_images = max_images
        self.target_size = target_size
        self.timeout = 15

    def process_product_images(self, image_urls: List[str]) -> List[bytes]:
        processed = []
        for url in image_urls[:self.max_images]:
            try:
                img = self._download_image(url)
                if img is None:
                    continue
                if img.mode in ("RGBA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        bg.paste(img, mask=img.split()[3])
                    else:
                        bg.paste(img)
                    img = bg
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                img = self._remove_watermarks(img)
                img = self._standardize_size(img)
                img = self._enhance_quality(img)
                processed.append(self._to_webp(img))
            except Exception as e:
                logger.error(f"Erro: {e}")
        return processed

    def _download_image(self, url: str) -> Optional[Image.Image]:
        try:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            return Image.open(BytesIO(r.content))
        except:
            return None

    def _remove_watermarks(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        return img.crop((int(w*0.03), int(h*0.08), int(w*0.97), int(h*0.92)))

    def _standardize_size(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        tw, th = self.target_size
        tr = tw / th
        cr = w / h
        if cr > tr:
            nw = int(h * tr)
            left = (w - nw) // 2
            img = img.crop((left, 0, left + nw, h))
        else:
            nh = int(w / tr)
            top = (h - nh) // 2
            img = img.crop((0, top, w, top + nh))
        return img.resize(self.target_size, Image.Resampling.LANCZOS)

    def _enhance_quality(self, img: Image.Image) -> Image.Image:
        img = ImageEnhance.Brightness(img).enhance(1.05)
        img = ImageEnhance.Contrast(img).enhance(1.10)
        img = ImageEnhance.Color(img).enhance(1.10)
        img = ImageEnhance.Sharpness(img).enhance(1.15)
        return img

    def _to_webp(self, img: Image.Image, quality: int = 85) -> bytes:
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=quality)
        return buf.getvalue()

