from io import BytesIO
import uuid

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from torcidas.models import Torcida, Membro
from community.models import Publicacao

User = get_user_model()
sufixo = uuid.uuid4().hex[:8]
usuario = torcida = publicacao = None
arquivo_salvo = None

try:
    usuario = User.objects.create_user(
        username=f"teste_img_{sufixo}",
        password="TesteSeguro123!"
    )

    torcida = Torcida.objects.create(
        nome=f"Teste imagem {sufixo}",
        slug=f"teste-imagem-{sufixo}"
    )

    Membro.objects.create(
        usuario=usuario,
        torcida=torcida,
        papel="admin"
    )

    buffer = BytesIO()
    Image.new("RGB", (32, 32), (30, 100, 200)).save(
        buffer, format="PNG"
    )

    imagem = SimpleUploadedFile(
        "teste.png",
        buffer.getvalue(),
        content_type="image/png"
    )

    cliente = APIClient()
    cliente.force_authenticate(user=usuario)

    resposta = cliente.post(
        "/api/comunidade/publicacoes/",
        {
            "torcida": torcida.pk,
            "texto": "Teste temporário de imagem.",
            "imagem": imagem,
        },
        format="multipart"
    )

    print("Status HTTP:", resposta.status_code)
    print("Resposta:", resposta.data)

    assert resposta.status_code == 201, (
        "A API não criou a publicação."
    )

    publicacao = Publicacao.objects.get(pk=resposta.data["id"])
    arquivo_salvo = publicacao.imagem.name

    assert arquivo_salvo, "Imagem não vinculada à publicação."
    assert default_storage.exists(arquivo_salvo), (
        "Arquivo não encontrado no armazenamento."
    )

    print("SUCESSO: publicação criada e imagem armazenada.")

finally:
    if publicacao is not None:
        publicacao.delete()

    if arquivo_salvo and default_storage.exists(arquivo_salvo):
        default_storage.delete(arquivo_salvo)

    if torcida is not None:
        torcida.delete()

    if usuario is not None:
        usuario.delete()

    print("Limpeza dos dados temporários concluída.")
