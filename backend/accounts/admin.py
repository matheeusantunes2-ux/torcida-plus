from django.contrib import admin
from .models import Perfil, AdminAuditLog


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "nome_exibicao", "criado_em")
    search_fields = ("usuario__username", "nome_exibicao")
    readonly_fields = ("criado_em", "atualizado_em")


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "ator", "acao", "entidade", "entidade_id", "descricao")
    list_filter = ("acao", "entidade", "criado_em")
    search_fields = ("ator__username", "descricao", "entidade_id")
    readonly_fields = ("ator", "acao", "entidade", "entidade_id", "descricao", "detalhes", "criado_em")
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
