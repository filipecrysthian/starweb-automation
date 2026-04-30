"""
StarWeb Automation — Entry Point

Automatiza o cadastro de Part Numbers no sistema StarWeb.
Suporta argumentos via CLI ou leitura do arquivo PN_cadastrar.txt.

Uso:
    python main.py                                        # Lê do arquivo
    python main.py --base 123 --cadastrar 456 789         # Via CLI
    python main.py --headless                             # Sem janela
    python main.py --base 123 --cadastrar 456 --headless  # Combinado
"""

import os
import sys
import argparse

from gerardortxt import Gerador
from partnumber import PartNumber
from mensagem import logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PN_FILE = os.path.join(BASE_DIR, "PN_cadastrar.txt")


def parse_args():
    """Processa argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="StarWeb Automation — Cadastro de Part Numbers"
    )
    parser.add_argument(
        "--base", type=str, help="Part Number base (origem dos comandos)"
    )
    parser.add_argument(
        "--cadastrar", nargs="+", type=str,
        help="Part Number(s) a cadastrar (um ou mais)"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Executar sem abrir janela do Chrome"
    )
    return parser.parse_args()


def main():
    """Ponto de entrada principal da automação."""
    args = parse_args()

    # Determinar PNs: CLI tem prioridade sobre arquivo
    if args.base and args.cadastrar:
        pn_base = args.base
        pn_cadastrar_list = args.cadastrar
        logger.info(f"PNs recebidos via CLI: base={pn_base}, cadastrar={pn_cadastrar_list}")
    else:
        # Ler do arquivo PN_cadastrar.txt
        if not os.path.isfile(PN_FILE):
            gerador = Gerador("PN_cadastrar.txt", corpo="PN_BASE: \nPN_CADASTRAR: ")
            gerador.criar_txt()
            logger.error(
                "Arquivo PN_cadastrar.txt criado. "
                "Insira os Part Numbers antes de continuar."
            )
            sys.exit(1)

        pn = PartNumber()
        pn_base = pn.pn_base()
        pn_cadastrar_list = pn.pn_cadastrar_lista()

        if not pn_base or not pn_cadastrar_list:
            logger.error("PN_BASE ou PN_CADASTRAR não preenchidos no arquivo.")
            sys.exit(1)

    logger.info(
        f"Base: {pn_base} | Cadastrar: {len(pn_cadastrar_list)} PN(s): "
        f"{', '.join(pn_cadastrar_list)}"
    )

    # Importação tardia para evitar abrir o Chrome antes de validar
    from starweb import StarWeb

    try:
        StarWeb(
            pn_base=pn_base,
            pn_cadastrar_list=pn_cadastrar_list,
            headless=args.headless,
        )
    except Exception as e:
        logger.error(f"Falha na execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
