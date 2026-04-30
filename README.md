# StarWeb Automation 🤖

Automação do cadastro de Part Numbers no sistema **StarWeb** via Selenium.

## O que faz?

Copia os comandos e parâmetros de um **Part Number base** (já cadastrado) para um **novo Part Number**, eliminando o trabalho manual de cadastro repetitivo.

## Pré-requisitos

- **Python 3.10+** instalado
- **Google Chrome** instalado (o ChromeDriver é gerenciado automaticamente)

## Instalação

```bash
# Clonar ou copiar o projeto
git clone <url-do-repositorio>
cd starweb-automation

# Criar ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

## Configuração

### 1. Credenciais

Crie um arquivo `.env` na raiz do projeto:

```ini
STARWEB_USERNAME=seu_usuario
STARWEB_SENHA=sua_senha
```

> ⚠️ **Nunca versione o arquivo `.env`** — ele já está no `.gitignore`.

### 2. Part Numbers

Edite o arquivo `PN_cadastrar.txt`:

```
PN_BASE: 1026500002
PN_CADASTRAR: 1026500004
```

- **PN_BASE**: Part Number existente cujos comandos serão copiados.
- **PN_CADASTRAR**: Novo Part Number que receberá os comandos.

## Uso

```bash
# Via Python
python main.py

# Ou via batch file
main.bat
```

O script irá:
1. ✅ Abrir o Chrome e acessar o StarWeb
2. ✅ Fazer login automaticamente
3. ✅ Carregar os comandos do PN base
4. ✅ Cadastrar os comandos no novo PN
5. ✅ Fechar o navegador ao finalizar

## Estrutura do Projeto

```
starweb-automation/
├── main.py           # Ponto de entrada
├── main.bat          # Atalho para execução via terminal
├── starweb.py        # Classe de automação (Selenium)
├── partnumber.py     # Leitura dos Part Numbers do arquivo .txt
├── credenciais.py    # Carrega credenciais do .env
├── mensagem.py       # Logging colorido (console + arquivo)
├── gerardortxt.py    # Gerador de arquivos de texto
├── PN_cadastrar.txt  # Arquivo de entrada (PN base e PN cadastrar)
├── requirements.txt  # Dependências Python
├── .env              # Credenciais (NÃO versionar)
└── .gitignore        # Arquivos ignorados pelo Git
```

## Logs

Os logs são salvos automaticamente em `starweb.log` com timestamps detalhados, útil para investigar falhas.
