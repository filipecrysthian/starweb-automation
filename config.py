"""
Módulo de configuração — lê valores do config.ini.

Todas as constantes de configuração do projeto são centralizadas aqui.
Se o config.ini não existir, valores padrão são usados.
"""

import os
import configparser

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_FILE = os.path.join(_BASE_DIR, "config.ini")

_config = configparser.ConfigParser()
_config.read(_CONFIG_FILE, encoding="utf-8")

# StarWeb
STARWEB_URL = _config.get("starweb", "url_login", fallback="http://147.1.0.41/star/acesso")
STARWEB_SCRIPTS_URL = _config.get("starweb", "url_scripts", fallback="http://147.1.0.41/star/cmdpartnumber")
DEFAULT_TIMEOUT = _config.getint("starweb", "timeout", fallback=30)
MAX_RETRIES_PN = _config.getint("starweb", "max_retries", fallback=3)
WAIT_AFTER_LOGIN = _config.getint("starweb", "wait_after_login", fallback=5)
WAIT_AFTER_NAVIGATE = _config.getint("starweb", "wait_after_navigate", fallback=3)
WAIT_AFTER_PN_INPUT = _config.getint("starweb", "wait_after_pn_input", fallback=5)

# Chrome
HEADLESS_DEFAULT = _config.getboolean("chrome", "headless", fallback=False)
