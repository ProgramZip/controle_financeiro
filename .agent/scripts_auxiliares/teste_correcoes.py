import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.utils import read_bank_statement_csv, read_bank_statement_pdf, _clean_amount, _classify_transaction_type
import frontend.components
import frontend.views

def test_corrections():
    print("==================================================")
    print("1. Testando _clean_amount para múltiplos formatos...")
    print("==================================================")
    v1, neg1 = _clean_amount("-150.00")
    assert v1 == 150.0 and neg1 is True, f"Falha no -150.00: {v1}, {neg1}"

    v2, neg2 = _clean_amount("250,50-")
    assert v2 == 250.50 and neg2 is True, f"Falha no 250,50-: {v2}, {neg2}"

    v3, neg3 = _clean_amount("(350,00)")
    assert v3 == 350.0 and neg3 is True, f"Falha no (350,00): {v3}, {neg3}"

    v4, neg4 = _clean_amount("1.250,00 D")
    assert v4 == 1250.0 and neg4 is True, f"Falha no 1.250,00 D: {v4}, {neg4}"

    v5, neg5 = _clean_amount("−R$ 10,00")  # Unicode minus \u2212
    assert v5 == 10.0 and neg5 is True, f"Falha no −R$ 10,00: {v5}, {neg5}"

    v6, neg6 = _clean_amount("+R$ 130,00")
    assert v6 == 130.0 and neg6 is False, f"Falha no +R$ 130,00: {v6}, {neg6}"

    print("   -> Sucesso! _clean_amount identifica todos os formatos numéricos e sinais.")

    print("\n==================================================")
    print("2. Testando classificação de Despesa vs Receita...")
    print("==================================================")
    # Valor negativo -> Despesa
    assert _classify_transaction_type(True, "Qualquer coisa") == "despesa"
    # Palavras de saída obrigatórias -> Despesa
    assert _classify_transaction_type(False, "Pix enviado para Joao") == "despesa"
    assert _classify_transaction_type(False, "TED enviada banco") == "despesa"
    assert _classify_transaction_type(False, "Compra realizada Rio Sul") == "despesa"
    assert _classify_transaction_type(False, "Guardado no cofrinho") == "despesa"
    assert _classify_transaction_type(False, "Pagamento de boleto") == "despesa"
    assert _classify_transaction_type(False, "Tarifa de conta") == "despesa"

    # Palavras de entrada com positivo -> Receita
    assert _classify_transaction_type(False, "Pix recebido de Maria") == "receita"
    assert _classify_transaction_type(False, "Salario referente ao mes") == "receita"
    assert _classify_transaction_type(False, "Deposito em dinheiro") == "receita"
    assert _classify_transaction_type(False, "Rendimento de aplicacao") == "receita"
    assert _classify_transaction_type(False, "Dinheiro resgatado") == "receita"
    print("   -> Sucesso! Lógica rigorosa de classificação validada.")

    print("\n==================================================")
    print("3. Validando arquivos reais da pasta .agent/teste/...")
    print("==================================================")
    base_teste = os.path.abspath(os.path.join(os.path.dirname(__file__), "../teste"))
    csv_path = os.path.join(base_teste, "extrato-2026-08-01-2026-08-31.csv")
    pdf_path = os.path.join(base_teste, "extrato-2026-08-01-2026-08-31.pdf")

    with open(csv_path, "rb") as f:
        df_csv = read_bank_statement_csv(f.read())
    
    with open(pdf_path, "rb") as f:
        df_pdf = read_bank_statement_pdf(f.read())

    print(f"   CSV: {len(df_csv)} linhas | Despesas: {(df_csv['Tipo'] == 'despesa').sum()} | Receitas: {(df_csv['Tipo'] == 'receita').sum()}")
    print(f"   PDF: {len(df_pdf)} linhas | Despesas: {(df_pdf['Tipo'] == 'despesa').sum()} | Receitas: {(df_pdf['Tipo'] == 'receita').sum()}")

    assert len(df_csv) == 92, f"Esperado 92 no CSV, obteve {len(df_csv)}"
    assert len(df_pdf) == 92, f"Esperado 92 no PDF, obteve {len(df_pdf)}"
    assert (df_csv["Tipo"] == "despesa").sum() == 67
    assert (df_csv["Tipo"] == "receita").sum() == 25
    assert (df_pdf["Tipo"] == "despesa").sum() == 67
    assert (df_pdf["Tipo"] == "receita").sum() == 25
    assert (df_csv["Valor"] > 0).all()
    assert (df_pdf["Valor"] > 0).all()

    # Validação estrita da coluna Hora e Descrição
    assert "Hora" in df_csv.columns, "Coluna 'Hora' ausente no CSV"
    assert "Hora" in df_pdf.columns, "Coluna 'Hora' ausente no PDF"
    assert df_csv["Hora"].iloc[0] == "17:39", f"Hora incorreta no CSV: {df_csv['Hora'].iloc[0]}"
    assert df_pdf["Hora"].iloc[0] == "17:39", f"Hora incorreta no PDF: {df_pdf['Hora'].iloc[0]}"
    
    # Validação de que Descrição NÃO é a hora e contém o favorecido/origem
    assert "17:39" not in df_csv["Descrição"].iloc[0], "Hora não pode estar na Descrição do CSV"
    assert "Camilla Fernandes" in df_csv["Descrição"].iloc[0], "Descrição deve conter o favorecido no CSV"
    assert "Camilla Fernandes" in df_pdf["Descrição"].iloc[0], "Descrição deve conter o favorecido no PDF"

    # Validação do componente modal_nova_conta_recorrente
    assert hasattr(frontend.components, "modal_nova_conta_recorrente"), "modal_nova_conta_recorrente ausente em components"

    print("   -> Perfeito! Coluna 'Hora' dedicada e isolada, 'Descrição' com favorecido real, 100% de paridade (67 despesas e 25 receitas).")

if __name__ == "__main__":
    test_corrections()
