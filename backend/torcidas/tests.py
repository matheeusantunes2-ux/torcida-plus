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


class PelotoesTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin_pelotao", password="Senha-Forte-2026!")
        self.membro = User.objects.create_user(username="membro_pelotao", password="Senha-Forte-2026!")
        self.torcida = Torcida.objects.create(nome="Nação Única", slug="nacao-unica")
        Membro.objects.create(usuario=self.admin, torcida=self.torcida, papel="admin")
        Membro.objects.create(usuario=self.membro, torcida=self.torcida, papel="membro")

    def test_admin_cria_pelotao_e_membro_pode_ser_vinculado(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/torcidas/{self.torcida.pk}/pelotoes/",
            {"nome": "Pelotão Norte", "slug": "pelotao-norte", "descricao": "Setor norte"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        pelotao_id = response.data["id"]
        member = Membro.objects.get(usuario=self.membro, torcida=self.torcida)
        self.client.patch(
            f"/api/torcidas/{self.torcida.pk}/membros/{member.pk}/",
            {"pelotao_id": pelotao_id},
            format="json",
        )
        member.refresh_from_db()
        self.assertEqual(member.pelotao_id, pelotao_id)

    def test_membro_comum_nao_pode_criar_pelotao(self):
        self.client.force_authenticate(user=self.membro)
        response = self.client.post(
            f"/api/torcidas/{self.torcida.pk}/pelotoes/",
            {"nome": "Pelotão Sul", "slug": "pelotao-sul"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_convite_pode_ser_limitado_a_pelotao(self):
        self.client.force_authenticate(user=self.admin)
        pelotao = __import__("torcidas.models", fromlist=["Pelotao"]).Pelotao.objects.create(
            torcida=self.torcida, nome="Pelotão Leste", slug="pelotao-leste"
        )
        response = self.client.post(
            f"/api/torcidas/{self.torcida.pk}/convites/",
            {"pelotao_id": pelotao.pk, "limite_usos": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        token = response.data["token"]
        convidado = User.objects.create_user(username="convidado_pelotao", password="Senha-Forte-2026!")
        self.client.force_authenticate(user=convidado)
        accepted = self.client.post("/api/torcidas/convites/aceitar/", {"token": token}, format="json")
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(Membro.objects.get(usuario=convidado, torcida=self.torcida).pelotao_id, pelotao.pk)


class LiderPelotaoPermissoesTests(APITestCase):
    def setUp(self):
        from .models import Pelotao
        self.admin = User.objects.create_user(username="admin_lider", password="Senha-Forte-2026!")
        self.leader = User.objects.create_user(username="lider_norte", password="Senha-Forte-2026!")
        self.member = User.objects.create_user(username="membro_norte", password="Senha-Forte-2026!")
        self.outsider = User.objects.create_user(username="membro_sul", password="Senha-Forte-2026!")
        self.torcida = Torcida.objects.create(nome="Permissões FC", slug="permissoes-fc")
        self.norte = Pelotao.objects.create(torcida=self.torcida, nome="Norte", slug="norte")
        self.sul = Pelotao.objects.create(torcida=self.torcida, nome="Sul", slug="sul")
        Membro.objects.create(usuario=self.admin, torcida=self.torcida, papel=Membro.Papel.ADMIN)
        Membro.objects.create(usuario=self.leader, torcida=self.torcida, papel=Membro.Papel.LIDER_PELOTAO, pelotao=self.norte)
        self.alvo = Membro.objects.create(usuario=self.member, torcida=self.torcida, pelotao=self.norte)
        self.fora = Membro.objects.create(usuario=self.outsider, torcida=self.torcida, pelotao=self.sul)

    def test_lider_pode_remover_integrante_do_proprio_pelotao(self):
        self.client.force_authenticate(user=self.leader)
        response = self.client.delete(f"/api/torcidas/{self.torcida.pk}/membros/{self.alvo.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Membro.objects.filter(pk=self.alvo.pk).exists())

    def test_lider_nao_pode_remover_integrante_de_outro_pelotao(self):
        self.client.force_authenticate(user=self.leader)
        response = self.client.delete(f"/api/torcidas/{self.torcida.pk}/membros/{self.fora.pk}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Membro.objects.filter(pk=self.fora.pk).exists())

    def test_lider_nao_pode_alterar_papel_ou_vinculo_do_integrante(self):
        self.client.force_authenticate(user=self.leader)
        response = self.client.patch(
            f"/api/torcidas/{self.torcida.pk}/membros/{self.alvo.pk}/",
            {"papel": "moderador"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_lider_so_pode_criar_convite_para_o_proprio_pelotao(self):
        self.client.force_authenticate(user=self.leader)
        own = self.client.post(
            f"/api/torcidas/{self.torcida.pk}/convites/",
            {"papel": "membro", "pelotao_id": self.norte.pk}, format="json"
        )
        self.assertEqual(own.status_code, 201)
        outside = self.client.post(
            f"/api/torcidas/{self.torcida.pk}/convites/",
            {"papel": "membro", "pelotao_id": self.sul.pk}, format="json"
        )
        self.assertEqual(outside.status_code, 403)

    def test_lider_nao_pode_criar_ou_editar_pelotoes(self):
        self.client.force_authenticate(user=self.leader)
        create = self.client.post(
            f"/api/torcidas/{self.torcida.pk}/pelotoes/",
            {"nome": "Oeste", "slug": "oeste"}, format="json"
        )
        self.assertEqual(create.status_code, 403)
        edit = self.client.patch(
            f"/api/torcidas/{self.torcida.pk}/pelotoes/{self.sul.pk}/",
            {"nome": "Sul alterado"}, format="json"
        )
        self.assertEqual(edit.status_code, 403)

    def test_admin_pode_designar_lider_mas_lider_precisa_de_pelotao(self):
        novo = User.objects.create_user(username="novo_lider", password="Senha-Forte-2026!")
        vinculo = Membro.objects.create(usuario=novo, torcida=self.torcida)
        self.client.force_authenticate(user=self.admin)
        invalid = self.client.patch(
            f"/api/torcidas/{self.torcida.pk}/membros/{vinculo.pk}/",
            {"papel": "lider_pelotao"}, format="json"
        )
        self.assertEqual(invalid.status_code, 400)
        valid = self.client.patch(
            f"/api/torcidas/{self.torcida.pk}/membros/{vinculo.pk}/",
            {"papel": "lider_pelotao", "pelotao_id": self.sul.pk}, format="json"
        )
        self.assertEqual(valid.status_code, 200)
        vinculo.refresh_from_db()
        self.assertEqual(vinculo.papel, Membro.Papel.LIDER_PELOTAO)
        self.assertEqual(vinculo.pelotao_id, self.sul.pk)


class AtividadesPelotoesTests(APITestCase):
    def setUp(self):
        from .models import Pelotao, AtividadePelotao
        self.admin = User.objects.create_user(username="admin_audit", password="Senha-Forte-2026!")
        self.leader = User.objects.create_user(username="leader_audit", password="Senha-Forte-2026!")
        self.member = User.objects.create_user(username="member_audit", password="Senha-Forte-2026!")
        self.other_leader = User.objects.create_user(username="leader_sul_audit", password="Senha-Forte-2026!")
        self.torcida = Torcida.objects.create(nome="Auditoria FC", slug="auditoria-fc")
        self.norte = Pelotao.objects.create(torcida=self.torcida, nome="Norte", slug="norte-audit")
        self.sul = Pelotao.objects.create(torcida=self.torcida, nome="Sul", slug="sul-audit")
        Membro.objects.create(usuario=self.admin, torcida=self.torcida, papel=Membro.Papel.ADMIN)
        Membro.objects.create(usuario=self.leader, torcida=self.torcida, papel=Membro.Papel.LIDER_PELOTAO, pelotao=self.norte)
        Membro.objects.create(usuario=self.other_leader, torcida=self.torcida, papel=Membro.Papel.LIDER_PELOTAO, pelotao=self.sul)
        Membro.objects.create(usuario=self.member, torcida=self.torcida, pelotao=self.norte)
        AtividadePelotao.objects.create(torcida=self.torcida, pelotao=self.norte, ator=self.admin, acao="membro_entrou", descricao="Entrada no Norte")
        AtividadePelotao.objects.create(torcida=self.torcida, pelotao=self.sul, ator=self.admin, acao="membro_entrou", descricao="Entrada no Sul")

    def test_lider_consulta_somente_historico_do_proprio_pelotao(self):
        self.client.force_authenticate(self.leader)
        response = self.client.get(f"/api/torcidas/{self.torcida.pk}/atividades/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["pelotao"], self.norte.pk)

    def test_lider_nao_pode_filtrar_outro_pelotao(self):
        self.client.force_authenticate(self.leader)
        response = self.client.get(f"/api/torcidas/{self.torcida.pk}/atividades/?pelotao_id={self.sul.pk}")
        self.assertEqual(response.status_code, 403)

    def test_admin_consulta_historico_de_todos_os_pelotoes(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/torcidas/{self.torcida.pk}/atividades/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

    def test_membro_comum_nao_consulta_historico(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(f"/api/torcidas/{self.torcida.pk}/atividades/")
        self.assertEqual(response.status_code, 403)
