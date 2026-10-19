import os
import sys
import py_compile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def test_syntax_and_imports():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    app_file = os.path.join(root, "app.py")
    views_file = os.path.join(root, "frontend", "views.py")

    print("1. Compilando sintaxe de app.py e frontend/views.py...")
    py_compile.compile(app_file, doraise=True)
    py_compile.compile(views_file, doraise=True)
    print("   -> Sucesso! Sintaxe 100% válida.")

    print("2. Testando importação dos módulos...")
    import frontend.views as v
    assert hasattr(v, "view_dashboard")
    assert hasattr(v, "view_movimentacoes")
    assert hasattr(v, "view_contas_mensais")
    assert hasattr(v, "view_importacao_extratos")
    assert hasattr(v, "view_investimentos_orcamentos")
    assert hasattr(v, "view_consultor_configuracoes")
    print("   -> Sucesso! Todas as 6 views importadas com sucesso.")

    print("\n[SUCESSO] TODOS OS TESTES DA FASE 6 PASSARAM COM 100% DE SUCESSO!")

if __name__ == "__main__":
    test_syntax_and_imports()
