# StarWeb Automation 🤖

Automação do cadastro de Part Numbers no sistema StarWeb usando Python + Selenium.

## Funcionalidades

- ✅ Login automático no StarWeb
- ✅ Extração de comandos/parâmetros de um PN base
- ✅ Cadastro em lote (múltiplos PNs de uma vez)
- ✅ Validação: impede cadastro duplicado
- ✅ Retry automático para "PART NUMBER INVÁLIDO"
- ✅ Modo headless (sem abrir janela do Chrome)
- ✅ Mapeamento inteligente de comandos (sem lista hardcoded)
- ✅ Configuração via `config.ini`
- ✅ Logging estruturado (console + arquivo `starweb.log`)
- ✅ Notificação sonora ao finalizar
- ✅ Credenciais seguras via `.env`
- ✅ Ajustes finos de performance para garantir estabilidade em sistemas lentos

## Instalação

```bash
# Clonar repositório
git clone https://github.com/filipecrysthian/starweb-automation.git
cd starweb-automation

# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

## Configuração

### 1. Credenciais (`.env`)

Criar arquivo `.env` na raiz:

```env
STARWEB_USER=seu_usuario
STARWEB_PASS=sua_senha
```

### 2. Part Numbers (`PN_cadastrar.txt`)

```ini
PN_BASE: 1026300007
PN_CADASTRAR: 1026300018
PN_CADASTRAR: 1026300019
PN_CADASTRAR: 1026300020
```

### 3. Configurações opcionais (`config.ini`)

```ini
[starweb]
url_login = http://147.1.0.41/star/acesso
url_scripts = http://147.1.0.41/star/cmdpartnumber
timeout = 30
max_retries = 3
wait_after_login = 5
wait_after_navigate = 3
wait_after_pn_input = 5
delay_between_commands = 4
delay_after_cq = 5

[chrome]
headless = false
```

### 4. Ajuste de Performance (Opcional)

Se você notar que a automação está muito rápida e o StarWeb não está registrando alguns comandos, você pode ajustar a velocidade:
1. Abra o arquivo `config.ini`.
2. Aumente o valor de `delay_between_commands` (ex: de `4` para `5` ou `6`). Isso fará com que o robô aguarde mais tempo entre o envio de cada comando, dando tempo ao banco de dados do StarWeb de salvá-lo.
3. Se quiser mais velocidade, você pode reduzir o valor aos poucos (ex: para `2` ou `3`), contanto que o sistema consiga acompanhar.

## Uso

### Via arquivo (modo padrão)

```bash
python main.py
```

### Via linha de comando (CLI)

```bash
# Um PN
python main.py --base 1026300007 --cadastrar 1026300018

# Múltiplos PNs
python main.py --base 1026300007 --cadastrar 1026300018 1026300019 1026300020

# Modo headless (sem janela)
python main.py --headless

# Combinado
python main.py --base 1026300007 --cadastrar 1026300018 --headless
```

### Via batch file

```bash
main.bat
```

## Estrutura do Projeto

```
starweb-automation/
├── config.ini          # Configurações (URLs, timeouts)
├── config.py           # Leitor de configurações
├── credenciais.py      # Carrega credenciais do .env
├── gerardortxt.py      # Gerador de arquivos txt
├── main.bat            # Script de execução Windows
├── main.py             # Ponto de entrada + CLI (argparse)
├── mensagem.py         # Logger centralizado
├── partnumber.py       # Parser de Part Numbers (lote)
├── starweb.py          # Automação principal
├── PN_cadastrar.txt    # Arquivo de entrada (PNs)
├── requirements.txt    # Dependências Python
├── .env                # Credenciais (não versionado)
├── .gitignore          # Arquivos ignorados pelo git
└── README.md           # Documentação
```

## Logs

A execução gera `starweb.log` com detalhes completos. Verifique em caso de falhas.

## Resumo da Execução

Ao finalizar, o script exibe um resumo:

```
══════════════════════════════════════════════════
RESUMO: 3 PN(s) processados
  ✅ Cadastrados: 2
  ⏭️  Pulados (já existem): 1
  PNs cadastrados: 1026300018, 1026300020
  PNs pulados: 1026300019
══════════════════════════════════════════════════
```
