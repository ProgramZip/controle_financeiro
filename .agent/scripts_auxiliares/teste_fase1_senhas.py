import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db, verify_user, hash_password, update_user_password, change_password_with_verification
from backend.crud import (
    get_users, add_user, change_user_password, admin_set_user_password, delete_user
)

def run_tests():
    print("Iniciando testes da Fase 1: Segurança e Credenciais (Alteração de Senha)...")
    init_db()

    # 1. Obter usuário admin
    admin = verify_user("admin", "admin123")
    if not admin:
        # Se a senha do admin já foi modificada ou é diferente, busca o usuário pelo ID
        users = get_users()
        admin = next((u for u in users if u["username"] == "admin"), None)
        assert admin is not None, "Usuário admin não encontrado."
        # Garante senha conhecida para o teste
        update_user_password(admin["id"], "admin123")
        admin = verify_user("admin", "admin123")

    assert admin is not None, "Falha ao verificar usuário admin."
    print("  [OK] Usuário admin verificado.")

    # 2. Criar usuário de teste temporário
    test_user_name = "usuario_teste_fase1"
    # Se já existir, remove
    users = get_users()
    existing = next((u for u in users if u["username"] == test_user_name), None)
    if existing:
        delete_user(existing["id"])

    test_uid = add_user(test_user_name, "senhaAntiga1", role="editor")
    assert test_uid is not None, "Falha ao criar usuário de teste."
    print("  [OK] Usuário temporário criado com sucesso.")

    # 3. Testar troca de senha com senha atual incorreta
    ok, msg = change_user_password(test_uid, "senhaErrada", "novaSenha123")
    assert not ok, "Troca de senha deveria ter falhado com senha atual errada."
    assert "incorreta" in msg.lower(), f"Mensagem inesperada: {msg}"
    print("  [OK] Bloqueio correto de senha atual incorreta.")

    # 4. Testar troca de senha com nova senha curta
    ok, msg = change_user_password(test_uid, "senhaAntiga1", "12")
    assert not ok, "Troca de senha deveria ter falhado com senha curta."
    print("  [OK] Bloqueio correto de senha com menos de 4 caracteres.")

    # 5. Testar troca de senha válida pelo próprio usuário
    ok, msg = change_user_password(test_uid, "senhaAntiga1", "novaSenhaSegura456")
    assert ok, f"Falha na troca legítima de senha: {msg}"
    print("  [OK] Alteração de senha própria com sucesso.")

    # 6. Validar que login antigo falha e novo funciona
    assert verify_user(test_user_name, "senhaAntiga1") is None, "Senha antiga ainda está válida!"
    user_logado = verify_user(test_user_name, "novaSenhaSegura456")
    assert user_logado is not None and user_logado["id"] == test_uid, "Falha no login com a nova senha."
    print("  [OK] Login com nova senha validado no SQLite.")

    # 7. Testar redefinição de senha pelo Admin
    ok, msg = admin_set_user_password(admin["id"], test_uid, "senhaResetadaPeloAdmin99")
    assert ok, f"Falha na redefinição pelo admin: {msg}"
    assert verify_user(test_user_name, "senhaResetadaPeloAdmin99") is not None, "Login com senha resetada pelo admin falhou."
    print("  [OK] Redefinição de senha de terceiros pelo Admin validada.")

    # 8. Testar que usuário comum não pode usar função de admin
    ok, msg = admin_set_user_password(test_uid, admin["id"], "tentativaHacker")
    assert not ok, "Usuário editor não pode redefinir senha via admin_set_user_password."
    print("  [OK] Bloqueio de autorização para não-admins validado.")

    # 9. Testar alteração de senha do próprio admin
    ok, msg = change_user_password(admin["id"], "admin123", "adminNovaSenha789")
    assert ok, f"Admin deveria conseguir alterar sua própria senha: {msg}"
    assert verify_user("admin", "adminNovaSenha789") is not None, "Login do admin com nova senha falhou."
    # Restaurar senha admin para padrão de desenvolvimento
    update_user_password(admin["id"], "admin123")
    print("  [OK] Alteração e restauração da senha do administrador validada.")

    # Limpeza
    delete_user(test_uid)
    print("  [OK] Limpeza de usuário de teste concluída.")

    print("\nTODOS OS TESTES DA FASE 1 PASSARAM COM 100% DE SUCESSO!")

if __name__ == "__main__":
    run_tests()
