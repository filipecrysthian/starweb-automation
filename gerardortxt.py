"""
Módulo gerador de arquivos de texto.

Utilizado para criar o arquivo PN_cadastrar.txt quando ele não existe.
"""

import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Gerador:
    """Cria arquivos de texto no diretório do projeto."""

    def __init__(self, nome: str, corpo: str) -> None:
        self.caminho = os.path.join(_BASE_DIR, nome)
        self.corpo = corpo

    def criar_txt(self) -> None:
        """Escreve o conteúdo no arquivo."""
        with open(self.caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(self.corpo)