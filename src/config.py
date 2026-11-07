"""Configuração da conexão com o Oracle a partir de variáveis de ambiente.

Variáveis usadas (os mesmos nomes já utilizados por ia/ia_agentes.py):
    ORACLE_USER      usuário do schema da aplicação
    ORACLE_PASSWORD  senha (nunca deve ir para o repositório)
    ORACLE_DSN       HOST:PORTA/NOME_DO_SERVICO
    ORACLE_TIMEOUT   (opcional) segundos de espera para conectar; padrão 10

Podem ser definidas no terminal ($env:ORACLE_USER = "...") ou em um arquivo
.env na raiz do projeto (veja .env.example). Variáveis já definidas no
terminal têm prioridade sobre o .env.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_ENV = RAIZ / ".env"
VARIAVEIS_OBRIGATORIAS = ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
TIMEOUT_PADRAO_S = 10


class ErroConfiguracao(Exception):
    """Variáveis de ambiente ausentes ou inválidas."""


@dataclass(frozen=True)
class ConfigOracle:
    """Parâmetros de conexão. A senha não aparece em repr()/print()."""

    usuario: str
    senha: str = field(repr=False)
    dsn: str
    timeout_s: int = TIMEOUT_PADRAO_S

    def parametros(self):
        """Argumentos para oracledb.connect()."""
        return {
            "user": self.usuario,
            "password": self.senha,
            "dsn": self.dsn,
            "tcp_connect_timeout": float(self.timeout_s),
        }


def _interpretar_linha(linha):
    """Converte 'CHAVE=valor' em (chave, valor); devolve None se não for atribuição."""
    linha = linha.strip()
    if not linha or linha.startswith("#") or "=" not in linha:
        return None
    if linha.startswith("export "):
        linha = linha[len("export "):]
    chave, _, valor = linha.partition("=")
    chave, valor = chave.strip(), valor.strip()
    # Aspas opcionais ao redor do valor (úteis se a senha tiver # ou espaços).
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        valor = valor[1:-1]
    return (chave, valor) if chave else None


def carregar_env(caminho=None):
    """Carrega o arquivo .env para os.environ, sem sobrescrever o que já existe.

    Retorna quantas variáveis foram carregadas. Se o arquivo não existir,
    não é erro: as variáveis podem vir direto do terminal.
    """
    caminho = Path(caminho) if caminho else ARQUIVO_ENV
    if not caminho.is_file():
        return 0
    try:
        texto = caminho.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise ErroConfiguracao(f"Não foi possível ler {caminho.name}: {exc}") from exc
    carregadas = 0
    for linha in texto.splitlines():
        par = _interpretar_linha(linha)
        if par and not os.environ.get(par[0]):
            os.environ[par[0]] = par[1]
            carregadas += 1
    return carregadas


def obter_config():
    """Monta a ConfigOracle validando as variáveis de ambiente."""
    carregar_env()
    ausentes = [v for v in VARIAVEIS_OBRIGATORIAS if not os.environ.get(v, "").strip()]
    if ausentes:
        raise ErroConfiguracao(
            "Variáveis de ambiente ausentes: " + ", ".join(ausentes)
            + ". Defina-as no terminal ou copie .env.example para .env."
        )
    bruto = os.environ.get("ORACLE_TIMEOUT", "").strip()
    try:
        timeout = int(bruto) if bruto else TIMEOUT_PADRAO_S
        if timeout <= 0:
            raise ValueError
    except ValueError:
        raise ErroConfiguracao("ORACLE_TIMEOUT deve ser um inteiro positivo (segundos).") from None
    return ConfigOracle(
        usuario=os.environ["ORACLE_USER"].strip(),
        senha=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"].strip(),
        timeout_s=timeout,
    )
