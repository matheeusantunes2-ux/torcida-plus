from django.contrib import admin
from .models import Publicacao, Comentario, Curtida, Notificacao


@admin.register(Publicacao)
class PublicacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "torcida", "autor", "criada_em")
    list_filter = ("torcida",)
    search_fields = ("texto", "autor__username", "torcida__nome")
    readonly_fields = ("criada_em", "atualizada_em")


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ("id", "publicacao", "autor", "criado_em")
    search_fields = ("texto", "autor__username")
    readonly_fields = ("criado_em", "atualizado_em")


@admin.register(Curtida)
class CurtidaAdmin(admin.ModelAdmin):
    list_display = ("publicacao", "usuario", "criada_em")
    list_filter = ("criada_em",)


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("destinatario", "ator", "tipo", "lida_em", "criada_em")
    list_filter = ("tipo", "lida_em")
    search_fields = ("destinatario__username", "ator__username", "texto")
