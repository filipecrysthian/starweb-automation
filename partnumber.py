"""
Módulo para leitura de Part Numbers do arquivo PN_cadastrar.txt.

Formato esperado do arquivo (suporta múltiplos PNs para cadastro):
    PN_BASE: 1234567890
    PN_CADASTRAR: 0987654321
    PN_CADASTRAR: 0987654322
    PN_CADASTRAR: 0987654323
"""

import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PN_FILE = os.path.join(_BASE_DIR, "PN_cadastrar.txt")


class PartNumber:
    """Lê e fornece o PN base e lista de PNs a cadastrar."""

    def __init__(self, filepath: str = _PN_FILE) -> None:
        self.filepath = filepath
        self._pn_base = ""
        self._pn_cadastrar_list = []
        self._extrair_partnumbers()

    def _extrair_partnumbers(self) -> None:
        """Extrai os part numbers do arquivo."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as arquivo:
                for linha in arquivo:
                    if ":" in linha:
                        chave, valor = linha.split(":", 1)
                        chave = chave.strip().upper()
                        valor = valor.strip()
                        if not valor:
                            continue
                        if chave == "PN_BASE":
                            self._pn_base = valor
                        elif chave == "PN_CADASTRAR":
                            self._pn_cadastrar_list.append(valor)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Arquivo '{self.filepath}' não encontrado. "
                "Crie o arquivo com PN_BASE e PN_CADASTRAR."
            )

    def pn_base(self) -> str:
        """Retorna o Part Number base."""
        return self._pn_base

    def pn_cadastrar(self) -> str:
        """Retorna o primeiro Part Number a ser cadastrado (backward compatible)."""
        return self._pn_cadastrar_list[0] if self._pn_cadastrar_list else ""

    def pn_cadastrar_lista(self) -> list:
        """Retorna a lista de todos os Part Numbers a cadastrar."""
        return self._pn_cadastrar_list.copy()
