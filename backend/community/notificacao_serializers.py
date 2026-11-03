from rest_framework import serializers
from .models import Notificacao

class NotificacaoSerializer(serializers.ModelSerializer):
    ator_username = serializers.CharField(source='ator.username', read_only=True, allow_null=True)
    class Meta:
        model = Notificacao
        fields = ['id', 'tipo', 'texto', 'referencia', 'ator_username', 'criada_em', 'lida_em']
        read_only_fields = fields
