"""
Módulo de logging colorido para o starweb-automation.

Substitui os prints coloridos por logging estruturado, mantendo
a saída colorida no console e adicionando log em arquivo.
"""

import logging
import sys
from colorama import Fore, Style, init as colorama_init

# Inicializa colorama (necessário no Windows)
colorama_init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Formatter que aplica cores baseado no nível do log."""

    LEVEL_COLORS = {
        logging.DEBUG:    Fore.WHITE,
        logging.INFO:     Fore.CYAN,
        logging.WARNING:  Fore.YELLOW,
        logging.ERROR:    Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
        timestamp = self.formatTime(record, "%H:%M:%S")
        message = record.getMessage()
        return f"{color}[{timestamp}] >>> {message}{Style.RESET_ALL}"


def setup_logger(name: str = "starweb", log_file: str = "starweb.log") -> logging.Logger:
    """Configura e retorna o logger padrão do projeto."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Handler para console (colorido)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # Handler para arquivo (com timestamp completo)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)

    return logger


# Logger padrão do projeto
logger = setup_logger()
