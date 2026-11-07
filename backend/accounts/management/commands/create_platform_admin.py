"""Cria o primeiro administrador geral de forma interativa e segura.

Execute no ambiente da aplicação:
    python manage.py create_platform_admin

A senha é solicitada no terminal, nunca passada por argumento ou gravada no
repositório. O comando não promove contas existentes: se o username já existir,
a operação é interrompida para evitar tomada acidental de conta.
"""
from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Perfil


class Command(BaseCommand):
    help = "Cria uma conta de administrador geral do TORCIDA+."

    def handle(self, *args, **options):
        User = get_user_model()
        username = input("Nome de usuário [admin-loja]: ").strip() or "admin-loja"

        if not username or len(username) > 150:
            raise CommandError("Nome de usuário inválido.")

        if User.objects.filter(username__iexact=username).exists():
            raise CommandError(
                f"O usuário '{username}' já existe. Nenhuma alteração foi feita. "
                "Use outro nome ou recupere o acesso por um procedimento verificado."
            )

        password = getpass("Crie uma senha forte: ")
        confirmation = getpass("Confirme a senha: ")
        if not password or password != confirmation:
            raise CommandError("As senhas estão vazias ou não conferem.")

        candidate = User(username=username, email="")
        try:
            validate_password(password, user=candidate)
        except Exception as exc:
            raise CommandError(f"Senha não aceita: {exc}") from exc

        with transaction.atomic():
            user = User.objects.create_superuser(
                username=username,
                email="",
                password=password,
            )
            Perfil.objects.get_or_create(
                usuario=user,
                defaults={"nome_exibicao": "Administrador geral"},
            )

        self.stdout.write(self.style.SUCCESS(
            f"Administrador geral '{user.username}' criado com sucesso. "
            "Guarde a senha em um gerenciador seguro."
        ))
