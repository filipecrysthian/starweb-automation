"""
Módulo principal de automação do StarWeb.

Automatiza o cadastro de Part Numbers no sistema StarWeb,
copiando comandos e parâmetros de um PN base para novos PNs.

Melhorias implementadas:
- Mapeamento de comandos por nome/descrição (sem lista hardcoded)
- Extração de texto imediata (evita StaleElementReference)
- Cadastro em lote (múltiplos PNs)
- Retry automático para elementos stale
- Modo headless (--headless)
- Configuração via config.ini
- Notificação sonora ao finalizar
"""

from functools import wraps
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

from credenciais import USERNAME, SENHA
from mensagem import logger
from config import (
    STARWEB_URL, STARWEB_SCRIPTS_URL,
    DEFAULT_TIMEOUT, MAX_RETRIES_PN,
    WAIT_AFTER_LOGIN, WAIT_AFTER_NAVIGATE, WAIT_AFTER_PN_INPUT,
    DELAY_BETWEEN_COMMANDS, DELAY_AFTER_CQ,
    HEADLESS_DEFAULT,
)

# XPaths utilizados
XPATH_LOGIN_USER = '//*[@id="login-username"]'
XPATH_LOGIN_PASS = '//*[@id="login-password"]'
XPATH_LOGIN_BTN = '//*[@id="login-form"]/button'
XPATH_PN_INPUT = '//*[@id="cmpn_part_number"]'
XPATH_BTN_ASSOCIAR = '//*[@id="btn-associar-cmd"]'
XPATH_MODAL = '//*[@id="exampleModal"]'
XPATH_MODAL_BODY = '//*[@id="exampleModal"]/div/div/div[2]'
XPATH_TABLE_ROWS = '//*[@id="div-table-cmds"]/section/table/tbody/tr'
XPATH_MODAL_TABLE = '//table[contains(@class,"lista-comandos")]'
XPATH_MODAL_CLOSE = '//*[@id="exampleModal"]/div/div/div[3]/button[@data-dismiss="modal"]'
XPATH_BTN_ENVIAR_CQ = '//*[@id="button-send-cq"]//button'


def retry_on_stale(max_retries=3, delay=1):
    """Decorator que retenta a função se ocorrer StaleElementReferenceException."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException:
                    if attempt == max_retries - 1:
                        raise
                    logger.debug(
                        f"Elemento stale em {func.__name__}, "
                        f"tentativa {attempt + 1}/{max_retries}"
                    )
                    sleep(delay)
        return wrapper
    return decorator


class StarWeb:
    """
    Automatiza o cadastro de Part Numbers no sistema StarWeb.

    Fluxo:
        1. Abre o Chrome e acessa o StarWeb
        2. Faz login
        3. Navega para a aba de scripts
        4. Insere o PN base e extrai comandos/parâmetros/descrições
        5. Para cada PN a cadastrar:
           a. Insere o PN e verifica se já está cadastrado
           b. Se não cadastrado, associa os comandos do PN base
        6. Exibe resumo e notifica com som
    """

    def __init__(
        self,
        pn_base: str,
        pn_cadastrar_list: list,
        headless: bool = False,
    ) -> None:
        self.pn_base = pn_base
        self.pn_cadastrar_list = pn_cadastrar_list
        self.headless = headless or HEADLESS_DEFAULT
        self.driver = None
        self.wait = None
        self.dados_base = []  # Lista de dicts: [{comando, descricao, parametro}]

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
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            logger.info("Modo headless ativado")

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

        # Extrair dados do PN base
        self._inserir_pn(self.pn_base)
        self._aguardar_carregamento_tabela()
        self._extrair_dados()
        logger.info(f"Extraídos {len(self.dados_base)} comandos do PN base")

        # Cadastrar cada PN
        resultados = {"sucesso": [], "pulado": [], "falha": []}

        for pn in self.pn_cadastrar_list:
            try:
                self._cadastrar_pn(pn)
                resultados["sucesso"].append(pn)
            except RuntimeError as e:
                logger.warning(str(e))
                resultados["pulado"].append(pn)
            except Exception as e:
                logger.error(f"Erro ao cadastrar PN {pn}: {e}")
                resultados["falha"].append(pn)

        self._exibir_resumo(resultados)
        self._notificar_conclusao(resultados)

    # ── Navegação e Login ──────────────────────────────────────────

    def _acessar_starweb(self) -> None:
        """Navega até a página de login do StarWeb."""
        logger.info("Acessando StarWeb")
        self.driver.get(STARWEB_URL)

        try:
            self.wait.until(
                EC.invisibility_of_element_located((By.ID, "loading-overlay"))
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

        sleep(WAIT_AFTER_LOGIN)
        logger.info("Login realizado com sucesso")

    def _acessar_guia_script(self) -> None:
        """Navega diretamente para a página de Scripts via URL."""
        logger.info("Acessando página de Scripts")
        self.driver.get(STARWEB_SCRIPTS_URL)
        sleep(WAIT_AFTER_NAVIGATE)

        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, XPATH_PN_INPUT))
        )
        logger.debug("Página de Scripts carregada")

    # ── Inserção de Part Number ────────────────────────────────────

    def _inserir_pn(self, pn: str) -> None:
        """Insere um Part Number no campo de entrada."""
        logger.info(f"Inserindo PN: {pn}")
        campo = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, XPATH_PN_INPUT))
        )
        self._limpar_campo(campo)
        campo.clear()
        # Digita o PN com um pequeno delay entre caracteres para maior estabilidade
        for char in pn:
            campo.send_keys(char)
            sleep(0.05)

    def _limpar_campo(self, campo) -> None:
        """Limpa o conteúdo de um campo de input via ActionChains."""
        actions = ActionChains(self.driver)
        actions.double_click(campo).perform()
        actions.key_down(Keys.BACKSPACE).perform()

    def _aguardar_carregamento_tabela(self) -> None:
        """Aguarda a tabela de comandos carregar após inserir o PN."""
        logger.debug("Aguardando carregamento da tabela de comandos")
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, XPATH_TABLE_ROWS))
        )
        logger.debug("Tabela de comandos carregada")

    # ── Extração de Dados do PN Base ───────────────────────────────

    @retry_on_stale(max_retries=3)
    def _extrair_dados(self) -> None:
        """Extrai comandos, descrições e parâmetros da tabela do PN base.

        Salva os textos imediatamente (não WebElements) para evitar
        StaleElementReferenceException caso a página atualize.
        """
        logger.info("Extraindo dados do PN base")
        self.dados_base = []

        linhas = self.driver.find_elements(By.XPATH, XPATH_TABLE_ROWS)
        for i in range(1, len(linhas) + 1):
            cmd = self.driver.find_element(
                By.XPATH, f'{XPATH_TABLE_ROWS}[{i}]/td[2]'
            ).text.strip()

            desc = self.driver.find_element(
                By.XPATH, f'{XPATH_TABLE_ROWS}[{i}]/td[3]'
            ).text.strip()

            param = self.driver.find_element(
                By.XPATH, f'{XPATH_TABLE_ROWS}[{i}]/td[4]/span'
            ).text.strip()

            self.dados_base.append({
                "comando": cmd,
                "descricao": desc,
                "parametro": param,
            })

        logger.debug(
            f"Comandos extraídos: "
            f"{[d['comando'] for d in self.dados_base]}"
        )

    # ── Cadastro de PN ─────────────────────────────────────────────

    def _cadastrar_pn(self, pn: str) -> None:
        """Cadastra um único Part Number."""
        logger.info(f"═══ Processando PN: {pn} ═══")
        self._inserir_pn(pn)
        self._verificar_pn(pn)
        self._digitar_comandos()
        self._enviar_para_aprovacao_cq(pn)
        logger.info(f"PN {pn} cadastrado e enviado para aprovação CQ!")

    def _verificar_pn(self, pn: str) -> None:
        """
        Verifica se o PN já existe e se já possui comandos.

        - 'PART NUMBER não Encontrado' → habilita botão para cadastro
        - 'PART NUMBER INVÁLIDO' → retry (pode ser timing do sistema)
        - PN com comandos existentes → RuntimeError (aborta este PN)
        """
        for tentativa in range(1, MAX_RETRIES_PN + 1):
            sleep(WAIT_AFTER_PN_INPUT)

            try:
                div_cmds = self.driver.find_element(By.ID, "div-table-cmds")
                texto = div_cmds.text
            except Exception:
                logger.debug("div-table-cmds não encontrado")
                return

            texto_lower = texto.lower()

            # PN INVÁLIDO — retry (pode ser problema de timing)
            if "inválido" in texto_lower:
                if tentativa < MAX_RETRIES_PN:
                    logger.warning(
                        f"PART NUMBER INVÁLIDO (tentativa {tentativa}/{MAX_RETRIES_PN}). "
                        "Re-inserindo..."
                    )
                    self._inserir_pn(pn)
                    continue
                else:
                    logger.warning(
                        "PART NUMBER INVÁLIDO após todas as tentativas. "
                        "Habilitando botão para tentar cadastro..."
                    )
                    self._habilitar_botao_associar()
                    return

            # PN não encontrado — novo PN, habilitar cadastro
            if "não encontrado" in texto_lower:
                logger.warning(
                    f"PN {pn} não encontrado no sistema. Registrando novo PN..."
                )
                self._habilitar_botao_associar()
                return

            # PN encontrado — verificar se já tem comandos
            cmds_existentes = self.driver.find_elements(
                By.XPATH, XPATH_TABLE_ROWS
            )
            if cmds_existentes:
                raise RuntimeError(
                    f"PN {pn} já possui {len(cmds_existentes)} comando(s) "
                    "cadastrado(s). Pulando para evitar duplicação."
                )

            logger.info(f"PN {pn} encontrado no sistema (sem comandos)")
            return

    def _habilitar_botao_associar(self) -> None:
        """Habilita o botão 'Associar Comandos' via JavaScript."""
        self.driver.execute_script(
            'document.getElementById("btn-associar-cmd")'
            '.removeAttribute("disabled");'
        )
        logger.info("Botão 'Associar Comandos' habilitado")

    # ── Inserção de Comandos via Modal ─────────────────────────────

    @retry_on_stale(max_retries=3)
    def _digitar_comandos(self) -> None:
        """Associa os comandos extraídos ao PN via modal."""
        logger.info("Inserindo comandos no novo PN")
        self._abrir_modal_associar()

        for idx, dados in enumerate(self.dados_base, 1):
            cmd = dados["comando"]
            desc = dados["descricao"]
            param = dados["parametro"]
            logger.debug(f"Processando comando {idx}/{len(self.dados_base)}: {cmd}")

            # Encontrar a linha do comando no modal por nome (e descrição se duplicado)
            target_row = self._encontrar_comando_no_modal(cmd, desc)
            if not target_row:
                logger.warning(f"Comando '{cmd}' não encontrado no modal. Pulando.")
                continue

            # Preencher parâmetro se necessário
            if param:
                try:
                    param_input = target_row.find_element(
                        By.XPATH, 'td[3]/input'
                    )
                    if param_input.is_enabled():
                        param_input.clear()
                        sleep(0.5)  # Pequeno delay antes de inserir o parâmetro
                        param_input.send_keys(param)
                        sleep(0.5)  # Pequeno delay após inserir o parâmetro
                except Exception:
                    logger.debug(f"Campo de parâmetro não disponível para {cmd}")

            # Clicar no botão de adicionar (+)
            btn_add = target_row.find_element(By.XPATH, 'td[4]/button')
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn_add
            )
            sleep(0.5)
            btn_add.click()
            sleep(DELAY_BETWEEN_COMMANDS)

        logger.info("Todos os comandos inseridos com sucesso")
        self._fechar_modal()

    def _encontrar_comando_no_modal(self, cmd: str, desc: str):
        """
        Encontra a linha do comando no modal por nome e descrição.

        Usa XPath direto na tabela do modal em vez de lista hardcoded.
        Para comandos duplicados (ex: cmdFIM), usa a descrição para
        desambiguação.

        Returns:
            WebElement da linha (tr) ou None se não encontrado.
        """
        # Buscar todas as linhas com o nome do comando
        xpath = (
            f'{XPATH_MODAL_TABLE}//tbody/tr'
            f'[td[1][normalize-space()="{cmd}"]]'
        )
        rows = self.driver.find_elements(By.XPATH, xpath)

        if not rows:
            return None

        if len(rows) == 1:
            return rows[0]

        # Múltiplas linhas — desambiguar pela descrição
        for row in rows:
            try:
                row_desc = row.find_element(By.XPATH, 'td[2]').text.strip()
                if row_desc == desc:
                    return row
            except Exception:
                continue

        # Fallback: retornar a primeira linha
        logger.warning(
            f"Múltiplas versões de '{cmd}' encontradas, usando a primeira"
        )
        return rows[0]

    def _abrir_modal_associar(self) -> None:
        """Abre o modal de associação de comandos."""
        botao = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, XPATH_BTN_ASSOCIAR))
        )
        botao.click()

        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, XPATH_MODAL_BODY))
        )
        sleep(1)
        logger.debug("Modal de associação aberto")

    def _fechar_modal(self) -> None:
        """Fecha o modal de associação."""
        try:
            btn_close = self.driver.find_element(By.XPATH, XPATH_MODAL_CLOSE)
            btn_close.click()
            self.wait.until(
                EC.invisibility_of_element_located((By.XPATH, XPATH_MODAL))
            )
            sleep(1)
            logger.debug("Modal fechado")
        except Exception:
            logger.debug("Modal já estava fechado ou não encontrado")

    def _enviar_para_aprovacao_cq(self, pn: str) -> None:
        """Clica no botão 'Enviar para aprovação CQ' após associar comandos.

        O botão é gerado dinamicamente pelo JavaScript da página
        dentro da div#button-send-cq após os comandos serem associados.
        """
        logger.info(f"Enviando PN {pn} para aprovação CQ...")
        try:
            btn_cq = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, XPATH_BTN_ENVIAR_CQ))
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn_cq
            )
            sleep(1)
            btn_cq.click()

            # Aguarda o feedback de envio (barra de progresso)
            sleep(DELAY_AFTER_CQ)
            logger.info(f"PN {pn} enviado para aprovação CQ com sucesso!")
        except Exception as e:
            logger.warning(f"Não foi possível enviar para aprovação CQ: {e}")

    def _exibir_resumo(self, resultados: dict) -> None:
        """Exibe resumo do cadastro em lote."""
        total = len(self.pn_cadastrar_list)
        sucesso = len(resultados["sucesso"])
        pulado = len(resultados["pulado"])
        falha = len(resultados["falha"])

        logger.info("═" * 50)
        logger.info(f"RESUMO: {total} PN(s) processados")
        logger.info(f"  ✅ Cadastrados: {sucesso}")
        if pulado:
            logger.info(f"  ⏭️  Pulados (já existem): {pulado}")
        if falha:
            logger.info(f"  ❌ Falhas: {falha}")

        if resultados["sucesso"]:
            logger.info(f"  PNs cadastrados: {', '.join(resultados['sucesso'])}")
        if resultados["pulado"]:
            logger.info(f"  PNs pulados: {', '.join(resultados['pulado'])}")
        if resultados["falha"]:
            logger.info(f"  PNs com falha: {', '.join(resultados['falha'])}")
        logger.info("═" * 50)

    @staticmethod
    def _notificar_conclusao(resultados: dict) -> None:
        """Emite notificação sonora ao finalizar."""
        try:
            import winsound
            if resultados["falha"]:
                # Bipe de erro
                winsound.MessageBeep(winsound.MB_ICONHAND)
            else:
                # Bipe de sucesso
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except ImportError:
            pass  # winsound só existe no Windows

    def _fechar_navegador(self) -> None:
        """Fecha o navegador de forma segura."""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("Navegador fechado")
            except Exception:
                logger.warning("Erro ao fechar o navegador (pode já estar fechado)")