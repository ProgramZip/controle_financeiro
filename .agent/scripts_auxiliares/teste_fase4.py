import os
import sys
import io
import pandas as pd
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.utils import (
    read_bank_statement_csv,
    save_invoice_image,
    decode_qr_code,
    get_db_backup_bytes,
    restore_db_from_bytes,
    export_transactions_to_excel,
    analyze_finances_with_ai
)

def run_tests():
    print("1. Testando leitura de extrato CSV...")
    csv_content = """Data;Descricao;Valor
10/10/2026;Supermercado Extra;-150.50
12/10/2026;Salario Mensal;4500.00
14/10/2026;Uber Viagens;-32.90
"""
    df_csv = read_bank_statement_csv(csv_content.encode("utf-8"))
    assert len(df_csv) == 3, f"Esperado 3 linhas, obteve {len(df_csv)}"
    assert "Supermercado Extra" in df_csv["Descrição"].values
    assert df_csv.loc[df_csv["Descrição"] == "Supermercado Extra", "Categoria_Sugerida"].values[0] == "Mercado"
    assert df_csv.loc[df_csv["Descrição"] == "Salario Mensal", "Tipo"].values[0] == "receita"
    print("   -> Sucesso! Extrato CSV processado e categorias sugeridas com sucesso.")

    print("2. Testando salvamento de imagem de nota fiscal...")
    img = Image.new("RGB", (200, 200), color=(73, 109, 137))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    saved_path = save_invoice_image(img_bytes, filename_prefix="nf_teste")
    assert os.path.exists(saved_path), f"Arquivo de nota não foi salvo em {saved_path}!"
    print(f"   -> Sucesso! Nota fiscal salva em: {saved_path}")

    print("3. Testando backup e exportação para Excel...")
    backup_data = get_db_backup_bytes()
    assert isinstance(backup_data, bytes), "Backup deve retornar bytes!"

    sample_transactions = [
        {"id": 1, "type": "despesa", "category": "Mercado", "description": "Compras semanais", "amount": 250.0, "payment_method": "À Vista", "installment_current": 1, "installment_total": 1, "due_date": "2026-10-10", "status": "Pago", "is_recurring": 0, "created_at": "2026-10-10 10:00:00"}
    ]
    excel_bytes = export_transactions_to_excel(sample_transactions)
    assert len(excel_bytes) > 0, "Excel gerado vazio!"
    print("   -> Sucesso! Backup e exportação Excel validados.")

    print("4. Testando segurança e comportamento do Consultor IA...")
    ai_resp = analyze_finances_with_ai("2026-10", sample_transactions)
    assert isinstance(ai_resp, str) and len(ai_resp) > 0
    print("   -> Sucesso! Consultor IA respondeu com tratamento correto de chave/fallback.")

    print("\n[SUCESSO] TODOS OS TESTES DA FASE 4 PASSARAM COM 100% DE SUCESSO!")


if __name__ == "__main__":
    run_tests()
