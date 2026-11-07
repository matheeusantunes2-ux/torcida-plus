from django.contrib import admin
from .models import Torcida, Membro, ConviteTorcida


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
