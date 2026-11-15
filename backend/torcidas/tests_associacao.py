from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from .models import Torcida,Membro,PlanoAssociacao,Associacao
User=get_user_model()
class AssociacaoSaaSTests(APITestCase):
    def setUp(self):
        self.admin=User.objects.create_user(username="gestor_assoc",password="Strong-Test-2026!")
        self.user=User.objects.create_user(username="socio_teste",password="Strong-Test-2026!")
        self.torcida=Torcida.objects.create(nome="Associação Teste",slug="associacao-teste")
        Membro.objects.create(usuario=self.admin,torcida=self.torcida,papel=Membro.Papel.ADMIN)
        self.free=PlanoAssociacao.objects.create(torcida=self.torcida,nome="Apoiador",valor=0,duracao_dias=365)
        self.paid=PlanoAssociacao.objects.create(torcida=self.torcida,nome="Oficial",valor="25.00",duracao_dias=30)
    def test_planos_publicos_nao_exigem_login(self):
        r=self.client.get(f"/api/torcidas/{self.torcida.id}/associacoes/planos/"); self.assertEqual(r.status_code,200); self.assertEqual(len(r.data),2)
    def test_solicitacao_paga_fica_pendente(self):
        self.client.force_authenticate(self.user); r=self.client.post(f"/api/torcidas/{self.torcida.id}/associacoes/solicitar/",{"plano_id":self.paid.id},format="json")
        self.assertEqual(r.status_code,201); self.assertEqual(r.data["status"],"pendente"); self.assertFalse(Membro.objects.filter(usuario=self.user,torcida=self.torcida).exists())
    def test_gestor_nao_ativa_plano_pago_sem_confirmacao(self):
        a=Associacao.objects.create(torcida=self.torcida,usuario=self.user,plano=self.paid); self.client.force_authenticate(self.admin)
        r=self.client.patch(f"/api/torcidas/{self.torcida.id}/associacoes/{a.id}/",{"status":"ativa"},format="json"); self.assertEqual(r.status_code,400)
    def test_plano_gratuito_gera_carteirinha_qr_temporaria(self):
        a=Associacao.objects.create(torcida=self.torcida,usuario=self.user,plano=self.free); self.client.force_authenticate(self.admin)
        r=self.client.patch(f"/api/torcidas/{self.torcida.id}/associacoes/{a.id}/",{"status":"ativa"},format="json"); self.assertEqual(r.status_code,200)
        self.client.force_authenticate(self.user); qr=self.client.get(f"/api/torcidas/associacoes/{a.id}/carteirinha-qr/"); self.assertEqual(qr.status_code,200)
        self.client.force_authenticate(self.admin); check=self.client.post(f"/api/torcidas/{self.torcida.id}/associacoes/validar-qr/",{"qr_token":qr.data["qr_token"]},format="json")
        self.assertTrue(check.data["valido"])
    def test_qr_expirado_nao_valida(self):
        from django.core import signing
        from .associacao_views import QR_SALT
        a=Associacao.objects.create(torcida=self.torcida,usuario=self.user,plano=self.free,status=Associacao.Status.ATIVA,inicio_em=timezone.now(),fim_em=timezone.now()+timedelta(days=30))
        self.client.force_authenticate(self.admin); token=signing.TimestampSigner(salt=QR_SALT).sign(f"{a.id}:{self.torcida.id}:nonce")
        from unittest.mock import patch
        with patch("torcidas.associacao_views.QR_MAX_AGE",-1):
            r=self.client.post(f"/api/torcidas/{self.torcida.id}/associacoes/validar-qr/",{"qr_token":token},format="json")
        self.assertFalse(r.data["valido"])
