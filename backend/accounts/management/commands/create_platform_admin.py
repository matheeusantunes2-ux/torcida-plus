"""Cria o primeiro administrador geral de forma interativa ou via ambiente protegido.

Modo interativo:
    python manage.py create_platform_admin

Modo automatizado:
    python manage.py create_platform_admin --from-env --if-missing

No modo automatizado, os segredos são lidos apenas do ambiente do serviço.
Nunca passe a senha na linha de comando, em workflow inputs ou no repositório.
A opção --if-missing torna a execução segura no comando de inicialização:
se o bootstrap estiver desligado ou a conta já existir, o servidor continua.
"""
import os
from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Perfil


class Command(BaseCommand):
    help = "Cria uma conta de administrador geral do TORCIDA+."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-env",
            action="store_true",
            help="Lê credenciais de variáveis protegidas do ambiente.",
        )
        parser.add_argument(
            "--if-missing",
            action="store_true",
            help="Não falha se o bootstrap estiver desligado ou a conta já existir.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        safe_mode = options["if_missing"]

        if safe_mode and not options["from_env"]:
            raise CommandError("--if-missing só pode ser usado junto com --from-env.")

        if options["from_env"]:
            if os.environ.get("TORCIDA_ADMIN_BOOTSTRAP_ENABLED") != "1":
                if safe_mode:
                    self.stdout.write("Bootstrap desativado; nenhuma alteração feita.")
                    return
                raise CommandError("Bootstrap não habilitado no ambiente do serviço.")
            username = os.environ.get("TORCIDA_ADMIN_BOOTSTRAP_USERNAME", "").strip()
            password = os.environ.get("TORCIDA_ADMIN_BOOTSTRAP_PASSWORD", "")
            if not username or not password:
                if safe_mode:
                    self.stderr.write("Bootstrap habilitado, mas faltam variáveis; nenhuma alteração feita.")
                    return
                raise CommandError("Faltam as credenciais protegidas do bootstrap.")
        else:
            username = input("Nome de usuário [admin-loja]: ").strip() or "admin-loja"
            password = None

        if not username or len(username) > 150:
            if safe_mode:
                self.stderr.write("Nome de usuário inválido; nenhuma alteração feita.")
                return
            raise CommandError("Nome de usuário inválido.")

        if User.objects.filter(username__iexact=username).exists():
            if safe_mode:
                self.stdout.write("A conta indicada já existe; nenhuma alteração foi feita.")
                return
            raise CommandError(
                f"O usuário '{username}' já existe. Nenhuma alteração foi feita. "
                "Use outro nome ou recupere o acesso por um procedimento verificado."
            )

        if password is None:
            password = getpass("Crie uma senha forte: ")
            confirmation = getpass("Confirme a senha: ")
            if not password or password != confirmation:
                raise CommandError("As senhas estão vazias ou não conferem.")

        candidate = User(username=username, email="")
        try:
            validate_password(password, user=candidate)
        except Exception as exc:
            if safe_mode:
                self.stderr.write("A senha configurada não passou na validação; nenhuma conta foi criada.")
                return
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
            "Administrador geral criado com sucesso. Nenhuma senha foi exibida."
        ))
