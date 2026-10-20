# 📜 Histórico de Desenvolvimento - controle_financeiro

Registro cronológico e técnico de todas as alterações, implementações e manutenções do projeto.

---

## [Fase 1] - 2026-10-16 - Leitura da Especificação e Inicialização do Projeto
- **Status:** Concluída com sucesso.
- **Ações Realizadas:**
  - Leitura integral do documento técnico de especificação: `E:\controle_financeiro\.agent\projeto.md`.
  - Mapeamento e validação de toda a stack tecnológica: Python 3.10+, Streamlit, SQLite (`financas.db`), Plotly, Pandas, pdfplumber, Pillow, opencv-python-headless, google-genai, python-dotenv, openpyxl.
  - Validação dos esquemas das 5 tabelas da base de dados (`users`, `transactions`, `recurring_bills`, `investments`, `budgets`).
  - Mapeamento de todas as regras de negócio:
    - 22 categorias de despesa e 6 categorias de receita.
    - Parcelamento automático com `group_id` e exibição dinâmica.
    - Motor de contas mensais recorrentes com controle por `recurring_ref` (`YYYY-MM`).
    - Quitação de despesas/receitas em 1 clique.
    - Captura de notas fiscais em `uploads/notas/` e decodificação de QR Code.
    - Conciliação bancária via extrato PDF/CSV.
    - Consultor Financeiro IA com Gemini (`google-genai`).
  - Criação do arquivo de histórico oficial do projeto (`.agent/history.md`).

---

## [Fase 2] - 2026-10-16 - Estrutura de Pastas, Configuração Raiz e Ambiente Virtual
- **Status:** Concluída com sucesso.
- **Ações Realizadas:**
  - Criação da árvore de diretórios completa:
    - `backend/` com `__init__.py`
    - `frontend/` com `__init__.py`
    - `uploads/notas/` com `.gitkeep`
    - `.agent/scripts_auxiliares/` com `.gitkeep`
  - Criação do `requirements.txt` contendo todas as dependências oficiais:
    - `streamlit`, `pandas`, `plotly`, `pdfplumber`, `Pillow`, `opencv-python-headless`, `google-genai`, `python-dotenv`, `openpyxl`.
  - Criação do arquivo de ambiente `.env` template com chave `GEMINI_API_KEY="sua_chave_aqui"`.
  - Criação do executável batch Windows `iniciar_sistema.bat` para ativação automática do `venv` e inicialização do servidor Streamlit em `0.0.0.0`.
  - Criação do ambiente virtual Python (`venv`) com Python 3.14.
  - Instalação completa de todas as bibliotecas no `venv`.
  - Execução de script de teste de importação validando o funcionamento de todos os módulos instalados (`ALL PACKAGES OK`).

---

## [Fase 3] - 2026-10-16 - Banco de Dados e Regras de Negócio (backend/database.py e backend/crud.py)
- **Status:** Concluída com sucesso.
- **Ações Realizadas:**
  - Construção do módulo `backend/database.py`:
    - Conexão SQLite gerenciada apontando para `E:\controle_financeiro\financas.db` com suporte a `Row` e foreign keys.
    - Função de hash de senhas SHA-256 (`hash_password`).
    - Criação das 5 tabelas relacionais completas:
      1. `users`: com perfil ('admin', 'editor', 'viewer') e criação automática do usuário padrão `admin` / `admin123`.
      2. `transactions`: com todas as colunas especificadas (`group_id`, `installment_current`, `installment_total`, `invoice_path`, `recurring_ref`, etc.).
      3. `recurring_bills`: matriz de despesas e receitas fixas com `due_day` e `is_active`.
      4. `investments`: controle de patrimônio e rentabilidade por classe de ativos.
      5. `budgets`: limites orçamentários mensais por categoria.
  - Construção do módulo `backend/crud.py`:
    - Inserção de movimentações com suporte a parcelamento automático (cálculo de datas mês a mês, divisão de centavos e vínculo via `group_id`).
    - Ação rápida em 1 clique para alteração de status (`Pendente` -> `Pago`/`Recebido`).
    - Motor de recorrência mensal inteligente (`process_recurring_bills`) com trava de competência (`recurring_ref = 'YYYY-MM'`), impedindo duplicações a cada reload.
    - CRUD completo de investimentos e metas de orçamento (`budgets`).
    - Gestão de usuários e permissões.
  - Criação e execução do script de teste automatizado `.agent/scripts_auxiliares/teste_fase3.py`:
    - Validação de login com hash SHA-256.
    - Validação do parcelamento automático e vínculo por `group_id`.
    - Validação de atualização de status em 1 clique.
    - Validação da trava de não-duplicação de contas recorrentes.
    - Validação de orçamentos e carteira de investimentos.
    - Todos os testes passaram com 100% de sucesso.
  - Banco `financas.db` limpo e inicializado pronto para produção.

---

## [Fase 4] - 2026-10-16 - Utilitários, Leitura de Extratos/Notas e Consultor IA (backend/utils.py)
- **Status:** Concluída com sucesso.
- **Ações Realizadas:**
  - Construção do módulo `backend/utils.py`:
    - **Leitor de Extratos CSV (`read_bank_statement_csv`):** Detecção automática de delimitador (`,` ou `;`), tratamento de padrão numérico brasileiro (R$, pontos e vírgulas), conversão de datas e inferência heurística de categorias para pré-conciliação.
    - **Leitor de Extratos PDF (`read_bank_statement_pdf`):** Extração de tabelas e fluxos de texto com `pdfplumber`, regex de linhas financeiras e padronização para conciliação.
    - **Gestão de Notas Fiscais:** Armazenamento seguro de comprovantes em `uploads/notas/` com compressão JPEG via `Pillow` e nomes únicos UUID/timestamp.
    - **Decodificador de QR Code (`decode_qr_code`):** Integração com `opencv-python-headless` (`cv2.QRCodeDetector`) com tratamento em escala de cinza para leitura instantânea de QR Codes de notas fiscais (NFC-e).
    - **Backup e Restauração:** Geração de dump binário de `financas.db` para download e mecanismo de restauração segura com validação prévia de integridade (`PRAGMA integrity_check`) e backup de segurança antes da substituição.
    - **Exportação para Excel:** Geração de planilha estilizada `.xlsx` via `openpyxl` e `pandas` pronta para download.
    - **Consultor Financeiro IA (`analyze_finances_with_ai`):** Integração com o SDK oficial `google-genai` (modelo `gemini-2.5-flash`), carregando credencial via `python-dotenv`, estruturando agregações de receitas, despesas, cumprimento de limites orçamentários e gerando diagnóstico consultivo com recomendações práticas.
  - Criação e execução do script de teste automatizado `.agent/scripts_auxiliares/teste_fase4.py`:
    - Parsing e inferência de categorias em extrato bancário validados.
    - Salvamento e leitura de imagem validados.
    - Backup binário e exportação para Excel validados.
    - Tratamento seguro de chave e requisições da IA validado.
    - Todos os testes passaram com 100% de sucesso.

---

## [Fase 5] - 2026-10-16 - Componentes Visuais e Modais Pop-up (frontend/components.py)
- **Status:** Concluída com sucesso.
- **Ações Realizadas:**
  - Construção do módulo `frontend/components.py`:
    - **Design System e CSS Customizado (`apply_custom_css`):** Tipografia moderna (Inter), estilização de cards com glassmorphism/gradiente suave, sombras sutis e regras de responsividade com foco Mobile-First.
    - **Renderizador de Métricas (`render_metric_card`):** Componente reutilizável para cards de resumo no Dashboard com ícones, valores de destaque e percentuais coloridos.
    - **Modal de Registro Pop-up (`modal_nova_movimentacao` com `@st.dialog`):**
      - Seletor de tipo obrigatório: `Despesa` ou `Receita`.
      - **Fluxo de Despesa:**
        - Exibição de todas as 22 categorias obrigatórias especificadas no `projeto.md`.
        - Suporte a pagamento `À Vista` e `Parcelado`.
        - Cálculo dinâmico em tempo real do valor de cada parcela (`num_parcelas` de 2 a 72) com exibição visual imediata.
        - Integração com captura de nota fiscal/comprovante (upload ou câmera direta no smartphone) e decodificação automática de QR Code via OpenCV.
        - Opção de salvar como conta mensal fixa (cadastrando automaticamente em `recurring_bills`).
      - **Fluxo de Receita:**
        - Exibição de todas as 6 categorias obrigatórias especificadas no `projeto.md`.
        - Campos de Descrição, Valor, Data, Status (`Recebido` ou `Pendente`) e opção de Recebimento Mensal Fixo.
  - Criação e execução do script de teste automatizado `.agent/scripts_auxiliares/teste_fase5.py`:
    - Validação de integridade de sintaxe e importação de componentes no ambiente virtual `venv`.
    - Teste concluído com 100% de sucesso.

---

## [Fase 6] - 2026-10-16 - Telas Principais, Navegação e Ponto de Entrada (frontend/views.py e app.py)
- **Status:** Concluída com sucesso.
- **Ações Realizadas:**
  - Construção do módulo `frontend/views.py`:
    - **Dashboard Geral (`view_dashboard`):** Seletor de mês de referência, cards de resumo (Receitas, Despesas, Saldo Líquido, Investimentos e Taxa de Poupança), gráfico interativo Donut de Despesas por Categoria (Plotly), gráfico comparativo de barras Receitas vs Despesas e listagem das últimas movimentações.
    - **Movimentações (`view_movimentacoes`):**
      - Seletor rápido entre Despesas e Receitas com filtros por categoria e busca textual.
      - Despesas: separação entre **Contas Pendentes / A Pagar** (com botão de 1 clique para quitar e visualizador de nota fiscal anexada) e **Contas Pagas**.
      - Receitas: separação entre **Valores a Receber (Pendentes)** (com botão de 1 clique para confirmar recebimento) e **Valores Já Recebidos**.
      - Botão no topo para exportação direta para planilha Excel (`.xlsx`).
    - **Contas Mensais (`view_contas_mensais`):** Gestão da matriz de recorrência, botão de sincronização forçada para o mês vigente, cadastro rápido de contas fixas e botões para pausar/ativar recorrência em 1 clique.
    - **Importação de Extratos (`view_importacao_extratos`):** Upload de arquivos PDF e CSV com parsing automático e tabela interativa de conciliação (`st.data_editor`), permitindo ao usuário marcar/desmarcar itens antes de gravar no banco.
    - **Investimentos & Orçamentos (`view_investimentos_orcamentos`):**
      - Carteira de Ativos: total aportado, patrimônio atual, rentabilidade em R$ e %, gráfico de pizza de alocação por classe de ativos e cadastro/exclusão de investimentos.
      - Metas & Orçamentos: monitoramento em tempo real do cumprimento dos tetos por categoria via barras de progresso (`st.progress`) e alertas visuais de estouro.
    - **Consultor IA & Configurações (`view_consultor_configuracoes`):**
      - Consultor IA: diagnóstico financeiro analítico baseado nos gastos reais do mês via Gemini, com campo para dúvidas personalizadas do usuário.
      - Configurações: atualização da chave `GEMINI_API_KEY` com persistência no `.env`, backup/download do banco SQLite em 1 clique, restauração segura e gestão de usuários/permissões (`admin`).
  - Construção do ponto de entrada `app.py`:
    - Configuração de página Streamlit (`page_title="Controle Financeiro"`, `layout="wide"`).
    - Inicialização automática da base de dados e injeção de CSS responsivo.
    - Sistema de autenticação de sessão com tela de login limpa e moderna.
    - Acionamento automático do motor de recorrência na inicialização da sessão.
    - Barra lateral com informações do usuário logado, botão de destaque **➕ Nova Movimentação** (acionando o modal `@st.dialog`), menu de navegação responsivo entre as 6 views e botão de logout.
  - Criação e execução do script de teste automatizado `.agent/scripts_auxiliares/teste_fase6.py`:
    - Validação de compilação de código e integridade de importação de todas as views.
    - Teste concluído com 100% de sucesso.

---

## [Correção & Manutenção] - 2026-10-16 - Resolução de Erro de Tipo no st.data_editor e Isolamento de Estados no Modal
- **Status:** Concluída com sucesso.
- **Problemas Identificados & Corrigidos:**
  1. **Incompatibilidade de Tipo no `st.data_editor` (Importação de Extratos):**
     - **Causa:** O Streamlit disparava `StreamlitAPIException` devido à coluna `'Data'` ser configurada com `st.column_config.DateColumn`, enquanto o DataFrame continha dados em formato texto string.
     - **Solução Implementada:**
       - No módulo `backend/utils.py`, as funções `read_bank_statement_csv` e `read_bank_statement_pdf` passam a forçar explicitamente a conversão da coluna `'Data'` para string (`df_res['Data'] = df_res['Data'].astype(str)`).
       - No módulo `frontend/views.py`, o `st.data_editor` foi reconfigurado para utilizar `st.column_config.TextColumn("Data", help="Formato AAAA-MM-DD")`, eliminando integralmente qualquer conflito de tipagem entre o Streamlit e o Pandas.
  2. **Isolamento de Widgets e Categorias no Modal (`frontend/components.py`):**
     - **Causa:** A alternância dinâmica entre "Despesa" e "Receita" dentro do `@st.dialog` sofria de colisão de estado dos widgets do Streamlit (Selectbox posicional), causando a mistura indevida de categorias de receita e despesa.
     - **Solução Implementada:**
       - Atribuição de chaves exclusivas (`key`) com prefixo para todos os campos do modal (`modal_desp_*` para despesas e `modal_rec_*` para receitas).
       - Garantia estrita de que ao selecionar Despesa, apenas as 22 categorias obrigatórias são renderizadas.
       - Garantia estrita de que ao selecionar Receita, apenas as 6 categorias obrigatórias são renderizadas.
       - Preservação integral do cálculo dinâmico de parcelas, geração de `group_id` e integração de QR Code / câmera para notas fiscais.
  3. **Validação Automatizada:**
     - Criação do script `.agent/scripts_auxiliares/teste_correcoes.py` validando o tipo da coluna `'Data'` como string e a integridade de todos os componentes da interface.

---

## [Correção & UI/UX] - 2026-10-16 - Menu Lateral por Botões e Classificação Inteligente de Extratos
- **Status:** Concluída com sucesso.
- **Problemas Identificados & Soluções Aplicadas:**
  1. **Substituição do Menu Lateral (Remoção das "Bolinhas"):**
     - **Problema:** A navegação lateral utilizava `st.radio` com círculos de seleção, quebrando a estética moderna e profissional da interface.
     - **Solução Implementada em `app.py`:**
       - Remoção completa do `st.radio` da barra lateral.
       - Implementação de menu de navegação vertical utilizando botões estilizados (`st.button` com `use_container_width=True`), gerenciados através de `st.session_state.pagina_ativa`.
       - O botão da tela ativa recebe destaque com estilo visual `primary`, enquanto os demais permanecem como `secondary`.
       - Em `frontend/components.py`, foi injetada estilização CSS dedicada para a sidebar (`text-align: left`, alinhamento flexível, espaçamento proporcional e efeito hover moderno).
  2. **Classificação Rigorosa na Importação de Extratos CSV/PDF:**
     - **Problema:** Lançamentos em extratos CSV com valores absolutos ou formatos variados estavam sendo interpretados indevidamente como receitas.
     - **Solução Implementada em `backend/utils.py`:**
       - Reconstrução da função `_clean_amount` com suporte avançado a números negativos em múltiplos padrões bancários brasileiros (sinal no início `-150`, sinal no final `150-`, parênteses `(150)` e indicador `D`/débito).
       - Criação da função `_classify_transaction_type` aplicando a hierarquia estrita de regras de negócio:
         - Valores com sinal negativo explícito são classificados como **despesa**.
         - Colunas de indicador bancário com marcas de débito/saída são classificadas como **despesa**.
         - Descrições com palavras-chave de saída (*pix enviado, TED enviada, compra, débito, boleto, saque, pgto, fatura, tarifa, ifood, uber, mercado, farmácia, etc.*) são classificadas obrigatoriamente como **despesa**.
         - Apenas valores positivos acompanhados de termos de entrada (*pix recebido, TED recebida, salário, depósito, rendimento, etc.*) ou colunas de crédito são classificados como **receita**.
         - Garantia de que a coluna de data resultante em ambos os leitores (CSV e PDF) seja rigorosamente string no padrão `YYYY-MM-DD`.
  3. **Validação e Testes Automatizados:**
     - Execução do script `.agent/scripts_auxiliares/teste_correcoes.py` cobrindo cenários de parsing numérico, regras de classificação de despesas e receitas e integridade de tipos em CSV, com 100% de sucesso.

---

## [Correção Crítica] - 2026-10-16 - Pop-up Real st.dialog e Leitura Rigorosa de Extratos CSV/PDF (PicPay / Bancos)
- **Status:** Concluída com sucesso.
- **Problemas Identificados & Soluções Aplicadas:**
  1. **Abertura do Cadastro como Pop-up Real (`st.dialog`):**
     - **Problema:** O botão "Nova Movimentação" precisava abrir um modal pop-up flutuante sobreposto nas telas principais, sem recarregar a página estaticamente ou renderizar formulários inline.
     - **Solução Implementada:**
       - Em `frontend/components.py`, a função principal de cadastro `modal_nova_movimentacao` está estritamente decorada com `@st.dialog("➕ Nova Movimentação", width="large")`, configurando o formulário completo de despesa (com as 22 categorias obrigatórias, parcelamento dinâmico e anexo de nota/câmera/QR Code) e receita (com as 6 categorias obrigatórias e opção de recorrência mensal).
       - Em `app.py`, o botão principal na barra lateral invoca diretamente `modal_nova_movimentacao(user["id"])` de forma flutuante sobreposta à aplicação.
       - Em `frontend/views.py`, foram adicionados botões de destaque `➕ Nova Movimentação` no topo de `view_dashboard` e `view_movimentacoes` (ao lado de Exportar Excel), permitindo ao usuário abrir a janela flutuante sobreposta de qualquer ponto do ecossistema sem recarregamento estático.
  2. **Correção Crítica na Leitura de Extratos CSV e PDF (PicPay / Bancos):**
     - **Problema:** Extratos de bancos digitais como PicPay utilizam caracteres Unicode especiais como sinal de menos (`−` `−`), blocos de texto por dia e BOM UTF-8 (`utf-8-sig`). A lógica anterior não capturava esses caracteres e podia interpretar saídas como receitas.
     - **Solução Implementada em `backend/utils.py`:**
       - **Tratamento de Símbolos Monetários e Sinais (`_clean_amount`):**
         - Suporte completo a sinais negativos em ASCII `-`, Unicode `−` (`−`), en-dash `–` (`–`), em-dash `—` (`—`), parênteses `(valor)`, `-R$` e `−R$`.
         - Remoção rigorosa de todos os caracteres não numéricos (R$, $, espaços), convertendo o montante para float positivo (`abs(num)`) e retornando a flag booleana `is_neg`.
       - **Lógica Rigorosa de Tipo (`_classify_transaction_type`):**
         - Se contiver sinal negativo (`-`, `−`, `-R$`, `−R$`, parênteses `(valor)`) OU termos de saída (*Pix enviado, Compra realizada, Pagamento, Guardado no cofrinho, Débito, Tarifa, Transferência enviada*), o campo `type` é obrigatoriamente classificado como **`despesa`**.
         - Apenas se o valor for positivo (`+`) E a descrição contiver termos de entrada (*Pix recebido, Depósito, Salário, Resgate, Dinheiro resgatado, Rendimento*), o campo `type` é classificado como **`receita`**.
       - **Engine de PDF Digital (`read_bank_statement_pdf`):**
         - Além de tabelas tradicionais (`extract_tables`), foi implementado um parser para extratos em texto corrido (PicPay), agrupando blocos por data (`30 de agosto 2026`) com regex para timestamp e valores.
       - **Engine de CSV (`read_bank_statement_csv`):**
         - Suporte a encoding `utf-8-sig` (removendo BOM), separador automático e composição rica da descrição unindo tipo, favorecido e detalhe da transação.
  3. **Validação com Amostras Reais em `.agent/teste/`:**
     - Testes automatizados executados com os arquivos reais `extrato-2026-08-01-2026-08-31.csv` e `extrato-2026-08-01-2026-08-31.pdf`:
       - **CSV:** 92 transações detectadas -> **67 Despesas** e **25 Receitas** (100% de precisão).
       - **PDF:** 92 transações detectadas -> **67 Despesas** e **25 Receitas** (100% de paridade).
       - Todos os valores foram convertidos para float positivo e datas formatadas como string `YYYY-MM-DD`.
     - Script `.agent/scripts_auxiliares/teste_correcoes.py` atualizado e executado com sucesso total (código de saída 0).

---

## [Auditoria & Correção Crítica] - 2026-10-16 - Resolução de Mapeamento de Colunas CSV (Hora/Descrição) e Remoção de Expanders
- **Status:** Concluída com sucesso total.
- **Auditoria de Causa Raiz:**
  1. **Falha de Mapeamento no CSV (`Hora` na `Descrição`):**
     - **Causa Raiz:** No extrato do PicPay (`extrato-2026-08-01-2026-08-31.csv`), as colunas são `data,hora,tipo,"origem / destino",valor,"forma de pagamento"`. A coluna de índice 1 (`df_raw.columns[1]`) é a coluna `'hora'`. Quando a rotina de busca de nomes canônicos de descrição falhava ou utilizava o fallback posicional padrão (`df_raw.columns[1]`), a coluna de hora (`17:39`, `21:51`) era atribuída como `desc_col`. Consequentemente, o horário das operações sobrescrevia a descrição e poluía a inferência de categorias.
     - **Solução Implementada em `backend/utils.py`:**
       - Criação de uma coluna estritamente dedicada para a **Hora** (`Hora`) tanto no leitor de CSV (`read_bank_statement_csv`) quanto no de PDF (`read_bank_statement_pdf`).
       - Implementação de lista de exclusão rigorosa (`cols_proibidas = {date_col, time_col, amount_col}`): **Data, Hora e Valor estão estritamente proibidos** de serem utilizados como descrição.
       - A coluna **Descrição** agora é composta unindo o tipo da operação e o favorecido/origem real (ex: `Pix enviado - Camilla Fernandes Braz da Silva`, `Pix enviado - SUPERMERCADO RIO SUL DO PANTANAL LTDA`), mantendo fidelidade absoluta aos lançamentos bancários.
  2. **Classificação Rigorosa (Despesa vs Receita):**
     - Reforço da prioridade hierárquica em `_classify_transaction_type`:
       - Qualquer transação com valor negativo (incluindo `-`, unicode minus `−` `\u2212`, en-dash `–`, em-dash `—`, `(valor)`, `-R$`, `−R$`) ou termos de saída obrigatórios (*Pix enviado, Compra realizada, Pagamento, Guardado no cofrinho, Débito, Tarifa, Transferência enviada*) é classificada obrigatoriamente como **`despesa`**.
       - Apenas valores positivos sem termos de saída acompanhados de termos de entrada (*Pix recebido, Depósito, Salário, Resgate, Dinheiro resgatado, Rendimento*) são classificados como **`receita`**.
  3. **Remoção de Componentes Estáticos Indesejados (`frontend/views.py` e `components.py`):**
     - **Problema:** O bloco `st.expander("➕ Cadastrar Nova Conta Fixa Recorrente")` permanecia estático na tela de Contas Mensais, quebrando o padrão de pop-up flutuante exclusivo.
     - **Solução:**
       - Criação do modal `@st.dialog("➕ Nova Conta Fixa Recorrente", width="medium")` em `frontend/components.py` (`modal_nova_conta_recorrente`).
       - Remoção completa do `st.expander` e do formulário inline em `frontend/views.py`.
       - Adição de botão de destaque `➕ Nova Conta Recorrente` na barra superior de ações de `view_contas_mensais`, abrindo o modal como janela flutuante sobreposta.
  4. **Atualização da Tabela de Conciliação no Streamlit:**
     - Em `view_importacao_extratos` (`frontend/views.py`), o `st.data_editor` foi atualizado para exibir explicitamente a coluna `Hora` (ajustada para largura `small`), ao lado de `Data`, `Descrição`, `Valor`, `Tipo`, `Categoria` e checkbox `Selecionado`.
     - Inclusão do botão de ação rápida `🔄 Recarregar Extrato` para permitir reprocessamento limpo e invalidação imediata de cache de sessão.
  5. **Validação com Amostras Reais (.agent/teste/):**
     - Script `.agent/scripts_auxiliares/teste_correcoes.py` executado com sucesso:
       - Confirmação de que `Hora` é preservada (`17:39`, `21:51`, etc.) em sua coluna própria.
       - Confirmação de que `Descrição` reflete o favorecido e jamais o horário.
       - Confirmação de paridade exata de 92 transações em CSV e PDF (67 despesas e 25 receitas).

---

## [Manutenção & Compatibilidade] - 2026-10-16 - Migração de use_container_width para width='stretch'
- **Status:** Concluída com sucesso total.
- **Ações Realizadas:**
  1. **Auditoria de Argumentos Depreciados do Streamlit:**
     - Identificado o aviso de depreciação do Streamlit 1.66+:
       `Please replace use_container_width with width. use_container_width will be removed after 2025-12-31.`
       `For use_container_width=True, use width='stretch'. For use_container_width=False, use width='content'.`
  2. **Refatoração Completa do Código:**
     - Varredura em todos os componentes e scripts da aplicação:
       - `app.py`: Substituição em botões da sidebar, botão de login e botão de disparo de modal (4 ocorrências).
       - `frontend/components.py`: Substituição nos botões de submissão dos modais pop-up (`modal_desp_btn_salvar`, `modal_rec_btn_salvar` e `modal_bill_submit`) (3 ocorrências).
       - `frontend/views.py`: Substituição em todos os botões (`st.button`), tabelas (`st.dataframe`, `st.data_editor`), download de planilhas/backups (`st.download_button`) e gráficos Plotly (`st.plotly_chart`) (19 ocorrências).
     - Total de 26 ocorrências migradas para `width='stretch'`, garantindo conformidade estrita e zero avisos nos logs de execução do terminal.
  3. **Validação:**
     - Execução do script automatizado `teste_correcoes.py` e verificação estática confirmando zero ocorrências residuais de `use_container_width`.

---

## [Correção Crítica & IA] - 2026-10-17 - Atualização do Modelo Gemini para gemini-3.8-flash
- **Status:** Concluída com sucesso total.
- **Problema Identificado:**
  - O endpoint de IA disparava erro HTTP 404 (`NotFound: 404 models/gemini-2.5-flash is not found for API version v1alpha...`) ao solicitar a análise financeira no Consultor IA, devido à descontinuação/indisponibilidade da família de modelos antiga (`gemini-2.5-flash`).
  - A API do Google recomendava a utilização do modelo atual `gemini-3.8-flash`.
- **Ações Realizadas em `backend/utils.py`:**
  - Localizada a função `analyze_finances_with_ai` responsável pela geração do diagnóstico estratégico e recomendações de patrimônio.
  - Substituído o identificador do modelo de `model="gemini-2.5-flash"` estritamente para `model="gemini-3.8-flash"`.
  - Mantida a integração nativa com o SDK oficial `google-genai` (`google.genai.Client(api_key=api_key)`), utilizando o método `client.models.generate_content(...)`.
- **Validação e Testes:**
  - Teste de conectividade e geração de texto realizado com sucesso utilizando a chave configurada no `.env`.
  - Teste ponta a ponta com a função `analyze_finances_with_ai(month='2026-08', user_question='Como posso otimizar meus investimentos?')` concluído com código de saída 0, retornando diagnóstico completo com mais de 3.300 caracteres estruturados em markdown.

---

## [Refatoração Arquitetural & Segurança] - 2026-10-17 - Isolamento Multi-Usuário Estrito e Sistema de Partilha de Espaço (user_shares)
- **Status:** Concluída com sucesso total.
- **Contexto & Problema de Negócio:**
  - Anteriormente, consultas no banco (`get_transactions`, `get_recurring_bills`, etc.) não filtravam estritamente pelo `user_id` logado em várias views. Como consequência, contas mensais e movimentações de múltiplos usuários eram agregadas indevidamente, violando a privacidade financeira individual.
  - Havia necessidade de um sistema flexível onde o espaço pessoal de cada usuário permanecesse estritamente isolado por padrão, permitindo contudo o compartilhamento explícito e opcional com outros usuários cadastrados, definindo permissões de `viewer` (apenas leitura) ou `editor` (leitura e modificação).
- **Ações Realizadas na Base de Dados (`backend/database.py`):**
  1. Criação da nova tabela **`user_shares`**:
     - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
     - `owner_id` (INTEGER, FK para `users(id)` ON DELETE CASCADE)
     - `shared_with_user_id` (INTEGER, FK para `users(id)` ON DELETE CASCADE)
     - `permission_level` (TEXT: `'viewer'` ou `'editor'`)
     - `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
     - Restrição `UNIQUE(owner_id, shared_with_user_id)`
  2. Atualização e migração da tabela **`budgets`**:
     - Inclusão da coluna `user_id` (FK para `users(id)` ON DELETE CASCADE).
     - Restrição de unicidade ajustada para `UNIQUE(user_id, category)`, permitindo que cada usuário defina seus próprios tetos de gastos.
  3. Migração defensiva de integridade:
     - Associação de quaisquer registros órfãos pré-existentes sem `user_id` ao usuário administrador padrão (`user_id = 1`).
- **Ações Realizadas no Módulo CRUD (`backend/crud.py`):**
  1. Implementação de funções de autorização e controle de acesso:
     - `get_accessible_user_ids(user_id)`: retorna conjunto contendo o próprio `user_id` mais todos os `owner_id` que compartilharam seus dados com este usuário.
     - `add_user_share(owner_id, shared_with_user_id, permission_level)`: cria ou atualiza compartilhamento com validação de parâmetros e auto-compartilhamento proibido.
     - `get_user_shares_by_owner(owner_id)`: lista compartilhamentos concedidos pelo usuário.
     - `get_user_shares_received(shared_with_user_id)`: lista espaços que outros proprietários compartilharam com ele.
     - `delete_user_share(share_id, owner_id)`: revoga compartilhamento com validação de propriedade.
     - `can_user_edit_resource(user_id, resource_owner_id)`: valida se um usuário tem permissão para editar/excluir dados (proprietário, admin ou editor).
  2. Refatoração rigorosa de todas as consultas:
     - `get_transactions`: filtra por `t.user_id IN (accessible_ids)` e inclui `owner_username` via JOIN com `users`.
     - `get_recurring_bills`: filtra por `r.user_id IN (accessible_ids)` e inclui `owner_username`.
     - `process_recurring_bills`: processa apenas contas do usuário logado e de espaços acessíveis, garantindo trava anti-duplicidade estritamente isolada por `user_id`.
     - `get_investments`: filtra por `i.user_id IN (accessible_ids)`.
     - `get_budgets` e `set_budget`: vinculam tetos ao `user_id` do usuário.
- **Ações Realizadas na Interface Streamlit (`frontend/views.py` e `app.py`):**
  1. Passagem explícita de `user_id` em todas as chamadas de CRUD e processamento de recorrência no login e nas views.
  2. Criação da aba dedicada **"🤝 Partilhamento de Conta"** na view de Consultor IA & Ajustes:
     - Formulário para selecionar outro usuário cadastrado, definir permissão (`viewer` ou `editor`) e conceder acesso imediato.
     - Tabela de acessos concedidos com botão de 1 clique para revogar.
     - Painel informativo de espaços compartilhados recebidos de outros usuários.
  3. Tratamento visual e restrições de permissão:
     - Itens compartilhados exibem badge identificador com o nome do proprietário original (`👤 <username>`).
     - Para usuários com permissão apenas de leitura (`viewer`), botões de quitação, recebimento e exclusão são desativados/ocultados, exibindo indicação visual de `👁️ Somente Leitura`.
- **Validação e Testes:**
  - Criação da suíte automatizada `.agent/scripts_auxiliares/teste_multiuser_shares.py` cobrindo 6 cenários críticos (isolamento padrão, tetos independentes, concessão viewer, concessão editor, listagem cruzada e revogação imediata).
  - Execução dos testes de regressão (`teste_correcoes.py`) confirmando 100% de estabilidade e integridade.

---

## [Correção & Funcionalidade] - 2026-10-17 - Isolamento Estrito por Padrão e Exclusão de Movimentações (Unitária e Mês Completo)
- **Status:** Concluída com sucesso total.
- **Problemas Identificados:**
  1. **Visualização Mista de Movimentações:** Ao carregar a tela de Movimentações ou Dashboard, se houvesse compartilhamento ativo em `user_shares`, as consultas expandiam para todos os usuários autorizados, misturando lançamentos de usuários distintos (ex: "admin" e "Gabriel") na mesma tabela principal.
  2. **Inexistência de Exclusão de Contas Pagas / Concluídas:** Transações já pagas ou recebidas eram exibidas apenas como tabela estática sem opção de exclusão individual (`delete_transaction`).
  3. **Ausência de Exclusão em Lote por Mês:** Não existia mecanismo para expurgar um mês específico de extrato ou testes em lote.
- **Ações Realizadas no Backend (`backend/crud.py`):**
  1. **Isolamento Estrito por Defeito:**
     - Modificadas as funções `get_transactions`, `get_recurring_bills`, `get_investments` e `get_budgets` para adotarem `include_shared: bool = False` por padrão.
     - Quando `user_id` é fornecido, a cláusula SQL filtra estritamente `user_id = ?`, garantindo que cada usuário veja unicamente seus próprios dados. O acesso ampliado só ocorre quando `include_shared=True` for solicitado explicitamente.
  2. **Implementação de Exclusão por Mês Completo (`delete_transactions_by_month`):**
     - Criada a função `delete_transactions_by_month(user_id: int, year_month: str) -> int`, que remove todos os registros da tabela `transactions` onde `user_id = ? AND substr(due_date, 1, 7) = ?`.
  3. **Ajuste na Exclusão Unitária (`delete_transaction`):**
     - Assinatura atualizada para `delete_transaction(transaction_id: int, user_id: int = None, requesting_user_id: int = None) -> bool`, aceitando chamada posicional direta `delete_transaction(item_id, user_id)`.
- **Ações Realizadas no Frontend (`frontend/views.py`):**
  1. **Exclusão Unitária em Todas as Linhas:**
     - Nas seções de **Contas Pagas / Concluídas** e **Valores Já Recebidos**, cada registro passa a exibir um botão dedicado `🗑️ Apagar` com feedback em tempo real (`st.success`) e recarregamento instantâneo (`st.rerun()`).
     - Preservados os botões de exclusão de contas pendentes a pagar e valores pendentes a receber.
  2. **Seção de Exclusão em Lote por Mês:**
     - Adicionado o painel colapsável `🗑️ Exclusão em Lote: Apagar Mês Completo` no topo da tela de Movimentações.
     - Permite selecionar o mês desejado (`YYYY-MM`), exibe o número exato de movimentações encontradas para o usuário logado e exige marcação de confirmação via checkbox de segurança antes de liberar o botão de perigo `🗑️ Apagar Mês Completo`.
  3. **Segregação na Consulta de Espaços Compartilhados:**
     - Na aba *Consultor IA & Ajustes -> Partilhamento de Conta*, criada seção específica onde o usuário escolhe um espaço compartilhado para consultar de forma isolada, sem misturar com sua contabilidade particular.
- **Validação e Testes:**
---

## [Deploy & Infraestrutura] - 2026-10-19 - Preparação para Deploy no Streamlit Community Cloud
- **Status:** Concluída com sucesso total.
- **Ações Realizadas:**
  1. **Configuração do `.gitignore`:**
     - Criado o arquivo `.gitignore` na raiz do projeto com regras estritas para impedir o envio acidental de arquivos sensíveis ou transitórios:
       - Banco de dados SQLite (`financas.db`, `*.db`, `*.sqlite3`).
       - Diretório de comprovantes e uploads (`uploads/`, `uploads/notas/*`).
       - Arquivos de credenciais e variáveis de ambiente (`.env`, `*.env`, `.streamlit/secrets.toml`).
       - Ambientes virtuais Python (`venv/`, `.venv/`, `env/`).
       - Caches do Python e do Streamlit (`__pycache__/`, `*.pyc`, `.streamlit/cache/`).
       - Arquivos e diretórios de dados de teste (`.agent/teste/`).
  2. **Atualização e Saneamento do `requirements.txt`:**
     - Revisão rigorosa de dependências, garantindo versões limpas e compatíveis com a nuvem do Streamlit:
       - `streamlit`
       - `pandas`
       - `plotly`
       - `pdfplumber`
       - `Pillow`
       - `opencv-python-headless` (essencial para ambientes Linux sem servidor gráfico X11)
       - `google-genai`
       - `python-dotenv`
       - `openpyxl`
       - `python-dateutil`
  3. **Compatibilidade Nativa com Streamlit Secrets (`backend/utils.py` e `frontend/views.py`):**
     - O motor do Gemini (`analyze_financial_health_with_gemini`) e a interface do Consultor IA foram atualizados para buscar a chave `GEMINI_API_KEY` primeiro em `os.getenv()` (para desenvolvimento local via `.env`) e, caso ausente, consultar automaticamente `st.secrets.get("GEMINI_API_KEY")` (padrão de nuvem do Streamlit).
  4. **Inicialização e Verificação do Repositório Git:**
     - Repositório local inicializado via `git init`.
     - Verificado com `git status` que `financas.db`, `.env`, `venv/` e `uploads/` estão 100% ignorados pelo Git.
  5. **Criação do Manual de Instruções de Deploy (`DEPLOY.md`):**
     - Criado arquivo detalhado `DEPLOY.md` na raiz com o passo a passo ilustrado:
       - Comandos do Git para primeiro commit e envio para o GitHub.
       - Conexão e criação do aplicativo no Streamlit Community Cloud (`share.streamlit.io`).
       - Configuração de `GEMINI_API_KEY` na área de Secrets do Streamlit Cloud.
       - Orientações de login inicial (`admin` / `admin123`) e auto-provisionamento do SQLite na nuvem.

---

## [Fase 1 - Melhorias Pré-Deploy] - 2026-10-20 - Segurança e Credenciais (Alteração e Redefinição de Senhas)
- **Status:** Concluída com sucesso total (100% dos testes aprovados).
- **Objetivos Atingidos:**
  1. **Alteração da Senha Própria por Qualquer Utilizador (Inclusive Administrador):**
     - Implementado mecanismo seguro para alteração de credencial pessoal com validação prévia da senha atual via hash SHA-256 e exigência de confirmação da nova senha.
  2. **Redefinição Administrativa de Senhas:**
     - Implementado recurso exclusivo para administradores redefinirem diretamente a senha de qualquer conta do sistema em caso de esquecimento ou gerenciamento de credenciais.
- **Ações Realizadas no Backend (`backend/database.py` e `backend/crud.py`):**
  - Em `backend/database.py`:
    - Criada a função `update_user_password(user_id: int, new_password: str) -> bool`: aplica hash SHA-256 e grava a nova credencial no SQLite.
    - Criada a função `change_password_with_verification(user_id: int, current_password: str, new_password: str) -> tuple[bool, str]`: valida se a senha atual confere com o hash registrado, checa tamanho mínimo (>= 4 caracteres) e atualiza a senha de forma atômica.
  - Em `backend/crud.py`:
    - Criada a função `change_user_password(user_id: int, current_password: str, new_password: str)`: encapsula a alteração com verificação para o usuário conectado.
    - Criada a função `admin_set_user_password(admin_user_id: int, target_user_id: int, new_password: str) -> tuple[bool, str]`: valida permissão `admin` do solicitante antes de aplicar a nova senha ao usuário alvo.
- **Ações Realizadas no Frontend (`frontend/views.py`):**
  - Na tela **"🤖 Consultor IA & Ajustes"** -> aba **"⚙️ Configurações & Backup"**:
    - Adicionada a seção **"🔐 Segurança & Alteração de Senha"** para todos os utilizadores autenticados, com campos para Senha Atual, Nova Senha e Confirmação de Senha, com validação instantânea e alertas visuais de feedback.
    - Na subseção **"👥 Gestão de Usuários"** (visível apenas para perfil `admin`), adicionado o expander **"🔑 Redefinir Senha de Usuário (Admin)"**, permitindo selecionar qualquer conta cadastrada e definir uma nova senha diretamente.
- **Validação e Testes:**
  - Criado e executado o script automatizado `.agent/scripts_auxiliares/teste_fase1_senhas.py`:
    - Validação de senha atual incorreta (bloqueio com erro explicativo).
    - Validação de nova senha menor que 4 caracteres (bloqueio).
    - Validação de alteração legítima de senha do usuário (novo login efetuado com sucesso e senha antiga invalidada).
    - Validação de redefinição administrativa por usuário `admin`.
    - Bloqueio de autorização caso usuário comum tente executar comandos de redefinição administrativa.
    - Alteração e restauração da senha do administrador geral do sistema.
    - Testes de regressão (`teste_exclusao_e_isolamento.py`) aprovados com 100% de integridade.

---

## [Fase 2 - Melhorias Pré-Deploy] - 2026-10-20 - Edição de Movimentações e Contas ("Alterar" ao lado de "Apagar")
- **Status:** Concluída com sucesso total (100% dos testes aprovados).
- **Objetivos Atingidos:**
  1. **Edição Direta de Lançamentos e Contas:** Permitir a modificação imediata de qualquer campo (categoria, descrição, valor, data de vencimento/referência, status, forma de pagamento e anexo de nota fiscal) sem necessidade de excluir e readicionar o registro.
  2. **Adição do Botão "✏️ Alterar" ao Lado de "🗑️ Apagar":** Presente de forma homogênea em todas as tabelas e listas da aplicação (Despesas Pendentes, Despesas Pagas, Receitas Pendentes, Receitas Recebidas e Matriz de Contas Fixas Recorrentes).
- **Ações Realizadas no Backend (`backend/crud.py`):**
  - Implementada a função `get_transaction_by_id(transaction_id: int) -> dict`: busca registro único para leitura e preenchimento defensivo.
  - Atualizada a função `update_transaction(transaction_id: int, requesting_user_id: int = None, **kwargs) -> bool`:
    - Adicionado suporte formal ao campo `type` (`despesa` / `receita`), permitindo inclusive a conversão de tipo caso o lançamento tenha sido registrado erroneamente.
    - Preservadas as validações de autorização e propriedade de dados via `can_user_edit_resource`.
  - Validada a função `update_recurring_bill` para suporte pleno à edição de `type`, `category`, `description`, `amount`, `due_day` e `is_active`.
- **Ações Realizadas no Frontend (`frontend/components.py` e `frontend/views.py`):**
  - Em `frontend/components.py`:
    - Criado o modal decorado `@st.dialog("✏️ Alterar Movimentação", width="large")`:
      - Carrega previamente os dados reais da movimentação.
      - Oferece alternância dinâmica entre Despesa e Receita com atualização de categorias correspondentes.
      - Edição de valor, descrição, data de vencimento, forma de pagamento e status.
      - Pré-visualização do comprovante/nota fiscal atual, com opção de remoção ou substituição por novo upload.
    - Criado o modal decorado `@st.dialog("✏️ Alterar Conta Mensal Recorrente", width="medium")`:
      - Permite editar tipo da conta, categoria, descrição, valor mensal, dia do vencimento (1 a 31) e estado da recorrência (Ativa ou Pausada).
  - Em `frontend/views.py`:
    - Na tela de **Movimentações (`view_movimentacoes`)**:
      - Adicionado o botão `✏️ Alterar` em `desp_pendentes` (Contas a Pagar).
      - Adicionado o botão `✏️ Alterar` em `desp_pagas` (Contas Concluídas).
      - Adicionado o botão `✏️ Alterar` em `rec_pendentes` (Valores a Receber).
      - Adicionado o botão `✏️ Alterar` em `rec_recebidas` (Valores Já Recebidos).
    - Na tela de **Contas Mensais (`view_contas_mensais`)**:
      - Adicionado o botão `✏️ Alterar` na lista de contas fixas recorrentes, posicionado ao lado de `🗑️ Apagar`.
- **Validação e Testes:**
  - Criado e executado o script automatizado `.agent/scripts_auxiliares/teste_fase2_edicao.py`:
    - Teste de atualização de múltiplos campos de transação com validação dos dados gravados no SQLite.
    - Teste de bloqueio de edição por usuário não autorizado (garantia de isolamento de segurança).
    - Teste de atualização de conta recorrente com validação no SQLite.
    - Reexecução dos testes da Fase 1 (`teste_fase1_senhas.py`) e regressão (`teste_exclusao_e_isolamento.py`) com 100% de sucesso.

---

## [Fase 3 - Melhorias Pré-Deploy] - 2026-10-20 - Cards de Resumo de Receitas e Despesas na Aba Movimentações
- **Status:** Concluída com sucesso total (100% dos testes aprovados).
- **Objetivos Atingidos:**
  1. **Blocos / Quadrados Visuais Executivos no Topo de Movimentações:** Exibição clara e de alto impacto visual do **Total das Despesas Adicionadas** e do **Total das Receitas Adicionadas** diretamente no topo da tela de movimentações (`view_movimentacoes`).
  2. **Filtro e Sincronização Dinâmica por Período:** Seletor de período integrado que permite alternar entre "Todos os Lançamentos" (acumulado histórico) e meses específicos (`YYYY-MM`), recalculando instantaneamente os valores somados, contadores e tabelas.
- **Ações Realizadas no Frontend (`frontend/views.py`):**
  - Implementado o seletor `📅 Período / Mês de Referência` no topo da tela, listando os meses disponíveis com dados e a opção padrão acumulada.
  - Criados dois blocos métricos destacados via `render_metric_card`:
    - **Card 1 (🔴 Total das Despesas Adicionadas):** Exibe a soma total formatada em `R$ X,XXX.XX`, contador de despesas registradas e indicação do período selecionado em cor de destaque `#f85149`.
    - **Card 2 (🟢 Total das Receitas Adicionadas):** Exibe a soma total formatada em `R$ X,XXX.XX`, contador de receitas registradas e indicação do período selecionado em cor de destaque `#3fb950`.
  - Sincronização automática das abas inferiores (`🔴 Despesas` e `🟢 Receitas`) para refletir o período selecionado de forma responsiva.
- **Validação e Testes:**
  - Criado e executado o script automatizado `.agent/scripts_auxiliares/teste_fase3_cards_movimentacoes.py`:
    - Teste de agregação geral de receitas e despesas.
    - Teste de agregação filtrada por mês específico (`2026-10`).
    - Validação de integridade de importação e execução de `frontend/views.py` e `render_metric_card`.
    - Reexecução de todos os testes das Fases 1 e 2 e regressão (`teste_fase1_senhas.py`, `teste_fase2_edicao.py`, `teste_exclusao_e_isolamento.py`) com 100% de aprovação.

---

## [Fase 4 - Melhorias Pré-Deploy] - 2026-10-20 - Reversão de Status (De Concluídas/Pagas para Pendentes)
- **Status:** Concluída com sucesso total (100% dos testes aprovados).
- **Objetivos Atingidos:**
  1. **Reversão Instantânea em 1 Clique:** Possibilidade de desmarcar e retornar qualquer conta paga ou receita recebida de volta para o status "Pendente", corrigindo instantaneamente marcações acidentais ou conciliações equivocadas.
  2. **Harmonização Visual da Interface:** O botão "🔄 Retornar" foi inserido de forma simétrica nas seções de contas pagas e receitas recebidas, mantendo proporções homogêneas de colunas com as seções pendentes.
- **Ações Realizadas no Backend (`backend/crud.py`):**
  - Implementada a função dedicada `revert_transaction_to_pending(transaction_id: int, requesting_user_id: int = None) -> bool`:
    - Valida propriedade do recurso via `can_user_edit_resource`.
    - Atualiza atomicamente o campo `status` para `'Pendente'` no banco de dados SQLite.
- **Ações Realizadas no Frontend (`frontend/views.py`):**
  - Na tela de **Movimentações (`view_movimentacoes`)**:
    - Na seção **`desp_pagas` (Contas Pagas / Concluídas)**:
      - Adicionado o botão `🔄 Retornar` ao lado de `✏️ Alterar` e `🗑️ Apagar`, com mensagem de sucesso e atualização imediata de estado.
    - Na seção **`rec_recebidas` (Valores Já Recebidos)**:
      - Adicionado o botão `🔄 Retornar` ao lado de `✏️ Alterar` e `🗑️ Apagar`, com mensagem de sucesso e atualização imediata de estado.
- **Validação e Testes:**
  - Criado e executado o script automatizado `.agent/scripts_auxiliares/teste_fase4_reversao_status.py`:
    - Validação de reversão de despesa paga para pendente com checagem direta no SQLite.
    - Validação de reversão de receita recebida para pendente com checagem direta no SQLite.
    - Bloqueio de tentativa de reversão por usuário não autorizado.
    - Execução da suíte completa de testes de todas as 4 fases (`teste_fase1_senhas.py`, `teste_fase2_edicao.py`, `teste_fase3_cards_movimentacoes.py`, `teste_fase4_reversao_status.py`, `teste_exclusao_e_isolamento.py`) com 100% de aprovação e zero regressões.





