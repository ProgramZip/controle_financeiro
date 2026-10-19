import os
import sys
import re
import csv
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')

MESES = {
    'janeiro': '01', 'fevereiro': '02', 'marco': '03', 'março': '03',
    'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07',
    'agosto': '08', 'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
}

def clean_amount(val_str):
    s = str(val_str).strip()
    # Verifica sinais negativos: hífen, minus sign unicode, en-dash, em-dash, parênteses
    is_neg = False
    if any(ch in s for ch in ['-', '−', '–', '—']):
        is_neg = True
    if s.startswith('(') and s.endswith(')'):
        is_neg = True
    
    # Remove R$, símbolos de moeda e caracteres não numéricos exceto vírgula e ponto
    clean = re.sub(r'[^\d,\.]', '', s)
    if not clean:
        return 0.0, False

    if ',' in clean and '.' in clean:
        if clean.rfind(',') > clean.rfind('.'):
            clean = clean.replace('.', '').replace(',', '.')
        else:
            clean = clean.replace(',', '')
    elif ',' in clean:
        clean = clean.replace(',', '.')
    
    try:
        val = abs(float(clean))
        return val, is_neg
    except:
        return 0.0, False

def classify(is_neg, text_bruto):
    t = text_bruto.lower()
    # 1. Se tem sinal negativo explícito
    if is_neg or any(ch in t for ch in ['−', '–', '—', '-r$']):
        return 'despesa'
    
    # 2. Palavras-chave de saída
    saidas = [
        'pix enviado', 'compra realizada', 'pagamento', 'guardado no cofrinho',
        'débito', 'debito', 'tarifa', 'transferência enviada', 'transferencia enviada',
        'ted enviada', 'doc enviado', 'saque', 'boleto', 'pgto', 'com saldo', 'com cartão'
    ]
    if any(k in t for k in saidas):
        return 'despesa'
    
    # 3. Palavras-chave de entrada
    entradas = [
        'pix recebido', 'depósito', 'deposito', 'salário', 'salario',
        'resgate', 'rendimento', 'transferência recebida', 'transferencia recebida',
        'ted recebida', 'doc recebido', 'reembolso', 'estorno'
    ]
    if any(k in t for k in entradas):
        return 'receita'
    
    if '+' in t:
        return 'receita'
        
    return 'despesa'

print("--- TESTANDO CSV DO PICPAY ---")
csv_path = "e:/controle_financeiro/.agent/teste/extrato-2026-08-01-2026-08-31.csv"
csv_rows = []
with open(csv_path, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for r in reader:
        v, is_neg = clean_amount(r['valor'])
        raw_full = f"{r.get('tipo', '')} {r.get('origem / destino', '')} {r.get('valor', '')}"
        tipo = classify(is_neg, raw_full)
        csv_rows.append((r['data'], raw_full, v, tipo))

print(f"Total lidos no CSV: {len(csv_rows)}")
desp_csv = sum(1 for r in csv_rows if r[3] == 'despesa')
rec_csv = sum(1 for r in csv_rows if r[3] == 'receita')
print(f"Despesas: {desp_csv} | Receitas: {rec_csv}")

print("\n--- TESTANDO PDF DO PICPAY ---")
pdf_path = "e:/controle_financeiro/.agent/teste/extrato-2026-08-01-2026-08-31.pdf"
pdf = pdfplumber.open(pdf_path)
pdf_trans = []
cur_date = "2026-08-01"

for p_idx, page in enumerate(pdf.pages):
    text = page.extract_text() or ""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m_date = re.search(r'(\d{1,2})\s+de\s+([a-zA-Zç]+)\s+(\d{4})', line, re.IGNORECASE)
        if m_date and 'saldo ao final' in line.lower():
            d, m_name, y = m_date.groups()
            m_num = MESES.get(m_name.lower(), '01')
            cur_date = f"{y}-{m_num}-{int(d):02d}"
            i += 1
            continue

        m_trans = re.search(r'^(\d{2}:\d{2})\s+(.*?)\s+([−–—+-]?\s*R\$\s*[\d\.,]+)$', line)
        if m_trans:
            hora, meio, val_str = m_trans.groups()
            desc = meio
            if i > 0 and not re.search(r'^\d{2}:\d{2}', lines[i-1]) and 'saldo' not in lines[i-1].lower() and 'hora tipo' not in lines[i-1].lower():
                desc = lines[i-1].strip() + ' ' + desc
            if i + 1 < len(lines) and not re.search(r'^\d{2}:\d{2}', lines[i+1]) and 'saldo' not in lines[i+1].lower() and 'documento emitido' not in lines[i+1].lower() and not re.search(r'\d{1,2}\s+de\s+[a-zA-Zç]+', lines[i+1]):
                desc = desc + ' ' + lines[i+1].strip()

            v, is_neg = clean_amount(val_str)
            tipo = classify(is_neg, f"{desc} {val_str}")
            pdf_trans.append((cur_date, desc, v, tipo))
        i += 1

print(f"Total lidos no PDF: {len(pdf_trans)}")
desp_pdf = sum(1 for r in pdf_trans if r[3] == 'despesa')
rec_pdf = sum(1 for r in pdf_trans if r[3] == 'receita')
print(f"Despesas: {desp_pdf} | Receitas: {rec_pdf}")
