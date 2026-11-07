from django.contrib import admin
from .models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "torcida", "tipo", "inicio_em", "status", "valor")
    list_filter = ("tipo", "status", "torcida")
    search_fields = ("titulo", "descricao", "local", "torcida__nome")
    readonly_fields = ("criado_por", "criado_em", "atualizado_em")
