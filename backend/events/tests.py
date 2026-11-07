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
        Membro.objects.create(usuario=self.member, torcida=self.torcida, papel="admin")

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
