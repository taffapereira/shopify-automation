"""
Módulo de utilitários para limpeza e organização do projeto.
Gerencia arquivos temporários, relatórios e itens sazonais.
"""
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Diretórios para arquivos temporários/sazonais
PROJETO_ROOT = Path(__file__).parent.parent
TEMP_DIR = PROJETO_ROOT / "temp"
RELATORIOS_DIR = PROJETO_ROOT / "relatorios"
TESTES_DIR = PROJETO_ROOT / "testes"
LOGS_DIR = PROJETO_ROOT / "logs"

# Configurações de retenção (dias)
RETENCAO_TEMP = 1        # Arquivos temp: 1 dia
RETENCAO_RELATORIOS = 30  # Relatórios: 30 dias
RETENCAO_TESTES = 7       # Testes: 7 dias
RETENCAO_LOGS = 14        # Logs: 14 dias


def criar_estrutura_diretorios():
    """Cria diretórios necessários se não existirem."""
    diretorios = [TEMP_DIR, RELATORIOS_DIR, TESTES_DIR, LOGS_DIR]

    for diretorio in diretorios:
        diretorio.mkdir(exist_ok=True)
        gitkeep = diretorio / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    print("✅ Estrutura de diretórios criada/verificada")
    return diretorios


def listar_arquivos_antigos(diretorio: Path, dias: int):
    """Lista arquivos mais antigos que X dias."""
    if not diretorio.exists():
        return []

    limite = datetime.now() - timedelta(days=dias)
    arquivos_antigos = []

    for arquivo in diretorio.iterdir():
        if arquivo.name.startswith('.'):  # Ignora .gitkeep e similares
            continue

        if arquivo.is_file():
            modificado = datetime.fromtimestamp(arquivo.stat().st_mtime)
            if modificado < limite:
                arquivos_antigos.append({
                    "arquivo": arquivo,
                    "modificado": modificado,
                    "dias": (datetime.now() - modificado).days
                })

    return arquivos_antigos


def limpar_diretorio(diretorio: Path, dias: int, dry_run: bool = True):
    """
    Remove arquivos mais antigos que X dias de um diretório.

    Args:
        diretorio: Caminho do diretório
        dias: Arquivos mais antigos que X dias serão removidos
        dry_run: Se True, apenas lista sem remover (padrão: True)
    """
    arquivos = listar_arquivos_antigos(diretorio, dias)

    if not arquivos:
        print(f"  📁 {diretorio.name}: Nenhum arquivo para limpar")
        return 0

    print(f"\n  📁 {diretorio.name} ({len(arquivos)} arquivos com mais de {dias} dias):")

    removidos = 0
    for item in arquivos:
        arquivo = item["arquivo"]
        dias_idade = item["dias"]

        if dry_run:
            print(f"    🔍 [SIMULAÇÃO] {arquivo.name} ({dias_idade} dias)")
        else:
            try:
                if arquivo.is_dir():
                    shutil.rmtree(arquivo)
                else:
                    arquivo.unlink()
                print(f"    🗑️  Removido: {arquivo.name} ({dias_idade} dias)")
                removidos += 1
            except Exception as e:
                print(f"    ❌ Erro ao remover {arquivo.name}: {e}")

    return removidos


def limpar_tudo(dry_run: bool = True):
    """
    Executa limpeza em todos os diretórios temporários.

    Args:
        dry_run: Se True, apenas mostra o que seria removido (padrão: True)
    """
    print("=" * 60)
    print("🧹 LIMPEZA DE ARQUIVOS TEMPORÁRIOS")
    print("=" * 60)

    if dry_run:
        print("⚠️  MODO SIMULAÇÃO - Nenhum arquivo será removido")
        print("   Para remover de verdade, use: limpar_tudo(dry_run=False)")

    total_removidos = 0

    # Limpar cada diretório com sua política de retenção
    configuracoes = [
        (TEMP_DIR, RETENCAO_TEMP, "Temporários"),
        (RELATORIOS_DIR, RETENCAO_RELATORIOS, "Relatórios"),
        (TESTES_DIR, RETENCAO_TESTES, "Testes"),
        (LOGS_DIR, RETENCAO_LOGS, "Logs"),
    ]

    for diretorio, dias, nome in configuracoes:
        removidos = limpar_diretorio(diretorio, dias, dry_run)
        total_removidos += removidos

    print("\n" + "=" * 60)
    if dry_run:
        print(f"📊 Total que seria removido: {total_removidos} arquivos")
    else:
        print(f"📊 Total removido: {total_removidos} arquivos")
    print("=" * 60)

    return total_removidos


def salvar_arquivo_temp(nome: str, conteudo: str):
    """Salva um arquivo no diretório temporário."""
    criar_estrutura_diretorios()
    arquivo = TEMP_DIR / nome
    arquivo.write_text(conteudo)
    print(f"✅ Arquivo temp salvo: {arquivo}")
    return arquivo


def salvar_relatorio(nome: str, conteudo: str, prefixo_data: bool = True):
    """
    Salva um relatório com data no nome.

    Args:
        nome: Nome do arquivo
        conteudo: Conteúdo do relatório
        prefixo_data: Se True, adiciona data no início do nome
    """
    criar_estrutura_diretorios()

    if prefixo_data:
        data = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_final = f"{data}_{nome}"
    else:
        nome_final = nome

    arquivo = RELATORIOS_DIR / nome_final
    arquivo.write_text(conteudo)
    print(f"✅ Relatório salvo: {arquivo}")
    return arquivo


def salvar_teste(nome: str, conteudo: str):
    """Salva resultado de teste."""
    criar_estrutura_diretorios()
    data = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = TESTES_DIR / f"{data}_{nome}"
    arquivo.write_text(conteudo)
    print(f"✅ Teste salvo: {arquivo}")
    return arquivo


def status_diretorios():
    """Mostra status de todos os diretórios temporários."""
    print("=" * 60)
    print("📊 STATUS DOS DIRETÓRIOS")
    print("=" * 60)

    configuracoes = [
        (TEMP_DIR, RETENCAO_TEMP, "Temporários"),
        (RELATORIOS_DIR, RETENCAO_RELATORIOS, "Relatórios"),
        (TESTES_DIR, RETENCAO_TESTES, "Testes"),
        (LOGS_DIR, RETENCAO_LOGS, "Logs"),
    ]

    for diretorio, dias, nome in configuracoes:
        if diretorio.exists():
            arquivos = [f for f in diretorio.iterdir() if not f.name.startswith('.')]
            antigos = len(listar_arquivos_antigos(diretorio, dias))
            print(f"\n  📁 {nome} ({diretorio.name}/)")
            print(f"     Total: {len(arquivos)} arquivos")
            print(f"     Para limpar (>{dias} dias): {antigos} arquivos")
        else:
            print(f"\n  📁 {nome}: Diretório não existe")

    print("\n" + "=" * 60)


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    print("\n🔧 Utilitário de Limpeza - Shopify Automation\n")

    # Criar estrutura se não existir
    criar_estrutura_diretorios()

    # Mostrar status atual
    status_diretorios()

    # Simular limpeza (dry_run=True por padrão)
    print("\n")
    limpar_tudo(dry_run=True)

    print("\n💡 Para executar a limpeza real:")
    print("   from src.utils import limpar_tudo")
    print("   limpar_tudo(dry_run=False)")
