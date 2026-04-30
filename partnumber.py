"""
Módulo para leitura de Part Numbers do arquivo PN_cadastrar.txt.

Formato esperado do arquivo:
    PN_BASE: 1234567890
    PN_CADASTRAR: 0987654321
"""

import os

# Diretório onde este script está localizado (caminho relativo seguro)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PN_FILE = os.path.join(_BASE_DIR, "PN_cadastrar.txt")


class PartNumber:
    """Lê e fornece o PN base e PN a cadastrar."""

    def __init__(self, filepath: str = _PN_FILE) -> None:
        self.filepath = filepath
        self._dados = self._extrair_partnumbers()

    def _extrair_partnumbers(self) -> dict:
        """Extrai os part numbers do arquivo e retorna como dicionário."""
        dados = {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as arquivo:
                for linha in arquivo:
                    if ":" in linha:
                        chave, valor = linha.split(":", 1)
                        dados[chave.strip()] = valor.strip()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Arquivo '{self.filepath}' não encontrado. "
                "Crie o arquivo com PN_BASE e PN_CADASTRAR."
            )
        return dados

    def pn_base(self) -> str:
        """Retorna o Part Number base."""
        return self._dados.get("PN_BASE", "")

    def pn_cadastrar(self) -> str:
        """Retorna o Part Number a ser cadastrado."""
        return self._dados.get("PN_CADASTRAR", "")
