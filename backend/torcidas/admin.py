from django.contrib import admin
from .models import Torcida, Membro, ConviteTorcida, AtividadePelotao, PlanoAssociacao, Associacao, PagamentoAssociacao


class MembroInline(admin.TabularInline):
    model = Membro
    extra = 0
    autocomplete_fields = ("usuario",)


@admin.register(Torcida)
class TorcidaAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "criada_em")
    search_fields = ("nome", "slug")
    inlines = (MembroInline,)


@admin.register(Membro)
class MembroAdmin(admin.ModelAdmin):
    list_display = ("usuario", "torcida", "papel", "criado_em")
    list_filter = ("papel", "torcida")
    search_fields = ("usuario__username", "torcida__nome")


@admin.register(ConviteTorcida)
class ConviteTorcidaAdmin(admin.ModelAdmin):
    list_display = ("torcida", "criado_por", "papel", "expira_em", "usos", "limite_usos", "revogado_em")
    list_filter = ("papel", "revogado_em")
    search_fields = ("torcida__nome", "criado_por__username")
    readonly_fields = ("token_hash", "criado_em")


@admin.register(AtividadePelotao)
class AtividadePelotaoAdmin(admin.ModelAdmin):
    list_display = ("torcida", "pelotao", "acao", "ator", "criado_em")
    list_filter = ("acao", "torcida", "pelotao")
    search_fields = ("descricao", "ator__username", "torcida__nome")
    readonly_fields = ("torcida", "pelotao", "ator", "acao", "descricao", "criado_em")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PlanoAssociacao)
class PlanoAssociacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "torcida", "valor", "duracao_dias", "ativo")
    list_filter = ("ativo", "torcida")
    search_fields = ("nome", "torcida__nome")

@admin.register(Associacao)
class AssociacaoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "torcida", "plano", "status", "fim_em", "aprovado_por")
    list_filter = ("status", "torcida", "plano")
    search_fields = ("usuario__username", "torcida__nome", "plano__nome")
    readonly_fields = ("criado_em", "atualizado_em")


@admin.register(PagamentoAssociacao)
class PagamentoAssociacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "associacao", "valor", "vencimento", "status", "pago_em", "confirmado_por")
    list_filter = ("status", "vencimento")
    search_fields = ("associacao__usuario__username", "associacao__torcida__nome")
    readonly_fields = ("criado_em", "pago_em", "confirmado_por")
