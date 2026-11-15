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
        cache_control = {
            directive.strip().split("=", 1)[0].lower()
            for directive in response["Cache-Control"].split(",")
        }
        self.assertIn("private", cache_control)
        self.assertIn("no-store", cache_control)
        self.assertNotIn("public", cache_control)
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


class AnexosPublicacaoTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user(username="autor_anexos", password="Senha-Forte-2026!")
        self.membro = User.objects.create_user(username="membro_anexos", password="Senha-Forte-2026!")
        self.intruso = User.objects.create_user(username="intruso_anexos", password="Senha-Forte-2026!")
        self.torcida = Torcida.objects.create(nome="Torcida Anexos", slug="torcida-anexos")
        Membro.objects.create(usuario=self.autor, torcida=self.torcida)
        Membro.objects.create(usuario=self.membro, torcida=self.torcida)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.temp_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.client = APIClient()

    def test_upload_audio_e_documento_com_publicacao(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_authenticate(user=self.autor)
        response = self.client.post("/api/comunidade/publicacoes/", {
            "torcida": self.torcida.pk,
            "texto": " ",
            "audio": SimpleUploadedFile("voz.webm", b"audio-test", content_type="audio/webm"),
            "arquivo": SimpleUploadedFile("regras.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
        }, format="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data["audio"])
        self.assertTrue(response.data["arquivo"])
        post = Publicacao.objects.get(pk=response.data["id"])
        self.assertEqual(post.status, Publicacao.Status.PENDENTE)

    def test_extensao_de_anexo_invalida_e_rejeitada(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_authenticate(user=self.autor)
        response = self.client.post("/api/comunidade/publicacoes/", {
            "torcida": self.torcida.pk,
            "texto": "Anexo",
            "arquivo": SimpleUploadedFile("script.exe", b"not-safe", content_type="application/octet-stream"),
        }, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Publicacao.objects.filter(texto="Anexo").exists())

    def test_link_de_audio_exige_membro_ativo(self):
        from django.core.files.base import ContentFile
        self.client.force_authenticate(user=self.autor)
        post = Publicacao.objects.create(torcida=self.torcida, autor=self.autor, texto="Áudio protegido", status=Publicacao.Status.APROVADA)
        post.audio.save("voz.webm", ContentFile(b"audio-data"), save=True)
        self.client.force_authenticate(user=self.membro)
        response = self.client.get("/api/comunidade/publicacoes/")
        audio_url = next(item["audio"] for item in response.data if item["id"] == post.pk)
        from urllib.parse import urlparse
        path = urlparse(audio_url).path
        token = urlparse(audio_url).query
        Membro.objects.filter(usuario=self.membro, torcida=self.torcida).delete()
        denied = self.client.get(f"{path}?{token}")
        self.assertEqual(denied.status_code, 404)
