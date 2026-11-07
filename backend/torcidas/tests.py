import hashlib

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase

from .models import Membro, Torcida, ConviteTorcida

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
        response = self.client.get(f"/api/torcidas/{self.torcida.pk}/membros/")
        self.assertEqual(response.status_code, 404)

    def test_membro_pode_consultar_torcida(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/torcidas/{self.torcida.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_anomino_nao_pode_criar_torcida(self):
        response = self.client.post(
            "/api/torcidas/",
            {"nome": "Nova Torcida", "slug": "nova-torcida", "cor_principal": "#202020"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


class ConvitesTorcidasTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_convite", password="Senha-Forte-2026!"
        )
        self.convidado = User.objects.create_user(
            username="convidado", password="Senha-Forte-2026!"
        )
        self.torcida = Torcida.objects.create(nome="Convite FC", slug="convite-fc")
        Membro.objects.create(usuario=self.admin, torcida=self.torcida, papel="admin")

    def criar_convite(self, **dados):
        self.client.force_authenticate(user=self.admin)
        return self.client.post(
            f"/api/torcidas/{self.torcida.pk}/convites/",
            dados,
            format="json",
        )

    def test_admin_cria_convite_e_usuario_aceita(self):
        resposta = self.criar_convite()
        self.assertEqual(resposta.status_code, 201)
        token = resposta.data["token"]
        self.assertFalse(ConviteTorcida.objects.filter(token_hash=token).exists())
        self.client.force_authenticate(user=self.convidado)
        aceite = self.client.post(
            "/api/torcidas/convites/aceitar/", {"token": token}, format="json"
        )
        self.assertEqual(aceite.status_code, 201)
        self.assertTrue(Membro.objects.filter(
            usuario=self.convidado, torcida=self.torcida
        ).exists())
        from community.models import Notificacao
        notificacao = Notificacao.objects.get(
            destinatario=self.admin,
            ator=self.convidado,
            tipo=Notificacao.Tipo.CONVITE,
            referencia=f"torcida:{self.torcida.pk}",
        )
        self.assertIn("convidado", notificacao.texto)


    def test_convite_nao_pode_ser_usado_acima_do_limite(self):
        resposta = self.criar_convite(limite_usos=1)
        token = resposta.data["token"]
        self.client.force_authenticate(user=self.convidado)
        self.assertEqual(self.client.post(
            "/api/torcidas/convites/aceitar/", {"token": token}, format="json"
        ).status_code, 201)
        segundo = User.objects.create_user(
            username="convidado2", password="Senha-Forte-2026!"
        )
        self.client.force_authenticate(user=segundo)
        self.assertEqual(self.client.post(
            "/api/torcidas/convites/aceitar/", {"token": token}, format="json"
        ).status_code, 400)

    def test_convite_expirado_e_rejeitado(self):
        resposta = self.criar_convite()
        token = resposta.data["token"]
        convite = ConviteTorcida.objects.get(
            token_hash=hashlib.sha256(token.encode()).hexdigest()
        )
        convite.expira_em = timezone.now() - timedelta(seconds=1)
        convite.save(update_fields=["expira_em"])
        self.client.force_authenticate(user=self.convidado)
        aceite = self.client.post(
            "/api/torcidas/convites/aceitar/", {"token": token}, format="json"
        )
        self.assertEqual(aceite.status_code, 400)

    def test_usuario_comum_nao_cria_convite(self):
        self.client.force_authenticate(user=self.convidado)
        resposta = self.client.post(
            f"/api/torcidas/{self.torcida.pk}/convites/", {}, format="json"
        )
        self.assertEqual(resposta.status_code, 404)

class PlatformAdminTorcidasTests(APITestCase):
    def test_superuser_lista_torcidas_sem_ser_membro(self):
        admin_global = User.objects.create_superuser(
            username="platform_admin_torcidas", email="", password="Strong-Test-Password-2026!"
        )
        torcida = Torcida.objects.create(nome="Admin Global FC", slug="admin-global-fc")
        self.client.force_authenticate(admin_global)
        response = self.client.get("/api/torcidas/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["id"] == torcida.pk for item in response.data))
