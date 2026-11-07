from django.contrib import admin
from .models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "torcida", "tipo", "inicio_em", "status", "valor")
    list_filter = ("tipo", "status", "torcida")
    search_fields = ("titulo", "descricao", "local", "torcida__nome")
    readonly_fields = ("criado_por", "criado_em", "atualizado_em")

    def save_model(self, request, obj, form, change):
        if not change and not obj.criado_por_id:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
