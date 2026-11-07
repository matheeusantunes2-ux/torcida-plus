from django.contrib import admin
from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "nome_exibicao", "criado_em")
    search_fields = ("usuario__username", "nome_exibicao")
    readonly_fields = ("criado_em", "atualizado_em")
