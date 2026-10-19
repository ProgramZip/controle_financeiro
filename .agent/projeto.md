\# 📘 Manual Definitivo de Arquitetura e Inicialização: `controle\_financeiro`



Este documento é o guia oficial e completo para a criação, configuração e desenvolvimento do sistema de gestão financeira pessoal e multi-utilizador\[cite: 1]. Contém toda a arquitetura técnica corrigida, esquemas de base de dados, guia de instalação do ambiente e o Prompt Mestre para o Antgravity IDE\[cite: 1].



\---



\## 1. Visão Geral e Stack Tecnológica

\* \*\*Diretório Raiz do Projeto:\*\* `E:\\controle\_financeiro`\[cite: 1]

\* \*\*Linguagem Base:\*\* Python 3.10+\[cite: 1]

\* \*\*Interface Gráfica (Frontend):\*\* Streamlit (arquitetura híbrida: \*Mobile-First\* para uso rápido no telemóvel/celular e \*Multi-Colunas\* para gestão detalhada no computador)\[cite: 1].

\* \*\*Base de Dados (Backend):\*\* SQLite (`financas.db` - armazenamento local, custo zero, sem necessidade de servidor externo)\[cite: 1].

\* \*\*Dependências Oficiais (`requirements.txt`):\*\*\[cite: 1]

&#x20; \* `streamlit` — Framework web, controlo de estado (`st.session\_state`) e modais (`st.dialog`)\[cite: 1].

&#x20; \* `pandas` — Manipulação de dados, agregações e conciliação de tabelas\[cite: 1].

&#x20; \* `plotly` — Gráficos interativos e responsivos para o Dashboard\[cite: 1].

&#x20; \* `pdfplumber` — Extração de texto e tabelas de extratos bancários em PDF\[cite: 1].

&#x20; \* `Pillow` — Manipulação e gravação de imagens de faturas/notas fiscais\[cite: 1].

&#x20; \* `opencv-python-headless` — Leitura e descodificação de QR Codes diretamente das fotos das notas fiscais.

&#x20; \* `google-genai` — SDK oficial para o Consultor de IA Financeira integrado.

&#x20; \* `python-dotenv` — Carregamento seguro da chave de API (`GEMINI\_API\_KEY`) a partir do ficheiro `.env`.

&#x20; \* `openpyxl` — Exportação de relatórios financeiros para formato Excel (`.xlsx`).



\---



\## 2. Arquitetura de Pastas e Ficheiros



```text

E:\\controle\_financeiro\\

│

├── .agent/                             # 🤖 \[REGRA DE OURO] Área autónoma exclusiva do Antgravity

│   ├── history.md                      # Diário técnico cronológico de todas as alterações feitas no projeto

│   └── scripts\_auxiliares/             # Scripts temporários de teste, migração ou manutenção da IA

│

├── venv/                               # 🐍 Ambiente virtual Python isolado

│

├── uploads/                            # 📁 Armazenamento físico local

│   └── notas/                          # Imagens e comprovativos de notas fiscais associadas aos gastos

│

├── backend/                            # ⚙️ Camada de Dados, Segurança e Regras de Negócio

│   ├── \_\_init\_\_.py

│   ├── database.py                     # Ligação SQLite, criação das 5 tabelas e utilizador admin padrão

│   ├── crud.py                         # Inserções, leituras, atualização em 1 clique, geração de parcelas e recorrências

│   └── utils.py                        # Leitores de PDF/CSV, descodificador de QR Code, backup/restauro e motor de IA

│

├── frontend/                           # 🎨 Camada de Interface e Experiência do Utilizador (Streamlit)

│   ├── \_\_init\_\_.py

│   ├── components.py                   # Janelas pop-up (st.dialog) de registo de Despesas/Receitas e cartões de resumo

│   └── views.py                        # Ecrãs principais: Dashboard, Movimentações, Contas Mensais, Investimentos, Orçamentos e IA

│

├── .env                                # 🔑 Ficheiro oculto com a chave GEMINI\_API\_KEY

├── app.py                              # 🚀 Ponto de entrada da aplicação (gere o login e o encaminhamento de abas)

├── requirements.txt                    # 📦 Lista de pacotes para instalação via pip

└── iniciar\_sistema.bat                 # ⚡ Executável Windows que ativa o venv e lança o servidor na rede local

```



\---



\## 3. Esquema Técnico da Base de Dados (`financas.db`)



O ficheiro `backend/database.py` deverá estruturar 5 tabelas relacionais com todas as travas de segurança e integridade\[cite: 1]:



1\. \*\*`users` (Utilizadores e Permissões):\*\*\[cite: 1]

&#x20;  \* `id` (PK), `username` (UNIQUE), `password\_hash` (SHA-256), `role` (`'admin'`, `'editor'`, `'viewer'`), `created\_at`\[cite: 1].

2\. \*\*`transactions` (Movimentações Financeiras):\*\*\[cite: 1]

&#x20;  \* `id` (PK), `user\_id` (FK), `type` (`'despesa'` ou `'receita'`), `category`, `description`, `amount` (REAL), `payment\_method` (`'À Vista'` ou `'Parcelado'`), `installment\_current`, `installment\_total`, `group\_id` (identificador único para agrupar todas as parcelas de uma mesma compra), `due\_date` (DATE), `status` (`'Pago'`, `'Recebido'`, `'Pendente'`), `invoice\_path` (caminho para `uploads/notas/`), `is\_recurring` (BOOLEAN), `recurring\_ref` (formato `'YYYY-MM'` para impedir duplicação de contas fixas no mês), `created\_at`\[cite: 1].

3\. \*\*`recurring\_bills` (Matriz de Contas Mensais):\*\*\[cite: 1]

&#x20;  \* `id` (PK), `user\_id` (FK), `type`, `category`, `description`, `amount`, `due\_day` (dia de vencimento no mês), `is\_active` (BOOLEAN)\[cite: 1].

4\. \*\*`investments` (Carteira de Investimentos):\*\*\[cite: 1]

&#x20;  \* `id` (PK), `user\_id` (FK), `asset\_name`, `category` (Renda Fixa, Ações, FIIs, Cripto, etc.), `invested\_amount`, `current\_value`, `update\_date`\[cite: 1].

5\. \*\*`budgets` (Orçamentos e Metas Mensais):\*\*\[cite: 1]

&#x20;  \* `id` (PK), `category` (UNIQUE), `monthly\_limit` (REAL)\[cite: 1].



\---



\## 4. Regras de Negócio e Comportamento do Sistema



\### 🔹 Registo em Janela Pop-up (`st.dialog`)

\* O botão \*\*"➕ Nova Movimentação"\*\* abre um modal limpo e adaptado ao ecrã do telemóvel/celular\[cite: 1].

\* \*\*Seleção Obrigatória:\*\* `Despesa` ou `Receita`\[cite: 1].

\* \*\*Fluxo de Despesa:\*\*\[cite: 1]

&#x20; \* \*\*Categorias:\*\* \*Alimentação, Assinaturas, Bares, Restaurantes, Casa, Compras, Contador, Gastos Pessoais, Dívidas e Empréstimos, Educação, Família, Impostos e taxas, Lazer e Hobbies, Mercado, Outros, Pets, Presentes e Doações, Roupas, Saúde, Trabalho, Transporte, Viagem\*\[cite: 1].

&#x20; \* \*\*Pagamento Parcelado:\*\* Se selecionado, exibe o campo de número de parcelas, mostra em tempo real o resumo da divisão (ex: \*"10x de R$ 150,00"\*) e grava todas as parcelas futuras no banco vinculadas pelo mesmo `group\_id`\[cite: 1].

&#x20; \* \*\*Nota Fiscal:\*\* Se marcado "Sim", permite carregar foto ou tirar foto com a câmara, guarda em `uploads/notas/` e tenta ler o QR Code via OpenCV\[cite: 1].

&#x20; \* \*\*Conta Mensal:\*\* Se marcado "Sim", regista também na tabela `recurring\_bills`\[cite: 1].

\* \*\*Fluxo de Recebimento:\*\*\[cite: 1]

&#x20; \* \*\*Categorias:\*\* \*Aluguéis, Empréstimos, Empresa, Nota Fiscal Emitida, Outras Receitas, Salário\*\[cite: 1].

&#x20; \* Campos de Descrição, Valor, Data, Status (\*Pago/Recebido\* ou \*Pendente\*) e opção de Recebimento Mensal\[cite: 1].



\### 🔹 Automação e Fluxo de Caixa

\* \*\*Motor de Recorrência Sem Duplicidade:\*\* Ao iniciar a sessão, o sistema verifica a tabela `recurring\_bills`. Para cada conta ativa, verifica se já existe um registo em `transactions` com o `recurring\_ref` do mês atual (ex: `'2026-10'`). Se não existir, cria a despesa como \*Pendente\*\[cite: 1].

\* \*\*Ação Rápida em 1 Clique:\*\* Tanto nas despesas pendentes quanto na tabela de valores a receber, cada linha terá um botão direto para quitar a conta, mudando o status para \*Pago/Recebido\* e movendo o item imediatamente para a lista de contas quitadas\[cite: 1].

\* \*\*Importador com Conciliação:\*\* Ao carregar um extrato PDF ou CSV, o sistema mostra uma tabela de pré-visualização onde o utilizador pode desmarcar linhas que já tenham sido lançadas manualmente antes de confirmar a gravação\[cite: 1].



\---



\## 5. Passo a Passo: Como Iniciar o Projeto Hoje



Siga esta ordem exata para preparar o terreno antes de a IA começar a programar:



\### Passo 1: Criar a Pasta Principal

1\. Abra o Explorador de Ficheiros do Windows e aceda ao disco \*\*`E:\\`\*\*\[cite: 1].

2\. Crie uma pasta chamada exatamente \*\*`controle\_financeiro`\*\* (`E:\\controle\_financeiro`)\[cite: 1].



\### Passo 2: Abrir no Antgravity IDE

1\. Abra o \*\*Antgravity IDE\*\*.

2\. Vá a \*File > Open Folder\* e selecione a pasta `E:\\controle\_financeiro`\[cite: 1].



\### Passo 3: Criar o Ambiente Virtual (Opcional via Terminal ou pedir à IA)

Se quiser deixar o ambiente virtual pronto pelo terminal do próprio Antgravity, execute:

```powershell

python -m venv venv

.\\venv\\Scripts\\activate

```



\### Passo 4: Enviar o Prompt Mestre ao Agente

Copie o bloco da \*\*Secção 6\*\* abaixo e envie no chat do Antgravity para que ele construa toda a estrutura, instale os pacotes, crie a pasta `.agent` e desenvolva os módulos\[cite: 1].



\---



\## 6. 🚀 Prompt Mestre Definitivo (Copiar e Colar no Antgravity)



```text

Você é o engenheiro de software sénior responsável por construir do zero o aplicativo "controle\_financeiro" para o utilizador Gabriel Guedes Patricio. O projeto será executado localmente em E:\\controle\_financeiro no Windows, utilizando Python, Streamlit e SQLite.



Siga rigorosamente a arquitetura, as regras de ouro e as especificações técnicas abaixo:



\### 📂 1. Estrutura de Pastas e Ficheiros (E:\\controle\_financeiro\\)

Crie e mantenha a seguinte árvore de diretórios:

\- E:\\controle\_financeiro\\.agent\\ -> \[REGRA DE OURO] Pasta exclusiva da IA. Crie imediatamente o ficheiro history.md e registe nele, de forma cronológica e técnica, absolutamente tudo o que for criado, alterado ou corrigido no projeto desde o primeiro passo. Você tem controlo total sobre esta pasta.

\- E:\\controle\_financeiro\\uploads\\notas\\ -> Pasta para guardar fotos de notas fiscais.

\- E:\\controle\_financeiro\\backend\\

&#x20; - \_\_init\_\_.py

&#x20; - database.py -> Ligação SQLite (financas.db) e criação das tabelas: users, transactions, recurring\_bills, investments, budgets.

&#x20; - crud.py -> Funções CRUD, geração de parcelas vinculadas por group\_id, motor de recorrência mensal com trava recurring\_ref (YYYY-MM) e alteração de status em 1 clique.

&#x20; - utils.py -> Leitura de extratos PDF (pdfplumber) e CSV, leitura de QR Code (opencv-python-headless), backup/restauro do banco e integração com Gemini (google-genai).

\- E:\\controle\_financeiro\\frontend\\

&#x20; - \_\_init\_\_.py

&#x20; - components.py -> Modais pop-up (st.dialog) para registo de Despesas e Receitas otimizados para ecrãs mobile e desktop.

&#x20; - views.py -> Ecrãs: Dashboard (com Plotly), Movimentações, Contas Mensais, Investimentos, Orçamentos e Consultor IA.

\- E:\\controle\_financeiro\\.env -> Ficheiro template contendo GEMINI\_API\_KEY="sua\_chave\_aqui".

\- E:\\controle\_financeiro\\requirements.txt -> streamlit, pandas, plotly, pdfplumber, Pillow, opencv-python-headless, google-genai, python-dotenv, openpyxl.

\- E:\\controle\_financeiro\\iniciar\_sistema.bat -> Script batch que ativa o ambiente virtual (venv) e executa: streamlit run app.py --server.address 0.0.0.0

\- E:\\controle\_financeiro\\app.py -> Ponto de entrada principal com sistema de login, barra de navegação responsiva e carregamento das views.



\### 🧠 2. Regras de Negócio Obrigatórias

1\. Login e Utilizadores: Autenticação via st.session\_state com senhas em hash SHA-256 (crie um utilizador padrão admin / admin123 na inicialização).

2\. Modal de Registo (st.dialog):

&#x20;  - Seleção obrigatória de Tipo: Despesa ou Receita.

&#x20;  - Se Despesa: Categoria obrigatória (Alimentação, Assinaturas, Bares, Restaurantes, Casa, Compras, Contador, Gastos Pessoais, Dívidas e Empréstimos, Educação, Família, Impostos e taxas, Lazer e Hobbies, Mercado, Outros, Pets, Presentes e Doações, Roupas, Saúde, Trabalho, Transporte, Viagem), Descrição, Valor, Forma de Pagamento (À Vista ou Parcelado - se parcelado, exibir número de parcelas, mostrar o valor dividido por parcela na tela e gravar as parcelas no banco com o mesmo group\_id), Data de Vencimento, Status (Pago/Pendente), Adicionar Nota Fiscal (Sim/Não - upload de foto para uploads/notas/ e leitura de QR Code) e Conta Mensal (Sim/Não - se sim, gravar em recurring\_bills).

&#x20;  - Se Receita: Categoria (Aluguéis, Empréstimos, Empresa, Nota Fiscal Emitida, Outras Receitas, Salário), Descrição, Valor, Data, Status (Pago/Pendente) e Recebimento Mensal (Sim/Não).

3\. Gestão de Movimentações:

&#x20;  - Seletor para alternar entre Despesas e Receitas.

&#x20;  - Nas Despesas: separar Pendentes e Contas Pagas. Gerar automaticamente as contas de recurring\_bills uma única vez por mês usando recurring\_ref (YYYY-MM).

&#x20;  - Nas Receitas: separar Valores Já Recebidos e Valores a Receber (Pendentes) em formato de tabela, com botão de ação rápida na linha para mudar de Pendente para Pago com 1 clique.

4\. Importação de Extratos (PDF/CSV): Incluir tabela de pré-visualização (conciliação) antes de gravar no banco para evitar duplicação com gastos manuais.

5\. Extras: Orçamentos por categoria com barras de progresso, Backup/Download do ficheiro financas.db em 1 clique, exportação para Excel e aba Consultor IA Financeira.

6\. UX/UI: Design Mobile-First (formulários verticais limpos e botões de fácil toque no smartphone) que expande em colunas organizadas no desktop.



\### ⚡ Ordem de Execução Solicitada:

Passo 1: Crie a estrutura de pastas, a pasta .agent com o history.md inicial, o requirements.txt, o .env e o iniciar\_sistema.bat.

Passo 2: Construa todo o backend (database.py, crud.py, utils.py) e teste a criação do banco.

Passo 3: Construa todo o frontend (components.py, views.py e app.py).

Passo 4: Atualize o .agent/history.md detalhando toda a entrega.



Pode iniciar pelo Passo 1 e seguir estruturando o projeto!

```

