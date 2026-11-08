from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from accounts.models import AdminAuditLog

User = get_user_model()


class CadastroTests(APITestCase):
    def test_cadastro_cria_usuario_e_perfil(self):
        response = self.client.post(
            "/api/auth/cadastro/",
            {
                "username": "novo_membro",
                "email": "novo@example.com",
                "password": "UmaSenha-Forte-2026!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        usuario = User.objects.get(username="novo_membro")
        self.assertTrue(usuario.check_password("UmaSenha-Forte-2026!"))
        self.assertTrue(hasattr(usuario, "perfil"))

    def test_cadastro_rejeita_senha_fraca(self):
        response = self.client.post(
            "/api/auth/cadastro/",
            {
                "username": "senha_fraca",
                "email": "fraca@example.com",
                "password": "123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="senha_fraca").exists())

    def test_perfil_privado_exige_autenticacao(self):
        response = self.client.get("/api/auth/perfil/")
        self.assertEqual(response.status_code, 401)


class PlatformAdminDashboardTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="platform_admin", email="admin@example.com",
            password="UmaSenha-Forte-2026!"
        )
        self.member = User.objects.create_user(
            username="membro_teste", email="membro@example.com",
            password="UmaSenha-Forte-2026!"
        )

    def test_dashboard_exige_admin_global(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get("/api/auth/platform-admin/overview/")
        self.assertEqual(response.status_code, 403)

    def test_admin_global_consulta_indicadores(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/auth/platform-admin/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["usuarios_total"], 2)
        self.assertEqual(response.data["usuarios_ativos"], 2)

    def test_admin_global_bloqueia_usuario_comum(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/auth/platform-admin/users/{self.member.pk}/status/",
            {"is_active": False},
            format="json",
        )
        self.member.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.member.is_active)

    def test_admin_global_reativa_usuario_comum(self):
        self.member.is_active = False
        self.member.save(update_fields=["is_active"])
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/auth/platform-admin/users/{self.member.pk}/status/",
            {"is_active": True},
            format="json",
        )
        self.member.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.member.is_active)

    def test_admin_global_nao_pode_bloquear_a_propria_conta(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/auth/platform-admin/users/{self.admin.pk}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_global_nao_pode_bloquear_outro_superuser(self):
        outro_admin = User.objects.create_superuser(
            username="outro_admin", email="outro-admin@example.com",
            password="UmaSenha-Forte-2026!"
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/auth/platform-admin/users/{outro_admin.pk}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_global_lista_usuarios(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/auth/platform-admin/users/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertTrue(any(u["username"] == "membro_teste" for u in response.data["results"]))

    def test_bloqueio_de_usuario_gera_registro_de_auditoria(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/auth/platform-admin/users/{self.member.pk}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        log = AdminAuditLog.objects.get(entidade="usuario", entidade_id=str(self.member.pk))
        self.assertEqual(log.ator, self.admin)
        self.assertEqual(log.acao, "usuario_bloqueado")

    def test_historico_de_auditoria_e_restrito_ao_admin_global(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get("/api/auth/platform-admin/audit/")
        self.assertEqual(response.status_code, 403)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/auth/platform-admin/audit/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
