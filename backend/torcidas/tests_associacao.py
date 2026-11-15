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

    def test_criacao_de_plano_exige_autenticacao(self):
        url=f"/api/torcidas/{self.torcida.id}/associacoes/planos/"
        anonimo=self.client.post(url,{"nome":"Novo Plano","valor":"0","duracao_dias":90},format="json")
        self.assertEqual(anonimo.status_code,401)
        self.client.force_authenticate(self.admin)
        autorizado=self.client.post(url,{"nome":"Novo Plano","valor":"0","duracao_dias":90},format="json")
        self.assertEqual(autorizado.status_code,201)

    def test_validacao_qr_invalido_registra_auditoria_sem_salvar_token(self):
        from .models import AtividadePelotao
        self.client.force_authenticate(self.admin)
        response=self.client.post(f"/api/torcidas/{self.torcida.id}/associacoes/validar-qr/",{"qr_token":"token-invalido-nao-registrar"},format="json")
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.data["valido"])
        log=AtividadePelotao.objects.filter(torcida=self.torcida,acao="validacao_qr_falha").latest("id")
        self.assertNotIn("token-invalido",log.descricao)
    def test_validacao_qr_valido_registra_auditoria(self):
        from .models import AtividadePelotao
        a=Associacao.objects.create(torcida=self.torcida,usuario=self.user,plano=self.free,status=Associacao.Status.ATIVA,inicio_em=timezone.now(),fim_em=timezone.now()+timedelta(days=30))
        self.client.force_authenticate(self.user)
        qr=self.client.get(f"/api/torcidas/associacoes/{a.id}/carteirinha-qr/")
        self.client.force_authenticate(self.admin)
        response=self.client.post(f"/api/torcidas/{self.torcida.id}/associacoes/validar-qr/",{"qr_token":qr.data["qr_token"]},format="json")
        self.assertTrue(response.data["valido"])
        self.assertTrue(AtividadePelotao.objects.filter(torcida=self.torcida,acao="validacao_qr_sucesso").exists())


    def test_cobranca_paga_ativa_associacao_e_renova_validade(self):
        from datetime import date
        from .models import PagamentoAssociacao
        a=Associacao.objects.create(torcida=self.torcida,usuario=self.user,plano=self.paid)
        self.client.force_authenticate(self.admin)
        created=self.client.post(f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/",{"associacao_id":a.id,"valor":"25.00","vencimento":date.today().isoformat()},format="json")
        self.assertEqual(created.status_code,201)
        paid=self.client.patch(f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/{created.data['id']}/",{"status":"pago"},format="json")
        self.assertEqual(paid.status_code,200)
        a.refresh_from_db()
        self.assertEqual(a.status,Associacao.Status.ATIVA)
        self.assertEqual((a.fim_em-a.inicio_em).days,30)
        self.assertEqual(PagamentoAssociacao.objects.get(pk=created.data["id"]).status,PagamentoAssociacao.Status.PAGO)
        self.assertTrue(Membro.objects.filter(usuario=self.user,torcida=self.torcida).exists())

    def test_cobranca_vencida_aparece_como_atrasada(self):
        from datetime import date, timedelta
        from .models import PagamentoAssociacao
        a=Associacao.objects.create(torcida=self.torcida,usuario=self.user,plano=self.paid)
        PagamentoAssociacao.objects.create(associacao=a,valor="25.00",vencimento=date.today()-timedelta(days=1))
        self.client.force_authenticate(self.admin)
        response=self.client.get(f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data[0]["status"],PagamentoAssociacao.Status.ATRASADO)

    def test_membro_comum_nao_acessa_financeiro_da_torcida(self):
        self.client.force_authenticate(self.user)
        response=self.client.get(f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/")
        self.assertEqual(response.status_code,404)

    def test_membro_comum_nao_cria_cobranca(self):
        Membro.objects.create(usuario=self.user,torcida=self.torcida,papel=Membro.Papel.MEMBRO)
        a=Associacao.objects.create(torcida=self.torcida,usuario=self.user,plano=self.paid)
        self.client.force_authenticate(self.user)
        response=self.client.post(f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/",{"associacao_id":a.id,"valor":"25.00","vencimento":timezone.localdate().isoformat()},format="json")
        self.assertEqual(response.status_code,403)

    def test_confirmar_pagamento_duas_vezes_nao_duplica_validade(self):
        from datetime import date
        from .models import PagamentoAssociacao
        a=Associacao.objects.create(torcida=self.torcida,usuario=self.user,plano=self.paid)
        self.client.force_authenticate(self.admin)
        created=self.client.post(f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/",{"associacao_id":a.id,"valor":"25.00","vencimento":date.today().isoformat()},format="json")
        self.assertEqual(created.status_code,201)
        url=f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/{created.data['id']}/"
        first=self.client.patch(url,{"status":"pago"},format="json")
        self.assertEqual(first.status_code,200)
        a.refresh_from_db(); first_end=a.fim_em
        second=self.client.patch(url,{"status":"pago"},format="json")
        self.assertEqual(second.status_code,200)
        a.refresh_from_db()
        self.assertEqual(a.fim_em,first_end)
        self.assertEqual(PagamentoAssociacao.objects.get(pk=created.data["id"]).status,PagamentoAssociacao.Status.PAGO)

    def test_pagamento_confirmado_nao_pode_ser_cancelado(self):
        from datetime import date
        a=Associacao.objects.create(torcida=self.torcida,usuario=self.user,plano=self.paid)
        self.client.force_authenticate(self.admin)
        created=self.client.post(f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/",{"associacao_id":a.id,"valor":"25.00","vencimento":date.today().isoformat()},format="json")
        self.client.patch(f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/{created.data['id']}/",{"status":"pago"},format="json")
        cancelled=self.client.patch(f"/api/torcidas/{self.torcida.id}/associacoes/pagamentos/{created.data['id']}/",{"status":"cancelado"},format="json")
        self.assertEqual(cancelled.status_code,400)
