# Shopify Automation

## Descrição
Projeto de automação e integração com a API da Shopify. Permite gerenciar produtos, pedidos, clientes e configurações da loja de forma programática.

## Requisitos
- Python 3.x
- Conta Shopify com acesso à API

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure o arquivo `.env` com suas credenciais

## Configuração

Crie um arquivo `.env` na raiz do projeto com:

```env
SHOPIFY_STORE_URL=sua-loja.myshopify.com
SHOPIFY_ACCESS_TOKEN=seu_token_de_acesso
SHOPIFY_API_VERSION=2025-04
```

## Funcionalidades

### 📦 Produtos (`src/produtos.py`)
- `listar_produtos()` - Lista todos os produtos
- `obter_produto(id)` - Detalhes de um produto
- `criar_produto(titulo, descricao, preco, ...)` - Cria produto
- `atualizar_produto(id, **kwargs)` - Atualiza produto
- `deletar_produto(id)` - Remove produto
- `atualizar_preco(id, preco)` - Altera preço
- `atualizar_estoque(item_id, location_id, qtd)` - Altera estoque

### 📋 Pedidos (`src/pedidos.py`)
- `listar_pedidos(status)` - Lista pedidos
- `obter_pedido(id)` - Detalhes de um pedido
- `cancelar_pedido(id, motivo)` - Cancela pedido
- `fechar_pedido(id)` - Fecha pedido
- `reabrir_pedido(id)` - Reabre pedido fechado
- `adicionar_nota_pedido(id, nota)` - Adiciona nota
- `criar_fulfillment(id, tracking, ...)` - Marca como enviado

### 👥 Clientes (`src/clientes.py`)
- `listar_clientes()` - Lista todos os clientes
- `obter_cliente(id)` - Detalhes de um cliente
- `criar_cliente(email, nome, ...)` - Cria cliente
- `atualizar_cliente(id, **kwargs)` - Atualiza cliente
- `deletar_cliente(id)` - Remove cliente
- `buscar_clientes(query)` - Busca clientes
- `pedidos_do_cliente(id)` - Pedidos de um cliente

### ⚙️ Configurações (`src/loja.py`)
- `obter_info_loja()` - Informações da loja
- `listar_localizacoes()` - Locais de estoque
- `listar_politicas()` - Políticas da loja
- `listar_paises_envio()` - Zonas de envio
- `listar_gateways_pagamento()` - Meios de pagamento
- `listar_temas()` - Temas instalados
- `listar_colecoes()` - Coleções de produtos
- `criar_colecao(titulo, descricao)` - Nova coleção
- `adicionar_produto_colecao(col_id, prod_id)` - Produto em coleção

## Uso

### Testar conexão
```bash
python main.py
```

### Usar módulos
```python
from src import listar_produtos, criar_produto, listar_pedidos

# Listar produtos
produtos = listar_produtos()

# Criar produto
criar_produto(
    titulo="Camiseta Azul",
    descricao="<p>Camiseta 100% algodão</p>",
    preco="59.90",
    status="draft"
)

# Listar pedidos abertos
pedidos = listar_pedidos(status="open")
```

## Estrutura do Projeto

```
shopify-automation/
├── config/              # Configurações
├── data/                # Dados permanentes
├── docs/                # Documentação
├── logs/                # Logs (auto-limpeza: 14 dias)
├── relatorios/          # Relatórios (auto-limpeza: 30 dias)
├── scripts/             # Scripts utilitários
├── temp/                # Temporários (auto-limpeza: 1 dia)
├── testes/              # Testes (auto-limpeza: 7 dias)
├── src/                 # Código fonte
│   ├── __init__.py      # Exports do pacote
│   ├── produtos.py      # CRUD de produtos
│   ├── pedidos.py       # Gerenciamento de pedidos
│   ├── clientes.py      # CRUD de clientes
│   ├── loja.py          # Configurações da loja
│   └── utils.py         # Utilitários e limpeza
├── main.py              # Ponto de entrada
├── requirements.txt     # Dependências
└── .env                 # Variáveis de ambiente
```

## 🧹 Limpeza Automática

O projeto inclui um sistema de limpeza para evitar acúmulo de arquivos temporários:

| Diretório | Retenção | Uso |
|-----------|----------|-----|
| `temp/` | 1 dia | Arquivos temporários |
| `testes/` | 7 dias | Resultados de testes |
| `logs/` | 14 dias | Logs de execução |
| `relatorios/` | 30 dias | Relatórios gerados |

### Comandos de limpeza:

```python
from src import limpar_tudo, status_diretorios, salvar_relatorio

# Ver status dos diretórios
status_diretorios()

# Simular limpeza (não remove nada)
limpar_tudo(dry_run=True)

# Executar limpeza real
limpar_tudo(dry_run=False)

# Salvar arquivos (serão limpos automaticamente depois)
salvar_relatorio("vendas.csv", conteudo)
salvar_arquivo_temp("dados.json", conteudo)
salvar_teste("teste_api.txt", resultado)
```

## APIs Utilizadas

- **Admin API (REST)** - Gerenciar produtos, pedidos, clientes
- **Fulfillment API** - Envios e rastreamento
- **Inventory API** - Controle de estoque

## Licença
MIT
