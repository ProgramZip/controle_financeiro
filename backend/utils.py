import os
import io
import re
import csv
import uuid
import shutil
import sqlite3
import numpy as np
import pandas as pd
from PIL import Image
import cv2
import pdfplumber
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do .env na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = BASE_DIR / "financas.db"
UPLOADS_NOTAS_DIR = BASE_DIR / "uploads" / "notas"
UPLOADS_NOTAS_DIR.mkdir(parents=True, exist_ok=True)

# Lista oficial de categorias do sistema para mapeamento
CATEGORIAS_DESPESA = [
    "Alimentação", "Assinaturas", "Bares", "Restaurantes", "Casa", "Compras",
    "Contador", "Gastos Pessoais", "Dívidas e Empréstimos", "Educação", "Família",
    "Impostos e taxas", "Lazer e Hobbies", "Mercado", "Outros", "Pets",
    "Presentes e Doações", "Roupas", "Saúde", "Trabalho", "Transporte", "Viagem"
]

CATEGORIAS_RECEITA = [
    "Aluguéis", "Empréstimos", "Empresa", "Nota Fiscal Emitida",
    "Outras Receitas", "Salário"
]


# =====================================================================
# 1. LEITURA DE EXTRATOS BANCÁRIOS (CSV E PDF) COM PRÉ-CONCILIAÇÃO
# =====================================================================

def _suggest_category(description: str, trans_type: str) -> str:
    """Infere uma categoria provável a partir da descrição da transação."""
    desc = description.lower()
    if trans_type == "receita":
        if any(w in desc for w in ["salario", "folha", "ordenado", "remun"]):
            return "Salário"
        if any(w in desc for w in ["aluguel", "alugueis", "locacao"]):
            return "Aluguéis"
        if any(w in desc for w in ["empresa", "pj", "pro labore", "faturamento"]):
            return "Empresa"
        if any(w in desc for w in ["nf", "nota fiscal"]):
            return "Nota Fiscal Emitida"
        return "Outras Receitas"
    else:
        if any(w in desc for w in ["mercado", "supermercado", "hiper", "atacadao", "acougue", "hortifruti"]):
            return "Mercado"
        if any(w in desc for w in ["restaurante", "lanchonete", "ifood", "burger", "pizza", "subway", "mcdonald"]):
            return "Restaurantes"
        if any(w in desc for w in ["uber", "99", "combustivel", "gasolina", "posto", "estacionamento", "pedagio"]):
            return "Transporte"
        if any(w in desc for w in ["farmacia", "drogaria", "medico", "hospital", "clinica", "exame", "dentista"]):
            return "Saúde"
        if any(w in desc for w in ["netflix", "spotify", "amazon prime", "disney", "youtube", "assinatura"]):
            return "Assinaturas"
        if any(w in desc for w in ["aluguel", "condominio", "energia", "luz", "agua", "internet", "gas", "enel", "sabesp"]):
            return "Casa"
        if any(w in desc for w in ["bar", "choperia", "pub", "cerveja"]):
            return "Bares"
        if any(w in desc for w in ["pet", "veterinario", "racao", "cobasi", "petz"]):
            return "Pets"
        if any(w in desc for w in ["curso", "faculdade", "escola", "livro", "udemy"]):
            return "Educação"
        if any(w in desc for w in ["roupa", "calcado", "zara", "renner", "riachuelo", "shein"]):
            return "Roupas"
        return "Outros"


def _clean_amount(val) -> tuple[float, bool]:
    """
    Converte valores monetários em (float_positivo, is_negative).
    Detecta sinais negativos no início (-150, −150), fim (150-, 150−), 
    parênteses (150,00), -R$, −R$ ou indicador 'D'/'DÉBITO'.
    """
    if isinstance(val, (int, float)):
        f_val = float(val)
        return abs(f_val), f_val < 0

    s = str(val).strip()
    if not s:
        return 0.0, False

    is_neg = False
    # Detecta sinais negativos: ASCII '-', Unicode '−' (\u2212), en-dash '–' (\u2013), em-dash '—' (\u2014)
    # ou formatos como -R$, −R$, R$ -, (150,00), 150,00-
    if any(ch in s for ch in ["-", "−", "–", "—"]):
        is_neg = True
    elif s.startswith("(") and s.endswith(")"):
        is_neg = True
    elif re.search(r"\(\s*[\d\.,]+\s*\)", s):
        is_neg = True
    elif re.search(r"\b(D|DEB|DEBITO|DÉBITO)\b", s, re.IGNORECASE):
        is_neg = True

    # Limpeza de caracteres não numéricos exceto dígitos, vírgula e ponto
    clean_s = re.sub(r"[^\d,\.]", "", s)
    if not clean_s:
        return 0.0, False

    # Padrão brasileiro: 1.250,50 -> 1250.50
    if "," in clean_s and "." in clean_s:
        if clean_s.rfind(",") > clean_s.rfind("."):
            clean_s = clean_s.replace(".", "").replace(",", ".")
        else:
            clean_s = clean_s.replace(",", "")
    elif "," in clean_s:
        clean_s = clean_s.replace(",", ".")

    try:
        num = float(clean_s)
        return abs(num), is_neg
    except ValueError:
        return 0.0, False


def _classify_transaction_type(is_neg: bool, raw_text: str = "", type_indicator: str = None) -> str:
    """
    Lógica Rigorosa de Tipo (Despesa vs Receita):
    1. Se contiver sinal negativo (-, −, -R$, −R$, parênteses (valor)) OU se a linha/descrição 
       contiver palavras-chave de saída (Pix enviado, Compra realizada, Pagamento, 
       Guardado no cofrinho, Débito, Tarifa, Transferência enviada), o campo 'type' 
       DEVE ser obrigatoriamente classificado como 'despesa'.
    2. Apenas se o valor for positivo (+) E a descrição contiver palavras-chave de entrada 
       (Pix recebido, Depósito, Salário, Resgate, Dinheiro resgatado, Rendimento), 
       o campo 'type' deve ser classificado como 'receita'.
    """
    text_lower = f"{raw_text or ''} {type_indicator or ''}".lower()

    # 1. Regra Absoluta: Se o valor for negativo -> DESPESA
    if is_neg or any(neg_symbol in text_lower for neg_symbol in ["-r$", "−r$", "–r$", "—r$", "- r$", "− r$"]):
        return "despesa"

    # 2. Palavras-chave obrigatórias de Entrada (apenas para valores positivos)
    entrada_keywords = [
        "pix recebido", "deposito", "depósito", "salario", "salário",
        "resgate", "resgatado", "dinheiro resgatado", "rendimento", "transferencia recebida",
        "transferência recebida", "ted recebida", "doc recebido", "estorno credito",
        "reembolso", "pro labore", "remuneracao", "remuneração", "faturamento"
    ]
    if any(k in text_lower for k in entrada_keywords):
        return "receita"

    if any(k in (type_indicator or "").lower() for k in ["cred", "créd", "entrada", "in", "receb"]):
        return "receita"

    # 3. Palavras-chave obrigatórias de Saída
    saida_keywords = [
        "pix enviado", "compra realizada", "compra", "pagamento", "pgto",
        "guardado no cofrinho", "debito", "débito", "tarifa", "transferencia enviada",
        "transferência enviada", "ted enviada", "doc enviado", "boleto", "saque",
        "fatura", "recarga", "anuidade", "iof", "estorno debito",
        "ifood", "uber", "mercado", "farmacia", "posto"
    ]
    if any(k in text_lower for k in saida_keywords):
        return "despesa"

    # Se contiver '+' explícito sem nenhuma palavra de saída
    if "+" in text_lower:
        return "receita"

    # Fallback conservador para extratos comerciais sem indicador
    return "despesa"


def _parse_date(val) -> str:
    """Tenta converter strings de data para 'YYYY-MM-DD'."""
    s = str(val).strip()
    match = re.search(r"(\d{2})[/.-](\d{2})[/.-](\d{4})", s)
    if match:
        d, m, y = match.groups()
        return f"{y}-{m}-{d}"
    match_iso = re.search(r"(\d{4})[/.-](\d{2})[/.-](\d{2})", s)
    if match_iso:
        y, m, d = match_iso.groups()
        return f"{y}-{m}-{d}"
    match_short = re.search(r"(\d{2})[/.-](\d{2})", s)
    if match_short:
        d, m = match_short.groups()
        return f"{date.today().year}-{m}-{d}"
    return date.today().strftime("%Y-%m-%d")


def read_bank_statement_csv(file_bytes_or_buffer) -> pd.DataFrame:
    """
    Lê extrato bancário em CSV e retorna DataFrame padronizado:
    ['Data', 'Hora', 'Descrição', 'Valor', 'Tipo', 'Categoria_Sugerida', 'Selecionado']
    """
    if isinstance(file_bytes_or_buffer, bytes):
        buffer = io.BytesIO(file_bytes_or_buffer)
    else:
        buffer = file_bytes_or_buffer

    # Tenta detectar separador (, ou ;)
    sample = buffer.read(2048)
    buffer.seek(0)
    try:
        sample_str = sample.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            sample_str = sample.decode("utf-8")
        except UnicodeDecodeError:
            sample_str = sample.decode("latin1")
            buffer.seek(0)

    sep = ";" if sample_str.count(";") > sample_str.count(",") else ","

    try:
        df_raw = pd.read_csv(buffer, sep=sep, encoding="utf-8-sig")
    except Exception:
        buffer.seek(0)
        try:
            df_raw = pd.read_csv(buffer, sep=sep, encoding="utf-8")
        except Exception:
            buffer.seek(0)
            df_raw = pd.read_csv(buffer, sep=sep, encoding="latin1")

    # Mapeamento inteligente e rigoroso de colunas
    cols_norm = {c: str(c).lower().strip() for c in df_raw.columns}

    # 1. Coluna de Data
    date_col = next((c for c, n in cols_norm.items() if any(k in n for k in ["data", "date", "dia", "dt"])), df_raw.columns[0])

    # 2. Coluna dedicada de Hora
    time_col = next((c for c, n in cols_norm.items() if any(k in n for k in ["hora", "time", "hr"])), None)

    # 3. Coluna de Valor
    amount_col = next((c for c, n in cols_norm.items() if any(k in n for k in ["valor", "amount", "saldo", "lancamento", "montante"])), df_raw.columns[-1])

    # 4. Coluna de Tipo / Operação
    type_col = next((c for c, n in cols_norm.items() if any(k in n for k in ["tipo", "natureza", "operacao", "operação", "dc", "d/c", "indicador"])), None)

    # 5. Coluna de Origem / Destino / Favorecido
    dest_col = next((c for c, n in cols_norm.items() if any(k in n for k in ["origem", "destino", "favorecido", "estabelecimento", "titulo", "detalhe"])), None)

    # 6. Coluna de Descrição / Histórico (PROIBIDO usar Data, Hora ou Valor)
    cols_proibidas = {date_col, time_col, amount_col}
    candidatas_desc = [c for c in df_raw.columns if c not in cols_proibidas]

    desc_col = next((c for c in candidatas_desc if any(k in str(c).lower() for k in ["descri", "hist", "memo", "transacao", "transação", "identificador"])), None)
    if not desc_col:
        if dest_col and dest_col not in cols_proibidas:
            desc_col = dest_col
        else:
            candidatas_sem_tipo = [c for c in candidatas_desc if c != type_col]
            if candidatas_sem_tipo:
                desc_col = candidatas_sem_tipo[0]
            elif candidatas_desc:
                desc_col = candidatas_desc[0]
            else:
                desc_col = None

    rows = []
    for _, r in df_raw.iterrows():
        raw_val_str = str(r[amount_col]) if amount_col and pd.notna(r[amount_col]) else ""
        abs_amount, is_neg = _clean_amount(raw_val_str)
        if abs_amount == 0.0:
            continue

        raw_hora = str(r[time_col]).strip() if (time_col and pd.notna(r[time_col])) else ""
        raw_type = str(r[type_col]).strip() if (type_col and pd.notna(r[type_col])) else ""
        raw_dest = str(r[dest_col]).strip() if (dest_col and pd.notna(r[dest_col])) else ""
        raw_desc = str(r[desc_col]).strip() if (desc_col and desc_col != dest_col and pd.notna(r[desc_col])) else ""

        # Montagem rica e precisa da Descrição (Tipo + Favorecido / Origem / Detalhe)
        partes_desc = []
        if raw_type:
            partes_desc.append(raw_type)
        if raw_dest and raw_dest.lower() != raw_type.lower():
            partes_desc.append(raw_dest)
        if raw_desc and raw_desc.lower() != raw_dest.lower() and raw_desc.lower() != raw_type.lower():
            partes_desc.append(raw_desc)

        full_desc = " - ".join(partes_desc) if partes_desc else (raw_dest or raw_desc or raw_type or "Lançamento de Extrato")
        contexto_linha = f"{raw_type} {raw_dest} {raw_desc} {raw_val_str}"

        trans_type = _classify_transaction_type(is_neg, contexto_linha, raw_type)
        trans_date = _parse_date(r[date_col])
        cat = _suggest_category(full_desc, trans_type)

        rows.append({
            "Data": str(trans_date),
            "Hora": str(raw_hora),
            "Descrição": full_desc,
            "Valor": round(abs_amount, 2),
            "Tipo": trans_type,
            "Categoria_Sugerida": cat,
            "Selecionado": True
        })

    df_res = pd.DataFrame(rows)
    if not df_res.empty:
        df_res["Data"] = df_res["Data"].astype(str)
        df_res["Hora"] = df_res["Hora"].astype(str)
    else:
        df_res = pd.DataFrame(columns=["Data", "Hora", "Descrição", "Valor", "Tipo", "Categoria_Sugerida", "Selecionado"])
    return df_res


def read_bank_statement_pdf(file_bytes_or_buffer) -> pd.DataFrame:
    """
    Lê extrato bancário em PDF (suporta extratos tradicionais e bancos digitais como PicPay).
    Retorna DataFrame padronizado com 'Data' e 'Hora' em formato string.
    """
    if isinstance(file_bytes_or_buffer, bytes):
        buffer = io.BytesIO(file_bytes_or_buffer)
    else:
        buffer = file_bytes_or_buffer

    MESES_PT = {
        'janeiro': '01', 'fevereiro': '02', 'marco': '03', 'março': '03',
        'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07',
        'agosto': '08', 'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }

    rows = []
    with pdfplumber.open(buffer) as pdf:
        # Primeiro testa se há tabelas convencionais
        has_tables = False
        for page in pdf.pages[:2]:
            t = page.extract_tables()
            if t and len(t) > 0 and len(t[0]) > 2:
                has_tables = True
                break

        if has_tables:
            # Fluxo para extratos bancários em formato de tabela tradicional
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if len(table) > 1:
                        for row in table:
                            clean_row = [str(c).strip() for c in row if c is not None and str(c).strip()]
                            if len(clean_row) >= 3:
                                date_candidate = next((c for c in clean_row if re.search(r"\d{2}/\d{2}", c)), None)
                                num_candidate = next((c for c in clean_row if re.search(r"-?\d+[,.]\d{2}", c)), None)
                                if date_candidate and num_candidate:
                                    desc_parts = [c for c in clean_row if c != date_candidate and c != num_candidate]
                                    desc = " ".join(desc_parts) if desc_parts else "Movimentação PDF"
                                    abs_val, is_neg = _clean_amount(num_candidate)
                                    if abs_val != 0.0:
                                        t_type = _classify_transaction_type(is_neg, desc)
                                        rows.append({
                                            "Data": str(_parse_date(date_candidate)),
                                            "Hora": "",
                                            "Descrição": desc,
                                            "Valor": round(abs_val, 2),
                                            "Tipo": t_type,
                                            "Categoria_Sugerida": _suggest_category(desc, t_type),
                                            "Selecionado": True
                                        })
        else:
            # Fluxo para extratos de bancos digitais (PicPay, Nubank, etc.) baseado em texto e blocos diários
            cur_date = date.today().strftime("%Y-%m-%d")
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines = text.split("\n")
                i = 0
                while i < len(lines):
                    line = lines[i].strip()

                    # Cabeçalho de data por extenso (ex: "30 de agosto 2026 Saldo ao final do dia")
                    m_date = re.search(r'(\d{1,2})\s+de\s+([a-zA-Zç]+)\s+(\d{4})', line, re.IGNORECASE)
                    if m_date and any(w in line.lower() for w in ['saldo', 'extrato', 'período', 'periodo']):
                        d, m_name, y = m_date.groups()
                        m_num = MESES_PT.get(m_name.lower(), '01')
                        cur_date = f"{y}-{m_num}-{int(d):02d}"
                        i += 1
                        continue

                    # Cabeçalho de data em formato numérico (ex: "30/08/2026")
                    m_date_num = re.search(r'^(\d{2})[/.-](\d{2})[/.-](\d{4})', line)
                    if m_date_num:
                        cur_date = _parse_date(m_date_num.group(0))

                    # Linha de transação com hora e valor no final (ex: "17:39 Pix enviado Com saldo −R$ 10,00")
                    m_trans = re.search(r'^(\d{2}:\d{2})\s+(.*?)\s+([−–—+-]?\s*R\$\s*[\d\.,]+)$', line)
                    if m_trans:
                        hora, meio, val_str = m_trans.groups()
                        meio_clean = re.sub(r'\s+Com saldo.*$', '', meio).strip()

                        # Reconstitui linhas quebradas de favorecido acima e abaixo
                        fav_parts = []
                        if i > 0 and not re.search(r'^\d{2}:\d{2}', lines[i-1]) and 'saldo' not in lines[i-1].lower() and 'hora tipo' not in lines[i-1].lower():
                            fav_parts.append(lines[i-1].strip())
                        if i + 1 < len(lines) and not re.search(r'^\d{2}:\d{2}', lines[i+1]) and 'saldo' not in lines[i+1].lower() and 'documento emitido' not in lines[i+1].lower() and not re.search(r'\d{1,2}\s+de\s+[a-zA-Zç]+', lines[i+1]):
                            fav_parts.append(lines[i+1].strip())

                        fav_text = " ".join(fav_parts).strip()
                        if fav_text and meio_clean:
                            desc = f"{meio_clean} - {fav_text}"
                        else:
                            desc = meio_clean or fav_text or "Movimentação PDF"

                        abs_val, is_neg = _clean_amount(val_str)
                        if abs_val != 0.0:
                            t_type = _classify_transaction_type(is_neg, f"{desc} {val_str}", meio_clean)
                            rows.append({
                                "Data": str(cur_date),
                                "Hora": str(hora),
                                "Descrição": desc,
                                "Valor": round(abs_val, 2),
                                "Tipo": t_type,
                                "Categoria_Sugerida": _suggest_category(desc, t_type),
                                "Selecionado": True
                            })
                    i += 1

    df_res = pd.DataFrame(rows)
    if not df_res.empty:
        df_res["Data"] = df_res["Data"].astype(str)
        df_res["Hora"] = df_res["Hora"].astype(str)
    else:
        df_res = pd.DataFrame(columns=["Data", "Hora", "Descrição", "Valor", "Tipo", "Categoria_Sugerida", "Selecionado"])
    return df_res




# =====================================================================
# 2. NOTAS FISCAIS: SALVAMENTO E LEITURA DE QR CODE COM OPENCV
# =====================================================================

def save_invoice_image(uploaded_file_or_bytes, filename_prefix="nf") -> str:
    """
    Salva imagem da nota fiscal na pasta uploads/notas/ e retorna o caminho relativo salvo.
    """
    ext = "jpg"
    unique_name = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.{ext}"
    dest_path = UPLOADS_NOTAS_DIR / unique_name

    if isinstance(uploaded_file_or_bytes, bytes):
        img = Image.open(io.BytesIO(uploaded_file_or_bytes))
    elif hasattr(uploaded_file_or_bytes, "read"):
        img = Image.open(uploaded_file_or_bytes)
    else:
        raise ValueError("Formato de imagem inválido para salvar nota fiscal.")

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Salva com compressão adequada
    img.save(dest_path, "JPEG", quality=85)
    return f"uploads/notas/{unique_name}"


def decode_qr_code(image_path_or_bytes) -> str:
    """
    Decodifica QR Code da imagem da nota fiscal via OpenCV (opencv-python-headless).
    Retorna a string do QR Code (URL da NFC-e, etc.) ou None se não encontrado.
    """
    try:
        if isinstance(image_path_or_bytes, (str, Path)):
            full_path = BASE_DIR / image_path_or_bytes if not Path(image_path_or_bytes).is_absolute() else Path(image_path_or_bytes)
            if not full_path.exists():
                return None
            img = cv2.imread(str(full_path))
        elif isinstance(image_path_or_bytes, bytes):
            nparr = np.frombuffer(image_path_or_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif hasattr(image_path_or_bytes, "read"):
            data = image_path_or_bytes.read()
            if hasattr(image_path_or_bytes, "seek"):
                image_path_or_bytes.seek(0)
            nparr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            return None

        if img is None:
            return None

        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        if data:
            return data.strip()

        # Tentativa secundária com conversão para escala de cinza e equalização
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        data, bbox, _ = detector.detectAndDecode(gray)
        if data:
            return data.strip()

        return None
    except Exception as e:
        print(f"Erro ao decodificar QR Code: {e}")
        return None


# =====================================================================
# 3. BACKUP, RESTAURAÇÃO E EXPORTAÇÃO EXCEL
# =====================================================================

def get_db_backup_bytes() -> bytes:
    """Lê o banco de dados financas.db e retorna os bytes para download."""
    if not DB_PATH.exists():
        return b""
    with open(DB_PATH, "rb") as f:
        return f.read()


def restore_db_from_bytes(uploaded_bytes: bytes) -> tuple[bool, str]:
    """
    Restaura o banco financas.db a partir dos bytes de upload.
    Realiza teste de integridade antes de confirmar a substituição.
    """
    if not uploaded_bytes:
        return False, "Arquivo vazio fornecido."

    temp_path = BASE_DIR / "financas_temp_restore.db"
    backup_existing_path = BASE_DIR / "financas_pre_restore.bak"

    try:
        # Grava temporário
        with open(temp_path, "wb") as f:
            f.write(uploaded_bytes)

        # Testa integridade do SQLite
        conn = sqlite3.connect(temp_path)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        check_result = cur.fetchone()
        conn.close()

        if not check_result or check_result[0] != "ok":
            if temp_path.exists():
                temp_path.unlink()
            return False, "Arquivo de banco SQLite corrompido ou inválido."

        # Cria cópia de segurança do atual se existir
        if DB_PATH.exists():
            shutil.copy2(DB_PATH, backup_existing_path)

        # Move o arquivo restaurado para a posição oficial
        shutil.move(temp_path, DB_PATH)
        return True, "Banco de dados restaurado com sucesso!"
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        if backup_existing_path.exists() and not DB_PATH.exists():
            shutil.copy2(backup_existing_path, DB_PATH)
        return False, f"Falha ao restaurar banco: {str(e)}"


def export_transactions_to_excel(transactions: list) -> bytes:
    """
    Exporta a lista de transações para uma planilha Excel estilizada (.xlsx) em memória.
    Retorna os bytes prontos para st.download_button.
    """
    output = io.BytesIO()

    if not transactions:
        df = pd.DataFrame(columns=[
            "ID", "Tipo", "Categoria", "Descrição", "Valor (R$)",
            "Forma Pagamento", "Parcela Atual", "Total Parcelas",
            "Data Vencimento", "Status", "Recorrente", "Criado Em"
        ])
    else:
        records = []
        for t in transactions:
            records.append({
                "ID": t.get("id"),
                "Tipo": t.get("type", "").capitalize(),
                "Categoria": t.get("category"),
                "Descrição": t.get("description"),
                "Valor (R$)": t.get("amount"),
                "Forma Pagamento": t.get("payment_method"),
                "Parcela Atual": t.get("installment_current"),
                "Total Parcelas": t.get("installment_total"),
                "Data Vencimento": t.get("due_date"),
                "Status": t.get("status"),
                "Recorrente": "Sim" if t.get("is_recurring") else "Não",
                "Criado Em": t.get("created_at")
            })
        df = pd.DataFrame(records)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Movimentações")

    output.seek(0)
    return output.getvalue()


# =====================================================================
# 4. CONSULTOR FINANCEIRO IA COM GEMINI (google-genai)
# =====================================================================

def analyze_finances_with_ai(
    month_year: str,
    transactions: list,
    budgets: list = None,
    user_question: str = None
) -> str:
    """
    Analisa os gastos reais do mês utilizando o SDK oficial google-genai.
    Gera diagnóstico financeiro, alertas de orçamento e recomendações personalizadas.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        try:
            import streamlit as st
            api_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
        except Exception:
            pass

    if not api_key or api_key == "sua_chave_aqui":
        return (
            "⚠️ **Chave do Gemini não configurada!**\n\n"
            "Para utilizar o Consultor Financeiro IA, configure sua chave no arquivo `.env` "
            "(`GEMINI_API_KEY=\"sua_chave\"`), nos Secrets do Streamlit Cloud ou na aba de Configurações do sistema."
        )

    try:
        from google import genai
    except ImportError:
        return "❌ Pacote `google-genai` não encontrado no ambiente virtual."

    # Agregação dos dados do mês
    month_trans = [t for t in transactions if str(t.get("due_date", ""))[:7] == month_year]
    total_despesas = sum(t["amount"] for t in month_trans if t.get("type") == "despesa")
    total_receitas = sum(t["amount"] for t in month_trans if t.get("type") == "receita")
    saldo = total_receitas - total_despesas

    despesas_pagas = sum(t["amount"] for t in month_trans if t.get("type") == "despesa" and t.get("status") == "Pago")
    despesas_pendentes = sum(t["amount"] for t in month_trans if t.get("type") == "despesa" and t.get("status") == "Pendente")

    # Agrupamento por categoria
    cat_gastos = {}
    for t in month_trans:
        if t.get("type") == "despesa":
            c = t.get("category", "Outros")
            cat_gastos[c] = cat_gastos.get(c, 0.0) + t["amount"]

    # Comparativo de orçamentos
    budget_map = {b["category"]: b["monthly_limit"] for b in (budgets or [])}
    comparativo_orcamento = []
    for cat, gasto in cat_gastos.items():
        limite = budget_map.get(cat)
        if limite:
            pct = (gasto / limite) * 100
            comparativo_orcamento.append(f"- **{cat}**: Gasto R$ {gasto:.2f} de teto R$ {limite:.2f} ({pct:.1f}%)" + (" 🚨 ESTOURO!" if gasto > limite else ""))

    prompt = f"""
Você é um Consultor Financeiro Pessoal Sênior e Estrategista de Patrimônio.
Analise os dados financeiros reais do mês {month_year} detalhados abaixo:

### RESUMO GERAL DO MÊS ({month_year}):
- Receita Total: R$ {total_receitas:,.2f}
- Despesa Total: R$ {total_despesas:,.2f}
- Saldo Previsto: R$ {saldo:,.2f}
- Despesas Quitadas: R$ {despesas_pagas:,.2f}
- Despesas Pendentes: R$ {despesas_pendentes:,.2f}

### GASTOS POR CATEGORIA:
{chr(10).join([f"- {cat}: R$ {val:,.2f}" for cat, val in sorted(cat_gastos.items(), key=lambda x: x[1], reverse=True)]) or "Nenhum gasto registrado neste mês."}

### STATUS DOS LIMITES DE ORÇAMENTO:
{chr(10).join(comparativo_orcamento) if comparativo_orcamento else "Nenhum teto de orçamento cadastrado para as categorias gastas."}

### INSTRUÇÕES:
1. Forneça um diagnóstico direto e objetivo da saúde financeira deste mês.
2. Destaque pontos de atenção crítica (categorias que mais pesaram ou orçamentos estourados).
3. Sugira 3 ações práticas e imediatas de corte ou otimização para poupar mais.
4. Mantenha um tom profissional, encorajador e consultivo em formato Markdown legível.
"""
    if user_question:
        prompt += f"\n\nPergunta adicional do usuário: {user_question}"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"⚠️ Erro ao consultar o modelo Gemini: {str(e)}"
