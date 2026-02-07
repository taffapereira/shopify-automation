# 🚀 SISTEMA DE PÓS-PROCESSAMENTO SHOPIFY v5

**Data:** 07/02/2026  
**Repositório:** https://github.com/taffapereira/shopify-automation

---

## ✅ O QUE FOI IMPLEMENTADO

### 1. **Processamento de Imagens** (`src/media/image_processor.py`)
- ✅ Download automático de até 6 imagens por produto
- ✅ Remoção de watermarks (crop 8% bordas)
- ✅ Padronização de tamanho 1200x1500 (proporção 4:5)
- ✅ Melhorias de qualidade:
  - Brilho +5%
  - Contraste +10%
  - Saturação +10%
  - Nitidez +15%
- ✅ Conversão para WebP (qualidade 85%)

### 2. **Geração de Conteúdo com IA** (`src/ai/content_generator.py`)
- ✅ Integração com Google Gemini (nova API `google.genai`)
- ✅ Prompt otimizado para e-commerce brasileiro
- ✅ Geração de:
  - Títulos clean (sem emojis, max 60 chars)
  - Descrições HTML estruturadas
  - Tradução automática de cores (EN→PT)
  - Tags relevantes
- ✅ Fallback para quando Gemini falha

### 3. **Calculadora de Preços** (`src/pricing/advanced_calculator.py`)
- ✅ **Markup global: 2.5x**
- ✅ Cálculo completo de impostos:
  - Imposto de Importação: 15%
  - ICMS: 18% (cálculo por dentro)
- ✅ Frete por categoria
- ✅ Arredondamento psicológico (R$ X,90)
- ✅ Cálculo de parcelamento (até 12x)
- ✅ Margem de lucro real

### 4. **Script Principal** (`scripts/enhance_existing_products.py`)
- ✅ Pipeline completo de pós-processamento
- ✅ Modo dry-run para testes
- ✅ Relatório de execução
- ✅ Rate limiting automático

---

## 📊 TABELA DE PREÇOS (Markup 2.5)

| Custo Real | + Frete | + Impostos | Preço Venda | Margem |
|------------|---------|------------|-------------|--------|
| R$ 20      | R$ 35   | R$ 47      | R$ 119,90   | ~60%   |
| R$ 40      | R$ 55   | R$ 75      | R$ 189,90   | ~60%   |
| R$ 60      | R$ 75   | R$ 102     | R$ 259,90   | ~60%   |
| R$ 80      | R$ 95   | R$ 129     | R$ 319,90   | ~60%   |
| R$ 100     | R$ 115  | R$ 156     | R$ 389,90   | ~60%   |

---

## 🎯 COMO USAR

### Teste com 1 produto (dry-run):
```bash
cd /Users/taffarel/Desktop/shopify-automation
python3 scripts/enhance_existing_products.py --dry-run --limit 1
```

### Processar coleção específica:
```bash
python3 scripts/enhance_existing_products.py --collection bolsas --limit 10
```

### Processar TODOS os produtos:
```bash
python3 scripts/enhance_existing_products.py
```

---

## 📁 ESTRUTURA DE ARQUIVOS

```
shopify-automation/
├── src/
│   ├── media/
│   │   └── image_processor.py     # ✅ Processamento de imagens
│   ├── ai/
│   │   └── content_generator.py   # ✅ Geração com Gemini
│   └── pricing/
│       └── advanced_calculator.py # ✅ Calculadora de preços
├── scripts/
│   └── enhance_existing_products.py  # ✅ Script principal
├── config/
│   └── taxas.json                 # ✅ Configuração de markup
└── .env                           # Chaves de API
```

---

## ⚙️ CONFIGURAÇÃO (.env)

```env
# Shopify
SHOPIFY_STORE_URL=gpyvfv-1k.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxx
SHOPIFY_API_VERSION=2024-01

# Google Gemini
GOOGLE_API_KEY=AIzaSyxxx

# Markup
DEFAULT_MARKUP=2.5
```

---

## 🔧 PRÓXIMOS PASSOS

1. **Executar dry-run** para validar comportamento
2. **Processar 5-10 produtos** como teste
3. **Verificar manualmente** os resultados
4. **Processar todos** se satisfeito

---

## ⚠️ OBSERVAÇÕES

- O Gemini pode falhar ocasionalmente - há fallback automático
- Preços são ESTIMADOS baseados no preço atual (que estava errado)
- Imagens são processadas mas NÃO são re-uploadadas (limitação da API)
- Para upload de imagens, seria necessário usar Files API

---

## 📞 SUPORTE

Repositório: https://github.com/taffapereira/shopify-automation

