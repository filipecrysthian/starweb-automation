"""
Módulo de credenciais — carrega variáveis de ambiente do arquivo .env

Nunca armazene credenciais diretamente no código-fonte.
Crie um arquivo .env na raiz do projeto com:
    STARWEB_USERNAME=seu_usuario
    STARWEB_SENHA=sua_senha
"""

import os
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("STARWEB_USERNAME", "")
SENHA = os.getenv("STARWEB_SENHA", "")

if not USERNAME or not SENHA:
    raise EnvironmentError(
        "Credenciais não configuradas. Crie um arquivo .env com "
        "STARWEB_USERNAME e STARWEB_SENHA."
    )