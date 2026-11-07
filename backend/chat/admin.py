from django.contrib import admin
from .models import Conversa, ParticipanteConversa, Mensagem, LeituraMensagem


class ParticipanteInline(admin.TabularInline):
    model = ParticipanteConversa
    extra = 0
    autocomplete_fields = ("usuario",)


@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    list_display = ("id", "torcida", "tipo", "nome", "criada_por", "atualizada_em")
    list_filter = ("tipo", "torcida")
    search_fields = ("nome", "criada_por__username")
    inlines = (ParticipanteInline,)


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ("id", "conversa", "autor", "criada_em", "apagada_em")
    list_filter = ("apagada_em",)
    search_fields = ("conteudo", "autor__username")
    readonly_fields = ("criada_em", "editada_em")


@admin.register(LeituraMensagem)
class LeituraMensagemAdmin(admin.ModelAdmin):
    list_display = ("mensagem", "usuario", "lida_em")
    search_fields = ("usuario__username",)


admin.site.register(ParticipanteConversa)
