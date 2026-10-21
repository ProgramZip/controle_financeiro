import ast
import inspect
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import backend.crud as crud

def main():
    crud_funcs = {name: func for name, func in inspect.getmembers(crud, inspect.isfunction)}
    print(f"Total de funções em backend.crud: {len(crud_funcs)}")

    target_dirs = [
        root_dir / "app.py",
        root_dir / "frontend",
        root_dir / "backend",
        root_dir / ".agent" / "scripts_auxiliares"
    ]

    files_to_check = []
    for item in target_dirs:
        if item.is_file() and item.suffix == ".py":
            files_to_check.append(item)
        elif item.is_dir():
            files_to_check.extend(item.rglob("*.py"))

    print(f"Arquivos Python a verificar: {len(files_to_check)}")

    total_calls_checked = 0
    errors = []

    for py_file in files_to_check:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))
        except Exception as e:
            errors.append(f"Erro ao parsear {py_file}: {e}")
            continue

        # Look for imported names from backend.crud
        imported_crud_funcs = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and (node.module == "backend.crud" or node.module.endswith(".crud")):
                    for alias in node.names:
                        orig = alias.name
                        asname = alias.asname or orig
                        if orig in crud_funcs:
                            imported_crud_funcs[asname] = orig

        # Walk AST to find calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    if node.func.id in imported_crud_funcs:
                        func_name = imported_crud_funcs[node.func.id]
                    elif node.func.id in crud_funcs:
                        func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in crud_funcs:
                        # e.g., crud.get_transactions(...)
                        func_name = node.func.attr

                if func_name and func_name in crud_funcs:
                    total_calls_checked += 1
                    func_obj = crud_funcs[func_name]
                    # Check inspect signature
                    try:
                        sig = inspect.signature(func_obj)
                        # We know args count and kwargs
                        kw_keys = [kw.arg for kw in node.keywords if kw.arg is not None]
                        pos_count = len(node.args)
                        has_kwargs = any(kw.arg is None for kw in node.keywords) # e.g. **kwargs
                        
                        # Check kwargs against signature parameters if not has_kwargs and not sig has VAR_KEYWORD (**kwargs)
                        has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
                        
                        if not has_var_keyword and not has_kwargs:
                            for kw in kw_keys:
                                if kw not in sig.parameters:
                                    errors.append(
                                        f"[{py_file.name}:{node.lineno}] Chamada a '{func_name}' com argumento desconhecido: '{kw}'"
                                    )
                    except Exception as sig_err:
                        # e.g. Streamlit cache wrapper
                        pass

    print(f"Total de chamadas a funções do crud analisadas: {total_calls_checked}")
    if errors:
        print(f"ENCONTRADOS {len(errors)} ERRO(S):")
        for err in errors:
            print("  ❌", err)
        sys.exit(1)
    else:
        print("✅ NENHUM erro de argumento incompatível encontrado!")

if __name__ == "__main__":
    main()
