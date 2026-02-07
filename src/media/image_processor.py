"""
🎨 Processador de Imagens Avançado
Com remoção de fundo (rembg) e seleção inteligente de imagens
"""
from PIL import Image, ImageEnhance, ImageFilter
import requests
from io import BytesIO
import logging
from typing import List, Optional, Tuple

# Tentar importar rembg para remoção de fundo
try:
    from rembg import remove as remove_bg
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

logger = logging.getLogger(__name__)


class AestheticImageProcessor:
    """
    Processador de imagens para e-commerce com:
    - Seleção inteligente das melhores imagens
    - Remoção de fundo (se rembg disponível)
    - Remoção de watermarks
    - Padronização de tamanho
    - Melhorias de qualidade
    """

    def __init__(self, max_images: int = 6, target_size: tuple = (1200, 1500)):
        self.max_images = max_images
        self.target_size = target_size
        self.timeout = 15

        if REMBG_AVAILABLE:
            logger.info("✅ rembg disponível - remoção de fundo ativada")
        else:
            logger.info("⚠️ rembg não disponível - usando processamento básico")

    def process_product_images(self, image_urls: List[str]) -> List[bytes]:
        """
        Pipeline completo de processamento de imagens

        1. Seleciona as melhores imagens (se > max_images)
        2. Processa cada imagem (fundo, tamanho, qualidade)
        3. Retorna lista de bytes WebP
        """
        # Selecionar melhores imagens se tiver muitas
        if len(image_urls) > self.max_images:
            selected_urls = self._select_best_images(image_urls)
        else:
            selected_urls = image_urls[:self.max_images]

        processed = []
        for idx, url in enumerate(selected_urls, 1):
            try:
                img = self._download_image(url)
                if img is None:
                    continue

                # Converter para RGB se necessário
                img = self._ensure_rgb(img)

                # Tentar remover fundo com rembg
                if REMBG_AVAILABLE:
                    try:
                        img = self._remove_background_ai(img)
                    except Exception as e:
                        logger.warning(f"rembg falhou, usando crop: {e}")
                        img = self._remove_watermarks(img)
                else:
                    img = self._remove_watermarks(img)

                # Padronizar tamanho com centralização inteligente
                img = self._smart_resize(img)

                # Melhorar qualidade
                img = self._enhance_quality(img)

                # Converter para WebP
                processed.append(self._to_webp(img))

            except Exception as e:
                logger.error(f"Erro ao processar imagem {idx}: {e}")
                continue

        return processed

    def _select_best_images(self, image_urls: List[str]) -> List[str]:
        """
        Seleciona as melhores imagens baseado em:
        - Tamanho (maior = melhor)
        - Proporção (mais próximo de 4:5 = melhor)
        - Descarta imagens muito pequenas
        """
        candidates = []

        for url in image_urls[:20]:  # Analisar no máximo 20
            try:
                # Baixar imagem para analisar
                response = requests.get(url, timeout=10)
                img = Image.open(BytesIO(response.content))
                w, h = img.size

                # Descartar muito pequenas
                if w < 400 or h < 400:
                    continue

                # Calcular score
                target_ratio = self.target_size[0] / self.target_size[1]
                current_ratio = w / h
                ratio_diff = abs(current_ratio - target_ratio)

                # Score: tamanho - penalidade por proporção errada
                score = (w * h) / 1000000 - ratio_diff * 5

                candidates.append({'url': url, 'score': score})

            except:
                continue

        # Ordenar por score e retornar top N
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return [c['url'] for c in candidates[:self.max_images]]

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download de imagem com tratamento de erros"""
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

    def _remove_background_ai(self, img: Image.Image) -> Image.Image:
        """
        Remove fundo usando rembg (IA)
        Retorna imagem com fundo branco
        """
        # rembg funciona melhor com PNG/bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # Remover fundo
        output_bytes = remove_bg(img_bytes.getvalue())
        img_no_bg = Image.open(BytesIO(output_bytes))

        # Criar fundo branco
        white_bg = Image.new('RGB', img_no_bg.size, (255, 255, 255))

        # Compor imagem sem fundo sobre fundo branco
        if img_no_bg.mode == 'RGBA':
            white_bg.paste(img_no_bg, (0, 0), img_no_bg)
        else:
            white_bg.paste(img_no_bg, (0, 0))

        return white_bg

    def _remove_watermarks(self, img: Image.Image) -> Image.Image:
        """
        Remove watermarks via crop das bordas
        Crop 5% de cada lado (onde geralmente ficam marcas)
        """
        w, h = img.size
        # Crop mais conservador: 5% de cada lado
        left = int(w * 0.05)
        top = int(h * 0.05)
        right = int(w * 0.95)
        bottom = int(h * 0.95)
        return img.crop((left, top, right, bottom))

    def _smart_resize(self, img: Image.Image) -> Image.Image:
        """
        Redimensiona inteligentemente mantendo produto centralizado
        em canvas branco do tamanho alvo
        """
        tw, th = self.target_size
        target_ratio = tw / th

        w, h = img.size
        current_ratio = w / h

        # Calcular novo tamanho mantendo proporção
        if current_ratio > target_ratio:
            # Imagem muito larga - ajustar pela largura
            new_width = tw
            new_height = int(tw / current_ratio)
        else:
            # Imagem muito alta - ajustar pela altura
            new_height = th
            new_width = int(th * current_ratio)

        # Redimensionar
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Criar canvas branco e centralizar
        canvas = Image.new('RGB', self.target_size, (255, 255, 255))
        x = (tw - new_width) // 2
        y = (th - new_height) // 2
        canvas.paste(img_resized, (x, y))

        return canvas

    def _enhance_quality(self, img: Image.Image) -> Image.Image:
        """Ajustes de qualidade para visual profissional"""
        # Brilho +5%
        img = ImageEnhance.Brightness(img).enhance(1.05)
        # Contraste +10%
        img = ImageEnhance.Contrast(img).enhance(1.10)
        # Saturação +5%
        img = ImageEnhance.Color(img).enhance(1.05)
        # Nitidez +15%
        img = ImageEnhance.Sharpness(img).enhance(1.15)
        return img

    def _to_webp(self, img: Image.Image, quality: int = 90) -> bytes:
        """Converte para WebP com alta qualidade"""
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=quality)
        return buf.getvalue()

