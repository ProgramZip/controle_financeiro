# 🚀 Guia de Deploy - Controle Financeiro no Streamlit Community Cloud com Turso Cloud

Este guia contém o passo a passo completo para publicar a sua aplicação de **Controle Financeiro Pessoal** no [Streamlit Community Cloud](https://share.streamlit.io/) com **persistência permanente de dados no Turso Cloud** de forma 100% gratuita.

---

## 📋 Pré-requisitos

1. Uma conta no [GitHub](https://github.com).
2. Uma conta no [Streamlit Community Cloud](https://share.streamlit.io) vinculada ao seu GitHub.
3. Credenciais do **Turso Cloud** (já geradas e configuradas no `.env`).
4. Chave de API do **Google Gemini** (obtida no [Google AI Studio](https://aistudio.google.com/)).

---

## 🛠️ Passo 1: Subir o Projeto para o GitHub

No terminal (na pasta raiz `E:\controle_financeiro`):

1. **Verifique o status dos arquivos:**
   ```bash
   git status
   ```

2. **Adicione os arquivos ao Git:**
   ```bash
   git add .
   ```

3. **Crie o commit de deploy:**
   ```bash
   git commit -m "feat: preparar aplicativo para deploy oficial com Turso Cloud"
   ```

4. **Defina a branch principal (`main`):**
   ```bash
   git branch -M main
   ```

5. **Conecte ao seu repositório no GitHub:**
   - Crie um repositório vazio no GitHub (ex: `controle-financeiro`).
   - Mantenha-o **Privado** (recomendado).
   - Vincule o repositório remoto:
     ```bash
     git remote add origin https://github.com/SEU_USUARIO/controle-financeiro.git
     git push -u origin main
     ```

> 🔒 **Segurança Garantida:** O arquivo `.gitignore` configurado impede o envio de arquivos sensíveis como `.env`, senhas locais e bases temporárias (`financas.db`). Apenas o código-fonte e `.env.example` são enviados.

---

## ☁️ Passo 2: Configurar o Deploy no Streamlit Community Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io/) e faça login com seu GitHub.
2. Clique no botão **"Create app"** (ou **"New app"**).
3. Selecione a opção **"Yep, I have an app"**.
4. Configure os parâmetros da aplicação:
   - **Repository:** `SEU_USUARIO/controle-financeiro`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** Escolha seu subdomínio (ex: `meu-controle-financeiro.streamlit.app`).

---

## 🔑 Passo 3: Configurar os Secrets (Turso Cloud & Gemini AI)

Na tela de configuração do deploy (ou clicando no menu **⚙️ Settings > Secrets** do seu aplicativo no Streamlit):

Insira as credenciais no formato TOML:

```toml
# Chave da Inteligência Artificial (Google Gemini)
GEMINI_API_KEY = "sua_chave_do_google_ai_studio"

# Banco de Dados em Nuvem Permanente (Turso Cloud)
DATABASE_URL = "libsql://controle-financeiro-programzip.aws-sa-east-1.turso.io"
DATABASE_AUTH_TOKEN = "seu_token_jwt_do_turso_aqui"
```

Clique em **"Save"** e em seguida em **"Deploy!"**.

---

## 💎 Benefícios da Integração Turso Cloud no Streamlit

- **Persistência Permanente:** O Streamlit Community Cloud reinicia instâncias periodicamente, o que apagaria bancos SQLite locais tradicionais. Com o **Turso Cloud**, todos os seus lançamentos, usuários, orçamentos e contas fixas permanecem salvos com replicação automática na nuvem.
- **Suporte Offline / Fallback Automático:** Caso rode localmente sem internet ou sem `DATABASE_URL`, o sistema opera automaticamente no banco local `financas.db`.
- **Acesso Multiusuário e Segunda Área de Trabalho:** Espaços compartilhados e permissões funcionam em tempo real para todos os usuários cadastrados.

---

## 🔄 Como Atualizar o App após Modificações

Sempre que fizer alterações no código local e desejar atualizar o Streamlit Cloud:

```bash
git add .
git commit -m "refactor: melhorias no sistema"
git push origin main
```

O Streamlit Community Cloud detectará o commit e atualizará a aplicação automaticamente em poucos segundos!

