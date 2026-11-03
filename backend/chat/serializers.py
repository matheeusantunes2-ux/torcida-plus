from django.contrib.auth import get_user_model
from rest_framework import serializers

from torcidas.models import Membro
from .models import Conversa, ParticipanteConversa, Mensagem

User = get_user_model()


class MensagemSerializer(serializers.ModelSerializer):
    autor_id = serializers.IntegerField(source="autor_id", read_only=True)
    autor_username = serializers.CharField(source="autor.username", read_only=True)

    class Meta:
        model = Mensagem
        fields = ["id", "autor_id", "autor_username", "conteudo", "criada_em", "editada_em"]
        read_only_fields = ["id", "autor_id", "autor_username", "criada_em", "editada_em"]

    def validate_conteudo(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("A mensagem não pode estar vazia.")
        return value


class ConversaSerializer(serializers.ModelSerializer):
    participantes = serializers.SerializerMethodField()
    ultima_mensagem = serializers.SerializerMethodField()

    class Meta:
        model = Conversa
        fields = ["id", "torcida", "tipo", "nome", "participantes", "ultima_mensagem", "criada_em", "atualizada_em"]
        read_only_fields = ["id", "participantes", "ultima_mensagem", "criada_em", "atualizada_em"]

    def get_participantes(self, obj):
        return list(obj.participantes.filter(ativo=True).values_list("usuario__username", flat=True))

    def get_ultima_mensagem(self, obj):
        mensagem = obj.mensagens.filter(apagada_em__isnull=True).order_by("-criada_em", "-id").first()
        if not mensagem:
            return None
        return {
            "id": mensagem.pk,
            "autor": mensagem.autor.username,
            "conteudo": mensagem.conteudo,
            "criada_em": mensagem.criada_em,
        }

    def validate(self, attrs):
        request = self.context["request"]
        torcida = attrs["torcida"]
        if not Membro.objects.filter(torcida=torcida, usuario=request.user).exists():
            raise serializers.ValidationError({"torcida": "Você não participa desta torcida."})
        tipo = attrs.get("tipo")
        if tipo not in (Conversa.Tipo.PRIVADA, Conversa.Tipo.GRUPO):
            raise serializers.ValidationError({"tipo": "Tipo de conversa inválido."})
        if tipo == Conversa.Tipo.GRUPO and not attrs.get("nome", "").strip():
            raise serializers.ValidationError({"nome": "Informe um nome para o grupo."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        participantes_ids = request.data.get("participantes", [])
        if not isinstance(participantes_ids, list) or len(participantes_ids) > 100:
            raise serializers.ValidationError({"participantes": "Informe uma lista de até 100 IDs."})
        ids = set()
        for value in participantes_ids:
            try:
                ids.add(int(value))
            except (TypeError, ValueError):
                raise serializers.ValidationError({"participantes": "IDs inválidos."})
        ids.add(request.user.pk)
        membros = set(Membro.objects.filter(
            torcida=validated_data["torcida"], usuario_id__in=ids
        ).values_list("usuario_id", flat=True))
        if membros != ids:
            raise serializers.ValidationError({"participantes": "Todos os participantes devem pertencer à torcida."})
        if validated_data["tipo"] == Conversa.Tipo.PRIVADA and len(ids) != 2:
            raise serializers.ValidationError({"participantes": "Uma conversa privada deve ter exatamente duas pessoas."})
        if validated_data["tipo"] == Conversa.Tipo.GRUPO and len(ids) < 2:
            raise serializers.ValidationError({"participantes": "O grupo precisa de pelo menos duas pessoas."})
        from django.db import transaction
        with transaction.atomic():
            conversa = Conversa.objects.create(criada_por=request.user, **validated_data)
            ParticipanteConversa.objects.bulk_create([
                ParticipanteConversa(conversa=conversa, usuario_id=user_id) for user_id in ids
            ])
        return conversa
