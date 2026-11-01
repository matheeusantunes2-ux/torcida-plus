from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from torcidas.models import Torcida

User = get_user_model()
SENHA = "Samba!Forte2026#Ritmo"
SLUG = "teste-torcida-api"

def executar():
    Torcida.objects.filter(slug=SLUG).delete()
    User.objects.filter(
        username__in=["teste_api_torcida_a", "teste_api_torcida_b"]
    ).delete()

    try:
        a = APIClient()

        r = a.post("/api/auth/cadastro/", {
            "username": "teste_api_torcida_a",
            "email": "teste_a@example.com",
            "password": SENHA,
        }, format="json")

        print("1. Cadastro A:", r.status_code, getattr(r, "data", r.content))
        assert r.status_code == 201, "Cadastro A falhou"

        r = a.post("/api/auth/login/", {
            "username": "teste_api_torcida_a",
            "password": SENHA,
        }, format="json")

        print("2. Login A:", r.status_code)
        assert r.status_code == 200, "Login A falhou"

        a.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])

        r = a.post("/api/torcidas/", {
            "nome": "Torcida de Teste",
            "slug": SLUG,
            "cor_principal": "#202020",
        }, format="json")

        print("3. Criar torcida:", r.status_code, getattr(r, "data", r.content))
        assert r.status_code == 201, "Criação da torcida falhou"

        r = a.get("/api/torcidas/")
        print("4. Listagem A:", r.status_code, getattr(r, "data", r.content))
        assert r.status_code == 200, "Listagem A falhou"
        assert any(t["slug"] == SLUG for t in r.data), "A não vê sua torcida"

        b = APIClient()

        r = b.post("/api/auth/cadastro/", {
            "username": "teste_api_torcida_b",
            "email": "teste_b@example.com",
            "password": SENHA,
        }, format="json")

        print("5. Cadastro B:", r.status_code, getattr(r, "data", r.content))
        assert r.status_code == 201, "Cadastro B falhou"

        r = b.post("/api/auth/login/", {
            "username": "teste_api_torcida_b",
            "password": SENHA,
        }, format="json")

        print("6. Login B:", r.status_code)
        assert r.status_code == 200, "Login B falhou"

        b.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])

        r = b.get("/api/torcidas/")
        print("7. Listagem B:", r.status_code, getattr(r, "data", r.content))
        assert r.status_code == 200, "Listagem B falhou"
        assert not any(t["slug"] == SLUG for t in r.data), \
            "FALHA DE ISOLAMENTO: B vê a torcida de A"

        print("\nSUCESSO: todos os testes passaram!")

    finally:
        Torcida.objects.filter(slug=SLUG).delete()
        User.objects.filter(
            username__in=["teste_api_torcida_a", "teste_api_torcida_b"]
        ).delete()
        print("Dados temporários removidos.")

executar()
