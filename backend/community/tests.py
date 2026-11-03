from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from torcidas.models import Membro, Torcida
from .models import Publicacao

User = get_user_model()


class IsolamentoPublicacoesTests(APITestCase):
    def setUp(self):
        self.autor = User.objects.create_user(
            username="autor_teste", password="Senha-Forte-2026!"
        )
        self.estranho = User.objects.create_user(
            username="estranho_teste", password="Senha-Forte-2026!"
        )
        self.torcida = Torcida.objects.create(
            nome="Comunidade Teste", slug="comunidade-teste"
        )
        Membro.objects.create(
            usuario=self.autor, torcida=self.torcida, papel="admin"
        )
        self.publicacao = Publicacao.objects.create(
            torcida=self.torcida,
            autor=self.autor,
            texto="Publicação privada da torcida",
        )

    def test_usuario_de_fora_nao_lista_publicacao(self):
        self.client.force_authenticate(user=self.estranho)
        response = self.client.get("/api/comunidade/publicacoes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_membro_consegue_listar_publicacao(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.get("/api/comunidade/publicacoes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_usuario_de_fora_nao_consegue_criar_publicacao_na_torcida(self):
        self.client.force_authenticate(user=self.estranho)
        response = self.client.post(
            "/api/comunidade/publicacoes/",
            {
                "torcida": self.torcida.pk,
                "texto": "Tentativa indevida",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            Publicacao.objects.filter(texto="Tentativa indevida").exists()
        )
