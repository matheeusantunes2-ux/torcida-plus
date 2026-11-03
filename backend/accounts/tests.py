from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

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
