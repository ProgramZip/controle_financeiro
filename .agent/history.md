# 📜 Histórico de Desenvolvimento - controle_financeiro

> 🚨 **REGRA DE OURO MANDATÓRIA PARA AGENTES DE IA E DESENVOLVEDORES:**
> **É ESTRITAMENTE OBRIGATÓRIO** consultar e ler integralmente este arquivo (`.agent/history.md`) **ANTES** de iniciar qualquer alteração, refatoração, implementação ou exclusão de código no projeto `controle_financeiro`.
> Este documento contém o histórico completo de decisões de arquitetura, correções de bugs, esquemas de banco de dados, regras de negócio multi-usuário e integrações de nuvem (Turso Cloud e Google Gemini).
> Ao concluir qualquer tarefa ou fase, é **OBRIGATÓRIO** atualizar este arquivo com um registro detalhado de todas as alterações realizadas, seguindo rigorosamente o padrão cronológico e técnico aqui estabelecido.

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
    - Bloqueio de tentativa de reversão por usuário não autorizado.
    - Execução da suíte completa de testes de todas as 4 fases (`teste_fase1_senhas.py`, `teste_fase2_edicao.py`, `teste_fase3_cards_movimentacoes.py`, `teste_fase4_reversao_status.py`, `teste_exclusao_e_isolamento.py`) com 100% de aprovação e zero regressões.

---

## [Evolução Estrutural & Usabilidade] - 2026-10-20 - Modernização Completa, Resiliência de IA, Perfis Expandidos e Espaços Compartilhados
- **Status:** Concluída com sucesso total (100% dos testes unitários e de regressão aprovados).
- **Resumo Executivo das Implementações:**

### 🛠️ 1. Correção Robusta do Erro 503 do Gemini com Retries e Fallback de Modelos (`backend/utils.py`)
- **Problema:** Picos de demanda na infraestrutura da Google provocavam respostas transitórias de erro `503 UNAVAILABLE` / `ResourceExhausted` durante o uso do Consultor IA.
- **Solução Implementada:**
  - Implementada lógica robusta de tentativas automáticas com *exponential backoff* (atraso progressivo de 2, 4 e 6 segundos) e múltiplos modelos alternativos estáveis (`gemini-3.8-flash`, `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`).
  - Tratamento defensivo de exceções de sobrecarga de rede, retornando mensagem orientativa amigável ao usuário caso todos os endpoints públicos estejam momentaneamente congestionados.

### 👤 2. Perfis de Utilizador Expandidos (`backend/database.py`, `backend/crud.py` e `frontend/views.py`)
- **Base de Dados & Migração:**
  - Atualizada a tabela `users` com colunas cadastrais opcionais: `full_name` (Nome Completo), `address` (Endereço) e `cpf` (Documento/CPF).
  - Adicionada rotina de migração defensiva com `PRAGMA table_info(users)` e comandos dinâmicos `ALTER TABLE users ADD COLUMN ...` executados automaticamente na inicialização sem perda de dados existentes.
  - O campo `username` permanece protegido como identificador único para autenticação e concessão de compartilhamento.
- **CRUD & Interface:**
  - Implementadas funções `update_user_profile(user_id, full_name, address, cpf)` e `get_user_profile(user_id)`.
  - Atualizada a função `get_users()` e `add_user()` para suportar os novos campos de perfil.
  - Na tela de Configurações (`view_consultor_configuracoes`), adicionada a seção **👤 Meu Perfil Cadastral**, permitindo visualizar o login e atualizar nome completo, CPF e endereço com atualização imediata da sessão ativa.
  - Na gestão de usuários pelo Administrador, incluídos os campos cadastrais na criação de usuários e na listagem em tabela.

### 🔍 3. Filtros Globais Unificados por Botão/Popover (`frontend/components.py` e `views.py`)
- **Problema:** Filtros dispersos e caixas de texto repetidas em abas individuais poluiam a tela e geravam inconsistências de usabilidade.
- **Solução Implementada:**
  - Criado o componente reutilizável `render_unified_filter_popover` acionado via `st.popover("🔍 Filtros Globais")` no topo das telas principais.
  - Suporte completo a 5 critérios de filtro simultâneos:
    1. **Período:** Seleção por mês `YYYY-MM` ou histórico acumulado ("Todos os Lançamentos").
    2. **Busca Textual Livre:** Pesquisa em tempo real por descrição ou favorecido/destinatário.
    3. **Data de Vencimento:** Opção por Qualquer Data, Intervalo de Datas (De/Até) ou Data Específica exata.
    4. **Faixa de Valor:** Filtro por valor mínimo e máximo em R$.
    5. **Categorias Específicas:** Multiselect dinâmico contendo as categorias das movimentações ou contas.
  - Substituição dos controles soltos, promovendo interface limpa, ágil e focada.

### 📊 4. Reestruturação da Aba de Contas Mensais (`frontend/views.py`)
- **Problema:** A visualização de contas recorrentes misturava despesas e receitas em uma única lista sem métricas de resumo.
- **Solução Implementada:**
  - Adoção exata do mesmo padrão visual, organizacional e modular da aba de Movimentações:
    - **Cards Métricos no Topo:** Total de Despesas Fixas Ativas (R$ e contagem) e Total de Receitas Fixas Ativas (R$ e contagem).
    - **Abas Dedicadas:** `🔴 Contas a Pagar (Despesas Fixas)` e `🟢 Receitas Fixas`.
    - **Listagem Estruturada:** Colunas perfeitamente alinhadas com informações detalhadas (vencimento, categoria e badge de status Ativa/Pausada), valor formatado em destaque e botões de ação rápida (`⏸️ Pausar` / `▶️ Ativar`, `✏️ Alterar` e `🗑️ Apagar`).

### 🗑️ 5. Exclusão em Lote por Modal `st.dialog` (`frontend/components.py` e `views.py`)
- **Problema:** A exclusão de um mês inteiro ocupava um bloco estático inline (`st.expander`), sujeito a cliques acidentais e poluição visual.
- **Solução Implementada:**
  - Removido o expander estático da tela principal.
  - Criado o modal seguro `@st.dialog("🗑️ Exclusão em Lote: Apagar Mês Completo", width="medium")` (`modal_excluir_mes_completo`), acionado por um botão elegante `🗑️ Excluir Mês` no topo de Movimentações.
  - O modal exige seleção do mês alvo, exibe a contagem exata de lançamentos que serão apagados e requer confirmação explícita por checkbox de segurança antes de liberar o botão de exclusão permanente.

### 🤝 6. Nova Página Dedicada "Espaços Compartilhados" - Segunda Área de Trabalho (`frontend/views.py` e `app.py`)
- **Problema:** O compartilhamento de contas ficava oculto em uma aba secundária nas Configurações, sem suporte para uma experiência operacional real de colaboração financeira.
- **Solução Implementada:**
  - Removida a gestão antiga de partilha das Configurações e criada uma **página dedicada no menu lateral**: `"🤝 Espaços Compartilhados"`.
  - **Aba 1: Segunda Área de Trabalho (Acessos Recebidos):**
    - **Modo Editor (`editor`):** Concede uma "Segunda Área de Trabalho" completa sobre o espaço do proprietário. O editor visualiza os cards de métricas do espaço compartilhado, aplica filtros globais, adiciona novas movimentações diretamente na conta do parceiro (`modal_nova_movimentacao(user_id=owner_id)`), edita lançamentos, quita/recebe contas e gerencia contas recorrentes.
    - **Modo Visualizador (`viewer`):** Concede um Dashboard consolidado e restrito (modo estritamente consultivo/leitura), com cards de resumo financeiro e tabelas analíticas estruturadas de transações e contas fixas, sem permissão de alteração ou exclusão.
  - **Aba 2: Gerenciar Meus Compartilhamentos (Concedidos):**
    - Formulário limpo para convidar outros usuários cadastrados definindo o nível de acesso (`viewer` ou `editor`).
    - Gestão de acessos concedidos com histórico de concessão e botão de revogação imediata (`🗑️ Revogar`).

### ✨ 7. Modernização Visual (Mobile & Desktop UI/UX) e Validação Total
- **UI/UX:** Estilização refinada via `frontend/components.py` (`apply_custom_css`) com espaçamentos otimizados para smartphones, cantos arredondados em dataframes, botões táteis no menu executivo da barra lateral e popovers estilizados.
- **Validação de Testes Automatizados:**
  - Criado o script `.agent/scripts_auxiliares/teste_fase7_evolucao_completa.py` cobrindo schema, migrações, perfis cadastrais, permissões de Segunda Área de Trabalho, lógica dos filtros globais e importação de componentes.
  - Reexecução com sucesso total de 100% da suíte de regressão (`teste_fase1_senhas.py`, `teste_fase2_edicao.py`, `teste_fase3_cards_movimentacoes.py`, `teste_fase4_reversao_status.py`, `teste_exclusao_e_isolamento.py`).

---

## [Melhorias Finais - Fase 1] - 2026-10-20 - Sincronização Controlada de Contas Mensais e Tabela de Dispensas (recurring_dismissals)
- **Status:** Concluída com sucesso total (100% dos testes aprovados).
- **Problema de Negócio Identificado:**
  - Anteriormente, o motor `process_recurring_bills` era disparado cegamente na inicialização da sessão e login (`app.py`), gerando movimentações mesmo em dias normais do mês.
  - Além disso, se o usuário excluísse manualmente uma movimentação gerada por recorrência para o mês vigente (`DELETE`), a execução automática subsequente recriava a mesma conta de forma indevida, desrespeitando a decisão do usuário de apagá-la naquela competência.
- **Ações Realizadas na Base de Dados (`backend/database.py`):**
  - Criação da tabela **`recurring_dismissals`** para registro de dispensas/exclusões intencionais:
    ```sql
    CREATE TABLE IF NOT EXISTS recurring_dismissals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recurring_ref TEXT NOT NULL, -- 'YYYY-MM'
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        type TEXT NOT NULL,
        dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, recurring_ref, description, category, type)
    );
    ```
- **Ações Realizadas no Backend (`backend/crud.py`):**
  1. **Controle de Execução Temporal & Parâmetro `force_manual`:**
     - A função `process_recurring_bills(year_month=None, user_id=None, force_manual=False)` agora exige estritamente que seja o **dia 1 do mês** para qualquer execução automática (`not force_manual and hoje.day != 1 -> return 0`).
     - Apenas quando o usuário aciona explicitamente o botão manual (`force_manual=True`), a rotina executa fora do dia 1.
  2. **Rastreamento de Exclusões Manuais:**
     - Em `delete_transaction`: Quando uma transação recorrente (`is_recurring=1` com `recurring_ref`) é apagada pelo usuário, ela é gravada em `recurring_dismissals`.
     - Em `delete_transactions_by_month`: Ao apagar um mês inteiro, todas as contas recorrentes nele contidas são registradas em `recurring_dismissals`.
  3. **Proteção Anti-Regeneração Automática:**
     - O motor de recorrência checa a tabela `recurring_dismissals`. Contas apagadas pelo usuário naquela competência são ignoradas e nunca mais são regeneradas automaticamente no mês.
     - Se o usuário desejar restaurá-las intencionalmente, ao clicar no botão "⚡ Sincronizar Mês Vigente" (`force_manual=True`), as dispensas daquele mês são limpas e as contas ativas são reprocessadas.
- **Ações Realizadas no Frontend e Login (`app.py` e `frontend/views.py`):**
  - Em `app.py`: O gatilho de login agora valida estritamente se `date.today().day == 1` com `force_manual=False`, impedindo execuções automáticas desnecessárias fora do dia 1.
  - Em `frontend/views.py`: O botão de ação rápida "⚡ Sincronizar Mês Vigente" passa o parâmetro explícito `force_manual=True`.
- **Validação e Testes:**
  - Criado e executado o script automatizado `.agent/scripts_auxiliares/teste_fase1_sincronizacao_controlada.py`:
    - Validação do bloqueio automático fora do dia 1.
    - Validação de geração manual via `force_manual=True`.
    - Validação de gravação em `recurring_dismissals` após exclusão pelo usuário.
    - Validação da proteção contra recriação cega de contas apagadas.
    - Validação da regeneração permitida apenas no clique manual explícito.
  - Execução da suíte de regressão (`teste_fase7_evolucao_completa.py`, `teste_exclusao_e_isolamento.py`) confirmando 100% de sucesso e integridade.

---

## [Melhorias Finais - Fase 2] - 2026-10-20 - Card de Alerta de Vencimento Imediato e Quitação Rápida no Dashboard
- **Status:** Concluída com sucesso total (100% dos testes aprovados).
- **Problema de Negócio Identificado:**
  - O usuário não possuía um aviso proativo e imediato no topo da aplicação sobre despesas que estão vencendo no dia ou nos dias imediatamente seguintes (ou já vencidas em atraso), obrigando-o a navegar até a tela de Movimentações para checar pendências urgentes.
- **Solução Implementada (`frontend/views.py`):**
  1. **Componente de Banner / Card de Alerta (`render_due_date_alerts`):**
     - Posicionado estrategicamente no topo do **Dashboard Geral** (`view_dashboard`), logo abaixo do título principal da página.
     - Realiza consulta filtrada estritamente pelo `user_id` logado (`trans_type="despesa"`, `status="Pendente"`).
     - Analisa a data de vencimento (`due_date`) em relação à data atual (`hoje = date.today()`):
       - **Vencida em Atraso:** (`due_date < hoje`) -> badge vermelho com contagem de dias em atraso.
       - **Vence Hoje:** (`due_date == hoje`) -> badge dourado com destaque imediato.
       - **Vence Amanhã:** (`due_date == hoje + 1 dia`) -> badge azul claro.
       - **Vence nos Próximos 3 Dias:** (`hoje < due_date <= hoje + 3 dias`) -> badge azul com contagem de dias restantes.
     - Se não existirem despesas vencidas ou vencendo nos próximos 3 dias, o card não é exibido, mantendo o painel limpo.
  2. **Resumo Visual Consolidado & Quitação Rápida (`_render_alert_item_row`):**
     - O banner exibe a contagem total de contas urgentes e o valor somado em R$ com destaque de urgência (ícone `🚨` para atrasos ou `⚠️` para vencimentos iminentes).
     - Cada conta é exibida com: badge de urgência, descrição, número de parcela (se parcelado), categoria, data de vencimento, valor formatado e botão **"✅ Quitar"** em 1 clique.
     - O botão de quitação rápida aciona `update_transaction_status(item["id"], "Pago", requesting_user_id=user["id"])`, emite notificação `st.toast` e atualiza a interface instantaneamente via `st.rerun()`.
     - Layout ergonômico: exibe as 3 contas mais prioritárias diretamente; se houver mais de 3, exibe as demais organizadas dentro de um expander expansível (`st.expander`), garantindo fluidez e responsividade tanto no desktop quanto em smartphones.
- **Validação e Testes Automatizados:**
  - Criado o script de validação `.agent/scripts_auxiliares/teste_fase2_alerta_vencimento.py`:
    - Validação de detecção de contas em atraso, vencendo hoje, amanhã e em 3 dias.
    - Validação de exclusão correta de contas futuras (> 3 dias), contas já pagas, receitas e contas de terceiros (isolamento estrito por usuário).
    - Validação da ação de quitação rápida em 1 clique (`update_transaction_status` para `"Pago"`).
  - Execução dos testes automatizados com 100% de êxito e reexecução de regressão (`teste_fase1_sincronizacao_controlada.py`, `teste_fase7_evolucao_completa.py`).

---

## [Melhorias Finais - Fase 3] - 2026-10-20 - Suporte Flexível a Banco de Dados em Nuvem (Turso / LibSQL / SQLite Customizado)
- **Status:** Concluída com sucesso total (100% dos testes aprovados).
- **Problema de Negócio Identificado:**
  - Em ambientes de nuvem efêmeros (como Streamlit Community Cloud), o disco local pode ser resetado a cada reinício de container, o que faria o arquivo SQLite local (`financas.db`) ser restaurado ao estado inicial caso o usuário não utilizasse backup.
- **Solução Implementada (`backend/database.py` e `.env.example`):**
  1. **Detecção e Resolução de Conexão Flexível:**
     - Implementada a função `get_database_url()`, que busca automaticamente a string de conexão em:
       1. Variáveis de ambiente `DATABASE_URL` ou `TURSO_DATABASE_URL` (`.env`).
       2. Secrets do Streamlit (`st.secrets["DATABASE_URL"]` ou `st.secrets["TURSO_DATABASE_URL"]`), ideal para deploy no Streamlit Cloud.
     - Implementada a função `get_turso_auth_token()` para suporte a autenticação JWT do Turso/LibSQL.
  2. **Arquitetura Multi-Driver Transparente em `get_connection()`:**
     - **Modo Nuvem (Turso / LibSQL):** Detecta URLs com esquema `libsql://` ou `https://` (ou domínio `turso.io`). Tenta carregar o driver `libsql_experimental` ou `libsql` dinamicamente com Row Factory ativado e validação de chaves estrangeiras. Caso a biblioteca não esteja instalada no ambiente local, emite um `warning` descritivo e faz fallback seguro para o SQLite local sem travar a execução.
     - **Modo SQLite Personalizado:** Aceita URLs como `sqlite:///caminho/banco.db` ou caminhos diretos, permitindo apontar para volumes persistentes ou bases de homologação/teste.
     - **Modo Padrão Local (financas.db):** Caso nenhuma variável de ambiente seja configurada, opera normalmente com a base SQLite padrão (`financas.db`), garantindo retrocompatibilidade total com o desenvolvimento local.
  3. **Documentação e Onboarding (`.env.example`):**
     - Criado o arquivo `.env.example` contendo as instruções práticas para configuração do Gemini e do banco em nuvem (Turso/LibSQL) ou SQLite customizado.
- **Validação e Testes Automatizados:**
  - Criado o script de validação `.agent/scripts_auxiliares/teste_fase3_banco_nuvem.py`:
    - Validação de conexão e consultas com o banco SQLite padrão (`financas.db`).
    - Validação de conexão e escrita com SQLite personalizado via `DATABASE_URL="sqlite:///..."`.
    - Validação de fallback defensivo com emissão de `warning` estruturado para URLs Turso quando o driver não está presente.
  - Bateria completa de regressão executada com 100% de êxito:
    - `teste_fase1_sincronizacao_controlada.py` -> APROVADO
    - `teste_fase2_alerta_vencimento.py` -> APROVADO
    - `teste_fase3_banco_nuvem.py` -> APROVADO
    - `teste_fase7_evolucao_completa.py` -> APROVADO

---

## [Turso Cloud] - 2026-10-20 - Integração e Ativação Operacional do Banco em Nuvem Turso
- **Status:** Ativo e 100% operacional no cluster de nuvem `controle-financeiro-programzip.aws-sa-east-1.turso.io`.
- **Objetivo Concluído:**
  - Conectar a aplicação ao banco de dados na nuvem do Turso utilizando as credenciais `DATABASE_URL` e `DATABASE_AUTH_TOKEN` no `.env`.
- **Ações Realizadas:**
  1. **Dependências (`requirements.txt`):**
     - Adicionado o pacote oficial `libsql-client` ao `requirements.txt`.
  2. **Módulo de Conexão (`backend/database.py`):**
     - Suporte nativo à leitura de `DATABASE_URL` e `DATABASE_AUTH_TOKEN` (com retrocompatibilidade para `TURSO_AUTH_TOKEN` e `st.secrets`).
     - Conversão automática do protocolo `libsql://` para `https://` para conexão via HTTP/REST compatível com todos os ambientes e proxies sem dependência de WebSockets ou compilação C/Rust.
     - Implementação da camada adaptadora DB-API 2.0 (`LibsqlConnection`, `LibsqlCursor`, `LibsqlRow`):
       - Suporte completo a Row Factory com acesso por nome (`row["col"]`), por índice numérico (`row[0]`), método `.get()` e conversão transparente para `dict(row)`.
       - Tratamento correto de contagem de linhas afetadas (`rowcount`) e IDs autoincrementais inseridos (`lastrowid`) corrigindo a falsidade booleana de `ResultSet` vazio em operações DML (`self._rs is not None`).
       - Gerenciamento transparente de ciclo de vida de conexões (context manager `with get_connection() as conn:`) fechando as sessões HTTP de forma limpa e sem vazamento de threads.
     - Preservação total do fallback automático para SQLite local (`financas.db`) caso nenhuma credencial seja informada.
  3. **Configuração do `.env` e `.env.example`:**
     - Configurado `.env` com a URL e Token JWT de produção do Turso Cloud.
     - Documentado `.env.example` com os parâmetros `DATABASE_URL` e `DATABASE_AUTH_TOKEN`.
- **Validação e Testes Automatizados no Turso Cloud:**
  - Criado e executado o script de validação `.agent/scripts_auxiliares/teste_turso_cloud_completo.py`:
    - Inicialização remota de todas as 7 tabelas estruturais no cluster do Turso.
    - Autenticação e criação do usuário padrão `admin`.
    - Ciclo completo de lançamentos: inserção (`add_transaction`), consulta filtrada (`get_transactions`), alteração de status em 1 clique (`update_transaction_status`) e exclusão (`delete_transaction`).
  - Suíte completa de testes de regressão (`teste_fase1_sincronizacao_controlada.py`, `teste_fase2_alerta_vencimento.py`, `teste_fase3_banco_nuvem.py`, `teste_fase7_evolucao_completa.py`) executada diretamente contra o Turso Cloud com 100% de sucesso.

---

## [Deploy Oficial] - 2026-10-20 - Preparação e Validação para Deploy no Streamlit Community Cloud
- **Status:** Concluído com sucesso (100% validado e pronto para deploy).
- **Ações Realizadas:**
  1. **Validação de Arquivos de Deploy:**
     - `app.py`: Validado na raiz do projeto (`E:\controle_financeiro\app.py`) como entrypoint principal do Streamlit (`st.set_page_config`, `init_db()`, `apply_custom_css()`, roteamento por abas e renderização responsiva).
     - `requirements.txt`: Limpo e auditado para execução em nuvem sem dependências de compilação ou drivers pesados locais. Contém: `streamlit`, `pandas`, `plotly`, `pdfplumber`, `Pillow`, `opencv-python-headless`, `google-genai`, `python-dotenv`, `openpyxl`, `python-dateutil` e `libsql-client`.
     - `.gitignore`: Atualizado e validado para proteger dados e chaves sensíveis: bloqueia `.env`, `*.env`, `.streamlit/secrets.toml`, ambientes virtuais (`venv/`), logs, caches temporários e bases locais (`financas.db`, `*.db`, `*.sql`), preservando o `.env.example` como template.
  2. **Compatibilidade Abrangente com `st.secrets`:**
     - Em `backend/database.py`, as funções `get_database_url()` e `get_database_auth_token()` suportam 3 modalidades:
       - Variáveis de ambiente padrão (`DATABASE_URL`, `TURSO_DATABASE_URL`, `DATABASE_AUTH_TOKEN`, `TURSO_AUTH_TOKEN`).
       - Streamlit Secrets diretos (`st.secrets["DATABASE_URL"]`, `st.secrets["DATABASE_AUTH_TOKEN"]`).
       - Streamlit Secrets aninhados (`st.secrets["turso"]["DATABASE_URL"]` ou `st.secrets["turso"]["url"]`, e `st.secrets["turso"]["DATABASE_AUTH_TOKEN"]` ou `st.secrets["turso"]["auth_token"]`).
     - Em `backend/utils.py`, `analyze_finances_with_ai` suporta leitura direta de `GEMINI_API_KEY` via `os.environ` e `st.secrets`.
  3. **Guia Oficial de Deploy (`DEPLOY.md`):**
     - Atualizado com passo a passo claro e resumido para envio ao GitHub (`git status`, `git add .`, `git commit`, `git push origin main`) e configuração no Streamlit Cloud.
     - Documentada a configuração de Secrets do Streamlit no formato TOML (`GEMINI_API_KEY`, `DATABASE_URL`, `DATABASE_AUTH_TOKEN`).
     - Destacados os benefícios do Turso Cloud: persistência contínua dos dados mesmo com resets de container do Streamlit Cloud, fallback transparente para SQLite local e segurança reforçada de credenciais.

---

## [Otimização de Performance & Cache] - 2026-10-21 - Eliminação de Latência e Aceleração do Turso Cloud
- **Status:** Concluído com sucesso (Aceleração comprovada em benchmark de 60x a 44.000x nas operações críticas).
- **Problema de Negócio Identificado:**
  - Latência acentuada nas transições de página e cliques do Streamlit devido ao overhead acumulado de conexões de rede HTTP remotas ao Turso Cloud (AWS São Paulo) a cada rerun completo do script.
  - A função `init_db()` executava 13+ queries DDL/DML repetitivamente em cada interação de usuário.
  - Consultas frequentes de orçamentos, investimentos, contas fixas e transações repetiam requisições de rede sem necessidade.
- **Soluções de Engenharia Implementadas:**
  1. **Memoização de Inicialização de Banco (`init_db` e `app.py`):**
     - `init_db(force=False)` agora possui trava em memória a nível de processo, evitando reexecuções redundantes.
     - Em `app.py`, a chamada foi envolvida com `@st.cache_resource(show_spinner=False)`, garantindo execução única no boot do servidor.
     - **Ganho:** Tempo de inicialização por rerun despencou de ~450ms para 0.002ms (~44.000x mais rápido).
  2. **Pool Persistente HTTP e Daemon Thread no Driver Turso (`backend/database.py`):**
     - Implementado gerenciamento compartilhado do cliente `libsql-client` (`get_shared_libsql_client`), mantendo sessões HTTP keep-alive abertas e reutilizáveis entre queries, evitando recriação de loops asyncio, conexões TCP e handshakes TLS a cada context manager.
     - Patch defensivo aplicado ao executor do `libsql_client` para criar threads internas com `daemon=True`, evitando qualquer bloqueio de encerramento do processo Python.
  3. **Camada de Cache Estratégico com `@st.cache_data` (`backend/crud.py`):**
     - Leitura frequente com cache configurado:
       - `get_transactions()`: TTL de 60 segundos com suporte a filtro direto por `month_year` e `limit`.
       - `get_budgets()`: TTL de 180 segundos.
       - `get_investments()`: TTL de 180 segundos.
       - `get_recurring_bills()`: TTL de 180 segundos.
       - `get_user_shares_by_owner()` e `get_user_shares_received()`: TTL de 120 segundos.
       - `get_users()` e `get_user_profile()`: TTL de 300 segundos.
  4. **Invalidação Ativa e Transparente (`clear_app_cache`):**
     - Implementada a função `clear_app_cache()`, chamada automaticamente em todas as 16 funções de mutação (INSERT, UPDATE, DELETE).
     - Garante consistência imediata: qualquer alteração de status, novo lançamento ou exclusão limpa o cache e reflete instantaneamente na interface sem inconsistências.
  5. **Otimização de Consultas e Gerenciamento de Sessão (`frontend/views.py`):**
     - O Dashboard agora puxa estritamente as transações do mês selecionado (`month_year=mes_sel`), reduzindo drasticamente o tráfego de dados na rede.
     - O alerta de vencimento restringe a consulta até 3 dias à frente (`end_date`), filtrando diretamente no cluster do Turso.
     - Os dados de perfil agora são lidos prioritariamente de `st.session_state["user"]`, eliminando idas ao banco de dados durante a navegação entre abas.
- **Validação e Diagnóstico Automatizado:**
  - Criado e executado o script `.agent/scripts_auxiliares/teste_performance_cache_turso.py`:
    - `init_db()`: de 447.3ms para 0.002ms (44.733x mais rápido).
    - `get_transactions()`: de 17.4ms para 0.233ms (74.5x mais rápido).
    - `get_budgets()`: de 17.0ms para 0.147ms (115.8x mais rápido).
    - `get_investments()`: de 10.9ms para 0.135ms (81.1x mais rápido).
    - `get_recurring_bills()`: de 11.6ms para 0.184ms (63.2x mais rápido).
    - `get_users()`: de 10.2ms para 0.083ms (122.0x mais rápido).
    - Invalidação automática após INSERT e DELETE validada com 100% de êxito.
  - Bateria completa de testes de regressão executada com 100% de aprovação (`teste_turso_cloud_completo.py`, `teste_fase1_sincronizacao_controlada.py`, `teste_fase2_alerta_vencimento.py`, `teste_fase7_evolucao_completa.py`).

---

## [Filtros Globais, Botão Flutuante e Chat Lateral de IA] - 2026-10-21 - Evolução de Usabilidade, Navegação e IA
- **Status:** Concluído com sucesso (100% testado, validado e documentado).
- **Ações Realizadas e Mudanças Arquiteturais:**
  1. **Padronização de Filtros de Pesquisa Globais (`frontend/components.py` e `frontend/views.py`):**
     - Criado o componente reutilizável `render_standard_period_filter(available_months, key_prefix, default_mode_index)`.
     - **Padrão Oficial do Sistema:** Por padrão, a aplicação e o Dashboard exibem agora os **dados gerais consolidados de todo o histórico**, oferecendo visão panorâmica total do patrimônio acumulado, receitas totais, despesas totais e balanço completo.
     - **Seletores Flexíveis:**
       - `🌐 Todo o Histórico (Geral)`: Consolidação de todos os lançamentos históricos com gráfico exclusivo de **Evolução Temporal Mensal** em Plotly.
       - `📅 Mês Específico`: Seletor direto de competência (`YYYY-MM`) com detecção automática de meses cadastrados e ordenação cronológica decrescente.
       - `📆 Período Personalizado (Calendário)`: Seletor intuitivo de intervalo com datas inicial e final via `st.date_input`, permitindo filtrar quinzenas, trimestres ou intervalos customizados com precisão diária.
     - Todas as métricas de cartões (`render_metric_card`), gráficos de pizza/donut, comparativos de barras e tabela de lançamentos adaptam-se instantaneamente ao filtro selecionado.
  2. **Reorganização Estrutural da Inteligência Artificial (Google Gemini):**
     - **Remoção da IA de Configurações:** A aba de consulta de IA foi completamente removida da página de configurações em `frontend/views.py`. A tela passou a se chamar `⚙️ Configurações & Perfil`, focando exclusivamente em Perfil Cadastral, Chave Gemini, Backup/Restauração de Banco, Segurança de Senhas e Gestão de Usuários.
     - **Botão Flutuante Fixo (FAB - Floating Action Button):** Criado o componente `render_floating_ai_assistant` em `frontend/components.py`. O botão flutuante é fixo no canto inferior direito (`position: fixed; bottom: 24px; right: 24px; z-index: 999999;`), com formato circular, gradiente executivo moderno (`#1f6feb` a `#238636`), animação de hover, sombra com brilho verde neon e microinterações táteis.
     - **Chat Lateral Deslizante (Drawer / Sidebar Dedicado):** Ao clicar no botão flutuante, abre-se um painel lateral deslizante à direita (`#ai-drawer-marker`, `width: 440px; height: 100vh; animation: drawerSlideInRight`). O drawer conta com:
       - Status da IA em tempo real (`🟢 Online (Gemini)`).
       - Botão explícito de fechar (`✖ Fechar`) e botão de limpar histórico (`🗑️ Limpar`).
       - Sugestões de perguntas rápidas através de botões/chips (Saldo Acumulado, Contas a Vencer, Maiores Gastos, Dicas para Poupar).
       - Histórico conversacional com avatares visuais (`👤` e `🤖`).
       - Input ágil com formulário limpo e responsivo.
     - **Regra de Fechamento Automático Mútuo:**
       - Quando o chat lateral de IA é aberto, o menu de navegação natural / sidebar principal da esquerda é **automaticamente ocultado/fechado** via CSS dinâmico (`section[data-testid="stSidebar"] { display: none !important; }`), eliminando qualquer sobreposição visual de painéis.
       - Quando o usuário clica em qualquer item de navegação no menu principal em `app.py`, o chat de IA é automaticamente fechado (`st.session_state["ai_chat_open"] = False`).
       - Ao fechar o chat lateral de IA pelo botão "✖", o menu de navegação da barra lateral é reaberto instantaneamente.
  3. **Camada de Inteligência e Fallback Multi-Modelo (`backend/utils.py`):**
     - A função `analyze_finances_with_ai` agora suporta `month_year="geral"` ou `None`, agregando todo o histórico financeiro consolidado quando solicitado.
     - Implementada a função conversacional `chat_with_financial_ai`, que alimenta o Google Gemini com o contexto financeiro em tempo real do usuário (saldo acumulado, histórico de receitas/despesas, contas pendentes, próximos vencimentos, maiores categorias e patrimônio investido).
     - Mecanismo de tentativas automáticas com atraso exponencial e fallback progressivo entre modelos (`gemini-3.8-flash` -> `gemini-2.5-flash` -> `gemini-2.0-flash` -> `gemini-1.5-flash`) contra picos de demanda (código 503/429).
  4. **Validação, Testes e Regra de Ouro:**
     - Criado o script `.agent/scripts_auxiliares/teste_filtros_e_ia_drawer.py`, validando a seleção de histórico consolidado, mês específico, datas e respostas do Gemini no drawer com 100% de sucesso.
     - Reexecutados os testes de regressão de performance e cache do Turso Cloud (`teste_performance_cache_turso.py`) e evolução completa (`teste_fase7_evolucao_completa.py`), todos aprovados com 100% de êxito.
     - Reforçada no topo deste documento a **Regra de Ouro Mandatória** obrigando qualquer IA ou desenvolvedor a ler integralmente este arquivo antes de alterar o código.

---

### 🛡️ Fase de Correção e Blindagem de Tipagem e Assinaturas (`backend/crud.py`)
- **Data e Horário:** 21/10/2026 (Ambiente Turso Cloud & Deploy Streamlit Cloud)
- **Status:** CONCLUÍDO COM 100% DE ÊXITO E VALIDAÇÃO VIA AST
- **Objetivo Técnico:**
  Eliminar inconsistências de assinaturas de métodos e avisos do analisador estático/linter identificados nas chamadas de funções do backend (`backend/crud.py`), garantindo tipagem PEP 484 precisa, suporte a argumentos adicionais (`**kwargs`), retrocompatibilidade total de parâmetros (`month_year` vs `year_month`, `force_manual`) e proteção em tempo de compilação e execução.
- **Detalhamento das Modificações:**
  1. **Blindagem e Padronização de `process_recurring_bills`:**
     - **Assinatura:** `def process_recurring_bills(year_month: Optional[str] = None, user_id: Optional[int] = None, force_manual: bool = False, month_year: Optional[str] = None, **kwargs: Any) -> int:`
     - Adicionado o parâmetro `force_manual: bool = False` para permitir o acionamento controlado pelo botão '⚡ Sincronizar Mês Vigente' em `frontend/views.py` e proteger contra execuções fora do dia 1 do mês em `app.py`.
     - Adicionada compatibilidade bidirecional entre `year_month` e `month_year` para que qualquer nomenclatura fornecida seja aceita sem erros de argumento desconhecido.
     - Suporte a chamadas posicionais com `user_id` no primeiro argumento.
  2. **Atualização e Tipagem Rigorosa de `get_transactions`:**
     - **Assinatura:** `def get_transactions(user_id: Optional[int] = None, trans_type: Optional[str] = None, status: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, category: Optional[str] = None, group_id: Optional[str] = None, search: Optional[str] = None, include_shared: bool = False, month_year: Optional[str] = None, year_month: Optional[str] = None, limit: Optional[int] = None, **kwargs: Any) -> List[Dict[str, Any]]:`
     - Adicionados explicitamente os parâmetros de filtro de competência `month_year: Optional[str] = None` e `year_month: Optional[str] = None`, permitindo buscas diretas por mês (`due_date LIKE 'YYYY-MM%'`) e limitador de registros (`limit`).
     - Adicionado `**kwargs: Any` para tolerância a argumentos extras em chamadas dinâmicas.
  3. **Blindagem de Outras Funções do Backend:**
     - `delete_transactions_by_month`: atualizada para aceitar tanto `year_month` quanto `month_year` e `**kwargs: Any`.
     - `get_recurring_bills`, `get_investments`, `get_budgets`: adicionados tipos explícitos (`Optional[...]`, `List[Dict[str, Any]]`) e `**kwargs: Any`.
     - `get_users`, `get_user_profile`: adicionada tipagem rigorosa de retorno e parâmetro de tolerância `**kwargs`.
  4. **Varredura Completa com Análise Sintática Abstrata (AST):**
     - Criado o script `.agent/scripts_auxiliares/verificar_assinaturas_crud.py` que analisou todas as 224 chamadas a funções do backend em 28 arquivos Python do projeto, certificando que **nenhuma** chamada possuía argumentos inválidos ou incompatíveis.
     - Criado o script `.agent/scripts_auxiliares/teste_verificacao_assinaturas_crud.py` que executou testes automatizados diretos sobre todas as assinaturas atualizadas (chamadas com `force_manual`, `month_year`, `year_month`, limites de dados, queries em cache e validações de erro), aprovado com 100% de sucesso.
     - Reexecutados com sucesso os testes de sincronização controlada (`teste_fase1_sincronizacao_controlada.py`), alerta de vencimentos (`teste_fase2_alerta_vencimento.py`) e diagnóstico de performance e cache do Turso Cloud (`teste_performance_cache_turso.py`).

---

### 🎨 Fase de Correção de Bugs Visuais, Restauração de Botões e Limpeza de Configurações
- **Data e Horário:** 21/10/2026 (Ambiente Turso Cloud & Deploy Streamlit Cloud)
- **Status:** CONCLUÍDO COM 100% DE ÊXITO E VALIDAÇÃO VISUAL/TÉCNICA
- **Objetivo Técnico:**
  Corrigir regressão visual na renderização dos botões do Streamlit (que estavam assumindo formato circular/pill gigante com texto cortado devido a vazamento de seletores CSS do botão flutuante de IA), restaurar o formato retangular elegante com cantos arredondados (`border-radius: 8px`), remover definitivamente a seção legada de "Chave de API do Gemini" da tela de Configurações & Perfil e otimizar o fechamento mútuo e alinhamento do chat lateral da IA.
- **Detalhamento das Modificações:**
  1. **Restauração Global de Estilização de Botões (`frontend/components.py`):**
     - Identificada a causa-raiz: o seletor `:has(> div #floating-ai-marker)` estava combinando com os blocos ancestrais do Streamlit, vazando `border-radius: 50% !important; width: 60px !important; height: 60px !important` para todos os botões do sistema.
     - Implementado seletor estritamente isolado via sibling adjacente `div[data-testid="element-container"]:has(#floating-ai-fab-anchor) + div[data-testid="element-container"]` e classe `.ai-fab-container / .ai-fab-button` com injeção de script de marcação imediata.
     - Definida a padronização global explícita para todos os botões do sistema (`div.stButton > button`, `div[data-testid="stFormSubmitButton"] > button`, `div[data-testid="stDownloadButton"] > button`, `[data-testid="stPopover"] > button`):
       - Formato retangular executivo com `border-radius: 8px !important`.
       - Padding equilibrado (`0.5rem 1rem !important`), altura mínima confortável (`min-height: 2.4rem !important`) e largura natural/responsiva (`width: auto`).
       - Diferenciação visual elegante entre botões primários (`#238636`, sombra verde) e secundários (`#21262d`, borda `#30363d`), ambos com micro-hover suave (`translateY(-1px)`).
  2. **Limpeza Definitiva da Página de Configurações (`frontend/views.py`):**
     - Removida completamente a seção legada "🔑 Chave de API do Gemini" (`GEMINI_API_KEY`) da tela `view_configuracoes_perfil`, uma vez que a chave de IA é gerida centralmente e a interação ocorre exclusivamente pelo FAB e Drawer lateral.
     - Renumeradas e reorganizadas as seções restantes:
       1. Perfil Cadastral (Nome Completo, Endereço e CPF)
       2. Backup & Restauração do Banco de Dados
       3. Segurança & Alteração de Senha
       4. Gestão de Usuários e Permissões (exclusivo para perfil Administrador)
  3. **Ajustes no Botão Flutuante e Drawer Lateral de IA (`frontend/components.py`):**
     - Isolamento rigoroso do painel lateral através de `.ai-drawer-panel` e `> div[data-testid="element-container"] #ai-drawer-anchor`.
     - Escondido automaticamente tanto o `section[data-testid="stSidebar"]` quanto o controle de recolhimento `button[data-testid="stSidebarCollapsedControl"]` enquanto o chat da IA estiver aberto.
     - Ajustada a tipografia, altura e quebra de texto dos botões de perguntas rápidas (chips) e do formulário de envio no chat lateral.

