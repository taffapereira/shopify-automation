"""
🎨 Processador de Imagens Avançado
Com remoção de fundo (remove.bg API ou rembg local) e seleção inteligente
"""
from PIL import Image, ImageEnhance, ImageFilter
import requests
import os
from io import BytesIO
import logging
from typing import List, Optional, Tuple

# Tentar importar rembg para remoção de fundo local
try:
    from rembg import remove as remove_bg_local
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

logger = logging.getLogger(__name__)


class AestheticImageProcessor:
    """
    Processador de imagens para e-commerce com:
    - Seleção inteligente das melhores imagens
    - Remoção de fundo via API (remove.bg) ou local (rembg)
    - Padronização de tamanho com centralização
    - Melhorias de qualidade
    """

    def __init__(self, max_images: int = 6, target_size: tuple = (1200, 1500)):
        self.max_images = max_images
        self.target_size = target_size
        self.timeout = 15

        # API Key do remove.bg (gratuito: 50 imagens/mês)
        self.removebg_api_key = os.getenv('REMOVEBG_API_KEY')

        # Decidir qual método usar
        if self.removebg_api_key:
            logger.info("✅ remove.bg API configurada - remoção de fundo profissional ativada")
            self.bg_removal_method = 'removebg'
        elif REMBG_AVAILABLE:
            logger.info("✅ rembg disponível - remoção de fundo local ativada")
            self.bg_removal_method = 'rembg'
        else:
            logger.info("⚠️ Nenhum método de remoção de fundo disponível - usando processamento básico")
            self.bg_removal_method = 'basic'

    def process_product_images(self, image_urls: List[str]) -> List[bytes]:
        """
        Pipeline completo de processamento de imagens
        """
        # Selecionar melhores imagens se tiver muitas
        if len(image_urls) > self.max_images:
            selected_urls = self._select_best_images(image_urls)
        else:
            selected_urls = image_urls[:self.max_images]

        processed = []
        for idx, url in enumerate(selected_urls, 1):
            try:
                print(f"   [{idx}/{len(selected_urls)}] Processando imagem...")

                img = self._download_image(url)
                if img is None:
                    continue

                # Converter para RGB se necessário
                img = self._ensure_rgb(img)

                # Aplicar remoção de fundo baseado no método disponível
                if self.bg_removal_method == 'removebg':
                    img = self._remove_background_api(img)
                elif self.bg_removal_method == 'rembg':
                    img = self._remove_background_local(img)
                else:
                    img = self._remove_watermarks(img)

                # Padronizar tamanho com centralização
                img = self._smart_resize(img)

                # Melhorar qualidade
                img = self._enhance_quality(img)

                # Converter para WebP
                processed.append(self._to_webp(img))
                print(f"      ✓ Imagem processada com sucesso")

            except Exception as e:
                logger.error(f"Erro ao processar imagem {idx}: {e}")
                continue

        return processed

    def _remove_background_api(self, img: Image.Image) -> Image.Image:
        """
        Remove fundo usando a API do remove.bg
        Gratuito: 50 imagens/mês (qualidade preview)
        Pago: qualidade full HD
        """
        print(f"      🎨 Removendo fundo via remove.bg API...")

        try:
            # Converter imagem para bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            # Chamar API
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': img_bytes},
                data={
                    'size': 'auto',
                    'format': 'png',
                    'bg_color': 'FFFFFF'  # Fundo branco
                },
                headers={'X-Api-Key': self.removebg_api_key},
                timeout=60
            )

            if response.status_code == 200:
                # Sucesso - retornar imagem processada
                result_img = Image.open(BytesIO(response.content))

                # Converter para RGB com fundo branco
                if result_img.mode == 'RGBA':
                    white_bg = Image.new('RGB', result_img.size, (255, 255, 255))
                    white_bg.paste(result_img, mask=result_img.split()[3])
                    return white_bg
                return result_img.convert('RGB')
            else:
                logger.warning(f"remove.bg API erro: {response.status_code} - {response.text[:100]}")
                # Fallback para processamento básico
                return self._remove_watermarks(img)

        except Exception as e:
            logger.error(f"Erro na API remove.bg: {e}")
            return self._remove_watermarks(img)

    def _remove_background_local(self, img: Image.Image) -> Image.Image:
        """
        Remove fundo usando rembg (local)
        """
        print(f"      🎨 Removendo fundo localmente...")

        try:
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            output_bytes = remove_bg_local(img_bytes.getvalue())
            img_no_bg = Image.open(BytesIO(output_bytes))

            # Criar fundo branco
            white_bg = Image.new('RGB', img_no_bg.size, (255, 255, 255))
            if img_no_bg.mode == 'RGBA':
                white_bg.paste(img_no_bg, mask=img_no_bg.split()[3])
            else:
                white_bg.paste(img_no_bg)

            return white_bg

        except Exception as e:
            logger.error(f"Erro no rembg: {e}")
            return self._remove_watermarks(img)

    def _select_best_images(self, image_urls: List[str]) -> List[str]:
        """Seleciona as melhores imagens baseado em tamanho e proporção"""
        candidates = []

        for url in image_urls[:20]:
            try:
                response = requests.get(url, timeout=10)
                img = Image.open(BytesIO(response.content))
                w, h = img.size

                if w < 400 or h < 400:
                    continue

                target_ratio = self.target_size[0] / self.target_size[1]
                current_ratio = w / h
                ratio_diff = abs(current_ratio - target_ratio)

                score = (w * h) / 1000000 - ratio_diff * 5
                candidates.append({'url': url, 'score': score})

            except:
                continue

        candidates.sort(key=lambda x: x['score'], reverse=True)
        return [c['url'] for c in candidates[:self.max_images]]

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download de imagem"""
        try:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            return Image.open(BytesIO(r.content))
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            return None

    def _ensure_rgb(self, img: Image.Image) -> Image.Image:
        """Garante que a imagem está em modo RGB"""
        if img.mode in ("RGBA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img)
            return bg
        elif img.mode != "RGB":
            return img.convert("RGB")
        return img

    def _remove_watermarks(self, img: Image.Image) -> Image.Image:
        """Remove watermarks via crop conservador das bordas"""
        w, h = img.size
        left = int(w * 0.05)
        top = int(h * 0.05)
        right = int(w * 0.95)
        bottom = int(h * 0.95)
        return img.crop((left, top, right, bottom))

    def _smart_resize(self, img: Image.Image) -> Image.Image:
        """Redimensiona e centraliza em canvas branco"""
        tw, th = self.target_size
        target_ratio = tw / th

        w, h = img.size
        current_ratio = w / h

        if current_ratio > target_ratio:
            new_width = tw
            new_height = int(tw / current_ratio)
        else:
            new_height = th
            new_width = int(th * current_ratio)

        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        canvas = Image.new('RGB', self.target_size, (255, 255, 255))
        x = (tw - new_width) // 2
        y = (th - new_height) // 2
        canvas.paste(img_resized, (x, y))

        return canvas

    def _enhance_quality(self, img: Image.Image) -> Image.Image:
        """Ajustes de qualidade"""
        img = ImageEnhance.Brightness(img).enhance(1.05)
        img = ImageEnhance.Contrast(img).enhance(1.10)
        img = ImageEnhance.Color(img).enhance(1.05)
        img = ImageEnhance.Sharpness(img).enhance(1.15)
        return img

    def _to_webp(self, img: Image.Image, quality: int = 90) -> bytes:
        """Converte para WebP"""
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=quality)
        return buf.getvalue()

