import base64
import tempfile
from urllib.parse import parse_qs, urlparse

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from community.models import Publicacao
from torcidas.models import Membro, Torcida


User = get_user_model()
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/"
    "aAAAAABJRU5ErkJggg=="
)


class AcessoImagemPublicacaoTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user(
            username="autor_imagem", password="Senha-Forte-2026!"
        )
        self.membro = User.objects.create_user(
            username="membro_imagem", password="Senha-Forte-2026!"
        )
        self.estranho = User.objects.create_user(
            username="estranho_imagem", password="Senha-Forte-2026!"
        )
        self.torcida = Torcida.objects.create(
            nome="Torcida Imagem", slug="torcida-imagem"
        )
        Membro.objects.create(usuario=self.autor, torcida=self.torcida)
        Membro.objects.create(usuario=self.membro, torcida=self.torcida)
        self.publicacao = Publicacao.objects.create(
            torcida=self.torcida,
            autor=self.autor,
            texto="Imagem de teste",
            status=Publicacao.Status.APROVADA,
        )
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.temp_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.publicacao.imagem.save(
            "teste.png", ContentFile(PNG_1X1), save=True
        )
        self.client = APIClient()

    def obter_url_assinada(self):
        self.client.force_authenticate(user=self.membro)
        response = self.client.get("/api/comunidade/publicacoes/")
        self.assertEqual(response.status_code, 200)
        url = response.data[0]["imagem"]
        self.assertTrue(url)
        parsed = urlparse(url)
        token = parse_qs(parsed.query)["token"][0]
        return parsed.path, token

    def test_imagem_exige_assinatura_temporaria(self):
        response = self.client.get(
            f"/media/publicacoes/{self.publicacao.imagem.name.split('/', 1)[1]}"
        )
        self.assertEqual(response.status_code, 404)

    def test_membro_recebe_imagem_assinada(self):
        path, token = self.obter_url_assinada()
        response = self.client.get(f"{path}?token={token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        response.close()

    def test_remocao_de_membro_revoga_acesso_a_imagem(self):
        path, token = self.obter_url_assinada()
        Membro.objects.filter(usuario=self.membro, torcida=self.torcida).delete()
        response = self.client.get(f"{path}?token={token}")
        self.assertEqual(response.status_code, 404)

    def test_publicacao_nao_aprovada_nao_entrega_imagem(self):
        path, token = self.obter_url_assinada()
        self.publicacao.status = Publicacao.Status.REJEITADA
        self.publicacao.save(update_fields=["status"])
        response = self.client.get(f"{path}?token={token}")
        self.assertEqual(response.status_code, 404)
