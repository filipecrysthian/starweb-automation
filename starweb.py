"""
Módulo principal de automação do StarWeb.

Automatiza o cadastro de Part Numbers no sistema StarWeb,
copiando comandos e parâmetros de um PN base para um novo PN.

Consolidação das versões v1 e v2, com melhorias de:
- Esperas explícitas (WebDriverWait) em vez de sleep fixo
- Tratamento de erros com cleanup do navegador
- Logging estruturado
- Selenium Manager nativo para gestão automática do chromedriver
- Driver inicializado no __init__ (não como atributo de classe)
"""

from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pandas import DataFrame

from partnumber import PartNumber
from credenciais import USERNAME, SENHA
from mensagem import logger


# Lista de todos os comandos disponíveis no StarWeb, na ordem em que
# aparecem na tabela do modal de associação. Essa ordem é usada para
# mapear cada comando ao seu índice (linha) na tabela.
#
# NOTA: Existem duplicatas intencionais (cmdFIM 3x, cmdOWMEM 2x,
# cmdTeste3 2x) que refletem a estrutura real da tabela no sistema.
# O método list.index() retorna SEMPRE o primeiro índice encontrado,
# o que pode causar problemas se o PN base contiver um dos comandos
# duplicados. TODO: investigar se o sistema realmente usa duplicatas.
ALL_COMMANDS = [
    "cmdASK", "cmdBAT", "cmdBIO", "cmdBLG", "cmdBTH", "cmdBTM", "cmdBTW",
    "cmdCAM", "cmdCAR", "cmdCMI", "cmdCMOS", "cmdDLY", "cmdDMY", "cmdEAB",
    "cmdFAN", "cmdFID", "cmdFIM", "cmdFIM", "cmdFIM", "cmdFLASHMAC",
    "cmdLAE", "cmdLAN", "cmdLAX", "cmdLDX", "cmdLED", "cmdLID", "cmdLME",
    "cmdLPB", "cmdMAC", "cmdMC2", "cmdMC3", "cmdMEM", "cmdMGG", "cmdMIC",
    "cmdMSG", "cmdMVM", "cmdOWBIOS", "cmdOWMAC2", "cmdOWMAC4", "cmdOWMEM",
    "cmdOWMEM", "cmdOWUSB", "cmdPCI", "cmdPRC", "cmdREDE", "cmdROT",
    "cmdRPM", "cmdRW1", "cmdRW3", "cmdSATA", "cmdSIM", "cmdSMD", "cmdSND",
    "cmdSNV", "cmdSVI", "cmdSXP", "cmdTBL", "cmdTBM", "cmdTBS", "cmdTBT",
    "cmdTEC", "cmdTERMAL", "cmdTeste", "cmdTeste1", "cmdTeste2", "cmdTeste3",
    "cmdTeste3", "cmdTeste5", "cmdTFX", "cmdTKB", "cmdTMI", "cmdTPD",
    "cmdTSR", "cmdTTP", "cmdTWL", "cmdTXI", "cmdU2X", "cmdU3X", "cmdUCT",
    "cmdUID", "cmdUII", "cmdUIW", "cmdUSB", "cmdUST", "cmdUSW", "cmdVGA",
    "cmdVID", "cmdWAN", "cmdWAV", "cmdWIT", "cmdX1", "cmdX16", "cmdYOG",
]

# Timeout padrão para esperas explícitas (em segundos)
DEFAULT_TIMEOUT = 30

# Número máximo de tentativas para inserir o PN cadastrar
MAX_RETRIES_PN = 3

# XPaths utilizados
XPATH_LOGIN_USER = '//*[@id="login-username"]'
XPATH_LOGIN_PASS = '//*[@id="login-password"]'
XPATH_LOGIN_BTN = '//*[@id="login-form"]/button'
XPATH_PN_INPUT = '//*[@id="cmpn_part_number"]'
XPATH_BTN_ASSOCIAR = '//*[@id="btn-associar-cmd"]'
XPATH_MODAL_BODY = '//*[@id="exampleModal"]/div/div/div[2]'
XPATH_MODAL_CMD_INPUT = '//*[@id="exampleModal"]/div/div/div[2]/form/div/div/input'
XPATH_TABLE_ROWS = '//*[@id="div-table-cmds"]/section/table/tbody/tr'
XPATH_LOADING_OVERLAY = "loading-overlay"

STARWEB_URL = "http://147.1.0.41/star/acesso"
STARWEB_SCRIPTS_URL = "http://147.1.0.41/star/cmdpartnumber"


class StarWeb:
    """
    Automatiza o cadastro de Part Numbers no sistema StarWeb.

    Fluxo:
        1. Abre o Chrome e acessa o StarWeb
        2. Faz login
        3. Navega para a aba de scripts
        4. Insere o PN base e extrai comandos/parâmetros
        5. Insere o PN a cadastrar e replica os comandos
    """

    def __init__(self) -> None:
        self.driver = None
        self.wait = None
        self.lista_comandos = []
        self.lista_parametros = []
        self.df = None

        try:
            self._inicializar_driver()
            self._executar_fluxo()
        except Exception as e:
            logger.error(f"Erro durante a automação: {e}")
            raise
        finally:
            self._fechar_navegador()

    def _inicializar_driver(self) -> None:
        """Inicializa o Chrome WebDriver com detecção automática do chromedriver."""
        logger.info("Inicializando navegador Chrome")
        options = Options()
        # Desabilitar logs excessivos do Chrome
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # Selenium 4.6+ detecta a versão do Chrome e baixa
        # o chromedriver compatível automaticamente (Selenium Manager)
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, DEFAULT_TIMEOUT)
        logger.debug("WebDriver inicializado com sucesso")

    def _executar_fluxo(self) -> None:
        """Executa o fluxo completo de automação."""
        self._acessar_starweb()
        self._login()
        self._acessar_guia_script()
        self._inserir_pn_base()
        self._aguardar_carregamento_tabela()
        self._extrair_dados()
        self.df = DataFrame(self._tratar_dados())
        logger.info(f"Extraídos {len(self.df)} comandos do PN base")
        self._inserir_pn_cadastrar()
        self._verificar_pn_cadastrar()
        self._digitar_comandos()
        logger.info("Tarefa concluída com sucesso!")

    def _acessar_starweb(self) -> None:
        """Navega até a página de login do StarWeb."""
        logger.info("Acessando StarWeb")
        self.driver.get(STARWEB_URL)

        # Se houver overlay/spinner de carregamento, espera sumir
        try:
            self.wait.until(
                EC.invisibility_of_element_located((By.ID, XPATH_LOADING_OVERLAY))
            )
        except Exception:
            logger.debug("Nenhum overlay de carregamento detectado")

    def _login(self) -> None:
        """Realiza o login no sistema StarWeb."""
        logger.info("Fazendo login")

        campo_usuario = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, XPATH_LOGIN_USER))
        )
        campo_usuario.send_keys(USERNAME)

        campo_senha = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, XPATH_LOGIN_PASS))
        )
        campo_senha.send_keys(SENHA)

        botao_login = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, XPATH_LOGIN_BTN))
        )
        botao_login.click()

        # Aguarda o login ser processado e a página redirecionar
        sleep(5)
        logger.info("Login realizado com sucesso")

    def _acessar_guia_script(self) -> None:
        """Navega diretamente para a página de Scripts via URL."""
        logger.info("Acessando página de Scripts")
        self.driver.get(STARWEB_SCRIPTS_URL)
        sleep(3)

        # Aguarda o campo de Part Number estar visível (página carregada)
        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, XPATH_PN_INPUT))
        )
        logger.debug("Página de Scripts carregada")

    def _inserir_pn_base(self) -> None:
        """Insere o Part Number base para extração dos comandos."""
        partnumber = PartNumber()
        pn_base = partnumber.pn_base()
        logger.info(f"Inserindo PN base: {pn_base}")

        campo = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, XPATH_PN_INPUT))
        )
        campo.clear()
        campo.send_keys(pn_base)

    def _aguardar_carregamento_tabela(self) -> None:
        """Aguarda a tabela de comandos carregar após inserir o PN."""
        logger.debug("Aguardando carregamento da tabela de comandos")
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, XPATH_TABLE_ROWS))
        )
        logger.debug("Tabela de comandos carregada")

    def _inserir_pn_cadastrar(self) -> None:
        """Insere o Part Number a ser cadastrado."""
        partnumber = PartNumber()
        pn_cadastrar = partnumber.pn_cadastrar()
        logger.info(f"Inserindo PN para cadastro: {pn_cadastrar}")

        campo = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, XPATH_PN_INPUT))
        )
        self._limpar_campo(campo)
        campo.clear()
        campo.send_keys(pn_cadastrar)

    def _verificar_pn_cadastrar(self) -> None:
        """
        Verifica se o PN cadastrar já existe no sistema.

        Detecta as mensagens:
        - 'PART NUMBER não Encontrado' — PN não existe, precisa registrar
        - 'PART NUMBER INVÁLIDO' — sistema ainda processando ou PN inválido

        Se o PN já existir E já tiver comandos associados, aborta a execução
        para evitar cadastro duplicado.
        """
        for tentativa in range(1, MAX_RETRIES_PN + 1):
            # Aguarda a resposta AJAX da página após inserir o PN
            sleep(5)

            try:
                div_cmds = self.driver.find_element(By.ID, "div-table-cmds")
                texto = div_cmds.text
            except Exception:
                logger.debug("div-table-cmds não encontrado, assumindo PN existente")
                return

            texto_lower = texto.lower()
            pn_nao_encontrado = "não encontrado" in texto_lower
            pn_invalido = "inválido" in texto_lower

            if pn_invalido:
                if tentativa < MAX_RETRIES_PN:
                    logger.warning(
                        f"PART NUMBER INVÁLIDO (tentativa {tentativa}/{MAX_RETRIES_PN}). "
                        "Re-inserindo PN..."
                    )
                    # Re-inserir o PN (pode ser problema de timing do sistema)
                    campo = self.wait.until(
                        EC.visibility_of_element_located((By.XPATH, XPATH_PN_INPUT))
                    )
                    self._limpar_campo(campo)
                    campo.clear()
                    partnumber = PartNumber()
                    campo.send_keys(partnumber.pn_cadastrar())
                    continue
                else:
                    logger.warning(
                        "PART NUMBER INVÁLIDO após todas as tentativas. "
                        "Habilitando botão para tentar cadastro..."
                    )
                    self._habilitar_botao_associar()
                    return

            if pn_nao_encontrado:
                logger.warning(
                    "PART NUMBER não encontrado no sistema. Registrando novo PN..."
                )
                self._habilitar_botao_associar()
                return

            # PN encontrado — verificar se já tem comandos associados
            cmds_existentes = self.driver.find_elements(By.XPATH, XPATH_TABLE_ROWS)
            if cmds_existentes:
                pn = PartNumber().pn_cadastrar()
                raise RuntimeError(
                    f"PART NUMBER {pn} já possui {len(cmds_existentes)} comando(s) "
                    "cadastrado(s). Abortando para evitar duplicação."
                )

            logger.info("PART NUMBER encontrado no sistema (sem comandos)")
            return

    def _habilitar_botao_associar(self) -> None:
        """Habilita o botão 'Associar Comandos' via JavaScript."""
        self.driver.execute_script(
            'document.getElementById("btn-associar-cmd")'
            '.removeAttribute("disabled");'
        )
        logger.info("Botão 'Associar Comandos' habilitado para novo PN")

    def _limpar_campo(self, campo) -> None:
        """Limpa o conteúdo de um campo de input via ActionChains."""
        actions = ActionChains(self.driver)
        actions.double_click(campo).perform()
        actions.key_down(Keys.BACKSPACE).perform()

    def _extrair_dados(self) -> None:
        """Extrai comandos e parâmetros da tabela do PN base."""
        logger.info("Extraindo dados do PN base")
        self._extrair_comandos()
        self._extrair_parametros()

    def _extrair_comandos(self) -> None:
        """Extrai os nomes dos comandos da tabela."""
        linhas = self.driver.find_elements(By.XPATH, XPATH_TABLE_ROWS)
        for i in range(1, len(linhas) + 1):
            elemento = self.driver.find_element(
                By.XPATH, f'{XPATH_TABLE_ROWS}[{i}]/td[2]'
            )
            self.lista_comandos.append(elemento)

    def _extrair_parametros(self) -> None:
        """Extrai os parâmetros dos comandos da tabela."""
        linhas = self.driver.find_elements(By.XPATH, XPATH_TABLE_ROWS)
        for i in range(1, len(linhas) + 1):
            elemento = self.driver.find_element(
                By.XPATH, f'{XPATH_TABLE_ROWS}[{i}]/td[4]/span'
            )
            self.lista_parametros.append(elemento)

    def _tratar_dados(self) -> dict:
        """Converte os WebElements extraídos em um dicionário de dados."""
        return {
            "comando": [cmd.text for cmd in self.lista_comandos],
            "parametro": [param.text for param in self.lista_parametros],
        }

    def _digitar_comandos(self) -> None:
        """Associa os comandos extraídos ao novo PN via modal."""
        logger.info("Inserindo comandos no novo PN")
        self._abrir_modal_associar()

        for i in range(len(self.df)):
            cmd = self.df.loc[i, "comando"]
            param = self.df.loc[i, "parametro"]
            logger.debug(f"Processando comando {i + 1}/{len(self.df)}: {cmd}")

            # Digitar o nome do comando no campo de busca
            input_cmd = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, XPATH_MODAL_CMD_INPUT))
            )
            input_cmd.clear()
            input_cmd.send_keys(cmd)

            # Encontrar o índice do comando na tabela do modal
            indice_cmd = ALL_COMMANDS.index(cmd) + 1

            # Se tem parâmetro, preenchê-lo
            if param:
                xpath_param = (
                    f'{XPATH_MODAL_BODY}/table/tbody/tr[{indice_cmd}]/td[3]/input'
                )
                input_param = self.wait.until(
                    EC.visibility_of_element_located((By.XPATH, xpath_param))
                )
                input_param.clear()
                input_param.send_keys(param)

            # Clicar no botão de adicionar
            xpath_btn = (
                f'{XPATH_MODAL_BODY}/table/tbody/tr[{indice_cmd}]/td[4]/button'
            )
            btn_add = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath_btn))
            )
            btn_add.click()

        logger.info("Todos os comandos inseridos com sucesso")

    def _abrir_modal_associar(self) -> None:
        """Abre o modal de associação de comandos."""
        botao = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, XPATH_BTN_ASSOCIAR))
        )
        botao.click()

        # Espera modal abrir completamente
        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, XPATH_MODAL_BODY))
        )
        logger.debug("Modal de associação aberto")

    def _fechar_navegador(self) -> None:
        """Fecha o navegador de forma segura."""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("Navegador fechado")
            except Exception:
                logger.warning("Erro ao fechar o navegador (pode já estar fechado)")