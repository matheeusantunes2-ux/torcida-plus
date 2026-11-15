from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from torcidas.models import Torcida, Membro
from .models import Evento

User = get_user_model()


class EventosApiTests(APITestCase):
    def setUp(self):
        self.global_admin = User.objects.create_superuser(
            username="event_global_admin", email="", password="Strong-Test-Password-2026!"
        )
        self.member = User.objects.create_user(
            username="event_member", password="Strong-Test-Password-2026!"
        )
        self.torcida = Torcida.objects.create(nome="Eventos FC", slug="eventos-fc")
        Membro.objects.create(usuario=self.member, torcida=self.torcida, papel="membro")

    def test_superuser_cria_evento_global_sem_ser_membro(self):
        self.client.force_authenticate(self.global_admin)
        response = self.client.post("/api/eventos/", {
            "torcida": self.torcida.pk,
            "titulo": "Encontro geral",
            "tipo": "encontro",
            "local": "Rio de Janeiro",
            "inicio_em": (timezone.now() + timedelta(days=5)).isoformat(),
            "valor": "0.00",
            "status": "publicado",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Evento.objects.count(), 1)

    def test_membro_comum_nao_cria_evento(self):
        self.client.force_authenticate(self.member)
        response = self.client.post("/api/eventos/", {
            "torcida": self.torcida.pk,
            "titulo": "Evento não autorizado",
            "inicio_em": (timezone.now() + timedelta(days=5)).isoformat(),
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_superuser_lista_eventos_de_todas_as_torcidas(self):
        Evento.objects.create(
            torcida=self.torcida, titulo="Evento privado", inicio_em=timezone.now(),
            status=Evento.Status.RASCUNHO, criado_por=self.member,
        )
        self.client.force_authenticate(self.global_admin)
        response = self.client.get("/api/eventos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_membro_comum_nao_exclui_evento_publicado(self):
        evento = Evento.objects.create(
            torcida=self.torcida,
            titulo="Evento protegido",
            inicio_em=timezone.now() + timedelta(days=2),
            status=Evento.Status.PUBLICADO,
            criado_por=self.member,
        )
        self.client.force_authenticate(self.member)
        response = self.client.delete(f"/api/eventos/{evento.pk}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Evento.objects.filter(pk=evento.pk).exists())


class IngressoEventoApiTests(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(username="ticket_member", password="Strong-Test-Password-2026!")
        self.outsider = User.objects.create_user(username="ticket_outsider", password="Strong-Test-Password-2026!")
        self.torcida = Torcida.objects.create(nome="Ingresso FC", slug="ingresso-fc")
        Membro.objects.create(usuario=self.member, torcida=self.torcida, papel="membro")
        self.evento = Evento.objects.create(
            torcida=self.torcida, titulo="Jogo com ingresso",
            inicio_em=timezone.now() + timedelta(days=3),
            valor="0.00", status=Evento.Status.PUBLICADO, criado_por=self.member,
        )

    def test_membro_emite_ingresso_gratuito_e_recebe_codigo(self):
        self.client.force_authenticate(self.member)
        response = self.client.post(f"/api/eventos/{self.evento.pk}/ingresso/", {"quantidade": 1}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "pago")
        self.assertTrue(response.data["codigo"])

    def test_usuario_de_fora_nao_consegue_emitir_ingresso(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.post(f"/api/eventos/{self.evento.pk}/ingresso/", {"quantidade": 1}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_ingresso_pago_e_exibido_no_status_de_acesso(self):
        self.client.force_authenticate(self.member)
        self.client.post(f"/api/eventos/{self.evento.pk}/ingresso/", {"quantidade": 1}, format="json")
        response = self.client.get(f"/api/eventos/{self.evento.pk}/ingresso/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["pode_entrar"])
