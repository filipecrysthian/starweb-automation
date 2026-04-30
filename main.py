"""
StarWeb Automation — Entry Point

Automatiza o cadastro de Part Numbers no sistema StarWeb.
Lê o PN base e PN a cadastrar do arquivo PN_cadastrar.txt.
"""

import os
import sys

from gerardortxt import Gerador
from mensagem import logger

# Diretório base do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PN_FILE = os.path.join(BASE_DIR, "PN_cadastrar.txt")


def main():
    """Ponto de entrada principal da automação."""

    # Verificar se o arquivo de Part Numbers existe
    if not os.path.isfile(PN_FILE):
        Gerador("PN_cadastrar.txt", corpo="PN_BASE: \nPN_CADASTRAR: ")
        Gerador.criar_txt()
        logger.error(
            "Arquivo PN_cadastrar.txt criado. "
            "Insira os Part Numbers antes de continuar."
        )
        sys.exit(1)

    # Importação tardia para evitar abrir o Chrome antes de validar o arquivo
    from starweb import StarWeb

    try:
        StarWeb()
    except Exception as e:
        logger.error(f"Falha na execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
