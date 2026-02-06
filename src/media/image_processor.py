"""
🖼️ Processador de Imagens
Adiciona marca d'água e processa imagens de produtos
"""
import os
import io
import base64
import logging
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import requests

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Processador de imagens para produtos"""

    def __init__(
        self,
        marca_dagua: str = "TWP",
        tamanho_padrao: Tuple[int, int] = (800, 800),
        qualidade: int = 85,
        opacidade_marca: int = 150
    ):
        """
        Inicializa processador

        Args:
            marca_dagua: Texto da marca d'água
            tamanho_padrao: Tamanho padrão das imagens (largura, altura)
            qualidade: Qualidade JPEG (0-100)
            opacidade_marca: Opacidade da marca d'água (0-255)
        """
        self.marca_dagua = marca_dagua
        self.tamanho_padrao = tamanho_padrao
        self.qualidade = qualidade
        self.opacidade_marca = opacidade_marca

    def baixar_imagem(self, url: str) -> Optional[Image.Image]:
        """
        Baixa imagem de uma URL

        Args:
            url: URL da imagem

        Returns:
            PIL Image ou None
        """
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
        except Exception as e:
            logger.error(f"Erro ao baixar imagem: {e}")
        return None

    def adicionar_marca_dagua(self, img: Image.Image) -> Image.Image:
        """
        Adiciona marca d'água na imagem

        Args:
            img: Imagem PIL

        Returns:
            Imagem com marca d'água
        """
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Cria layer para marca d'água
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)

        # Tamanho da fonte proporcional à imagem
        font_size = max(30, img.width // 15)

        # Tenta carregar fonte
        try:
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/SFNSDisplay.ttf",
                "/Library/Fonts/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
            font = None
            for path in font_paths:
                if os.path.exists(path):
                    font = ImageFont.truetype(path, font_size)
                    break
            if not font:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        # Calcula posição (canto inferior direito)
        bbox = draw.textbbox((0, 0), self.marca_dagua, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        margin = 20
        x = img.width - text_width - margin
        y = img.height - text_height - margin

        # Desenha sombra
        draw.text((x + 2, y + 2), self.marca_dagua, font=font, fill=(0, 0, 0, 80))

        # Desenha texto principal
        draw.text((x, y), self.marca_dagua, font=font, fill=(255, 255, 255, self.opacidade_marca))

        # Combina
        resultado = Image.alpha_composite(img, watermark)
        return resultado.convert('RGB')

    def processar(self, img: Image.Image) -> Image.Image:
        """
        Processa imagem completa: redimensiona, melhora, marca d'água

        Args:
            img: Imagem PIL

        Returns:
            Imagem processada
        """
        # Redimensiona mantendo proporção
        img.thumbnail(self.tamanho_padrao, Image.Resampling.LANCZOS)

        # Cria fundo branco quadrado
        resultado = Image.new('RGB', self.tamanho_padrao, (255, 255, 255))

        # Centraliza
        x = (self.tamanho_padrao[0] - img.width) // 2
        y = (self.tamanho_padrao[1] - img.height) // 2

        if img.mode == 'RGBA':
            resultado.paste(img, (x, y), img)
        else:
            resultado.paste(img, (x, y))

        # Melhora contraste
        enhancer = ImageEnhance.Contrast(resultado)
        resultado = enhancer.enhance(1.05)

        # Adiciona marca d'água
        resultado = self.adicionar_marca_dagua(resultado)

        return resultado

    def processar_url(self, url: str) -> Optional[Image.Image]:
        """
        Baixa e processa imagem de URL

        Args:
            url: URL da imagem

        Returns:
            Imagem processada ou None
        """
        img = self.baixar_imagem(url)
        if img:
            return self.processar(img)
        return None

    def para_base64(self, img: Image.Image) -> str:
        """
        Converte imagem para base64

        Args:
            img: Imagem PIL

        Returns:
            String base64
        """
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=self.qualidade)
        return base64.b64encode(buffer.getvalue()).decode()

    def salvar(self, img: Image.Image, caminho: str):
        """
        Salva imagem em arquivo

        Args:
            img: Imagem PIL
            caminho: Caminho do arquivo
        """
        img.save(caminho, format='JPEG', quality=self.qualidade)
        logger.info(f"✅ Imagem salva: {caminho}")

