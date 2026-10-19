import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def test_imports():
    try:
        import frontend.components as comp
        assert hasattr(comp, "apply_custom_css")
        assert hasattr(comp, "render_metric_card")
        assert hasattr(comp, "modal_nova_movimentacao")
        print("[SUCESSO] frontend/components.py importado e validado com sucesso!")
    except Exception as e:
        print(f"[ERRO] Falha ao importar frontend/components.py: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_imports()
