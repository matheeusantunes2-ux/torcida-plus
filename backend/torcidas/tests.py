from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Membro, Torcida

User = get_user_model()


class IsolamentoTorcidasTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_teste", password="Senha-Forte-2026!"
        )
        self.outro = User.objects.create_user(
            username="outro_teste", password="Senha-Forte-2026!"
        )
        self.torcida = Torcida.objects.create(
            nome="Torcida Teste", slug="torcida-teste"
        )
        Membro.objects.create(
            usuario=self.admin, torcida=self.torcida, papel="admin"
        )

    def test_usuario_nao_membro_nao_lista_torcida(self):
        self.client.force_authenticate(user=self.outro)
        response = self.client.get(f"/api/torcidas/{self.torcida.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_usuario_nao_membro_nao_pode_listar_membros(self):
        self.client.force_authenticate(user=self.outro)
        response = self.client.get(
            f"/api/torcidas/{self.torcida.pk}/membros/"
        )
        self.assertEqual(response.status_code, 404)

    def test_membro_pode_consultar_torcida(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/torcidas/{self.torcida.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_anomino_nao_pode_criar_torcida(self):
        response = self.client.post(
            "/api/torcidas/",
            {
                "nome": "Nova Torcida",
                "slug": "nova-torcida",
                "cor_principal": "#202020",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)
