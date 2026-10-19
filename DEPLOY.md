# 🚀 Guia de Deploy - Controle Financeiro no Streamlit Community Cloud

Este guia contém o passo a passo completo para publicar a sua aplicação de **Controle Financeiro Pessoal** no [Streamlit Community Cloud](https://share.streamlit.io/) de forma 100% gratuita.

---

## 📋 Pré-requisitos

1. Uma conta no [GitHub](https://github.com).
2. Uma conta no [Streamlit Community Cloud](https://share.streamlit.io) vinculada ao seu GitHub.
3. Chave de API do Google Gemini (obtenha gratuitamente no [Google AI Studio](https://aistudio.google.com/)).

---

## 🛠️ Passo 1: Subir o Projeto para o GitHub

No terminal (na pasta raiz `E:\controle_financeiro`):

1. **Adicione os arquivos limpos ao Git:**
   ```bash
   git add .
   ```

2. **Crie o primeiro commit:**
   ```bash
   git commit -m "feat: preparar aplicativo para deploy no Streamlit Cloud"
   ```

3. **Crie a branch principal (`main`):**
   ```bash
   git branch -M main
   ```

4. **Crie um repositório no GitHub:**
   - Acesse [github.com/new](https://github.com/new).
   - Nomeie o repositório (ex: `controle-financeiro`).
   - Mantenha-o **Privado** (recomendado) ou Público.
   - **Não** inicialize com README, .gitignore ou licença (já temos esses arquivos locais).

5. **Conecte e suba os arquivos:**
   ```bash
   git remote add origin https://github.com/SEU_USUARIO/controle-financeiro.git
   git push -u origin main
   ```

> 🔒 **Segurança garantida:** O arquivo `.gitignore` configurado garante que sua base de dados (`financas.db`), recibos (`uploads/`), senhas e chaves locais (`.env`) **não** serão enviados para a internet.

---

## ☁️ Passo 2: Configurar o Deploy no Streamlit Community Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io/) e faça login com sua conta do GitHub.
2. Clique no botão **"Create app"** (ou **"New app"**).
3. Selecione a opção **"Yep, I have an app"**.
4. Preencha os campos de implantação:
   - **Repository:** `SEU_USUARIO/controle-financeiro`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** Escolha um subdomínio disponível (ex: `meu-controle-financeiro.streamlit.app`).

---

## 🔑 Passo 3: Configurar os Secrets (Chave Gemini AI)

Para que o **Consultor Inteligente (IA)** funcione na nuvem, você deve configurar os Secrets do Streamlit:

1. Antes de finalizar o deploy (ou clicando no menu **⚙️ Settings > Secrets** do seu app):
2. Na caixa de texto de Secrets, insira:
   ```toml
   GEMINI_API_KEY = "sua_chave_do_google_ai_studio_aqui"
   ```
3. Clique em **"Save"**.
4. Clique em **"Deploy!"**.

---

## 💡 Como Funciona na Primeira Execução

- **Banco de Dados Automático:** Quando o aplicativo iniciar pela primeira vez na nuvem, o SQLite criará automaticamente o banco de dados e o usuário padrão:
  - **Usuário:** `admin`
  - **Senha inicial:** `admin123`
- **Recomendação de Segurança:** Ao logar pela primeira vez, acesse a aba **"Consultor IA & Ajustes"** e altere a senha do usuário `admin`, ou crie um novo usuário para o seu uso pessoal.
- **Uploads Temporários:** No Streamlit Cloud gratuito, novos uploads de comprovantes (`uploads/notas/`) são salvos na instância temporária da nuvem.

---

## 🔄 Como Atualizar o App após Modificações Locais

Sempre que fizer alterações locais no código e quiser enviar para a nuvem:

```bash
git add .
git commit -m "refactor: melhorias no sistema"
git push origin main
```

O Streamlit Community Cloud detectará o novo commit automaticamente e atualizará o aplicativo em poucos segundos!
