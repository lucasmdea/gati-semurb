"""core.management.commands.setup_roles

Padroniza papéis do sistema:
- Grupo de Técnicos (Tecnicos): atende chamados, opera inventário/estoque.
- Grupo de Usuários (Usuarios): abre chamados e acompanha os próprios.

Uso típico:
  docker compose run --rm web python manage.py setup_roles --include-all-users

Opcional:
  - Definir nomes dos grupos:
      python manage.py setup_roles --tech-group Tecnicos --user-group Usuarios
  - Adicionar técnicos por username:
      python manage.py setup_roles --tech-users tecnico1 tecnico2
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


@dataclass(frozen=True)
class ModelPerms:
    app_label: str
    model: str
    codenames: tuple[str, ...]


class Command(BaseCommand):
    help = "Cria/atualiza grupos de Usuários e Técnicos com permissões mínimas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tech-group",
            default=getattr(settings, "TECHNICIANS_GROUP_NAME", "Tecnicos"),
            help="Nome do grupo de técnicos.",
        )
        parser.add_argument(
            "--user-group",
            default=getattr(settings, "REQUESTERS_GROUP_NAME", "Usuarios"),
            help="Nome do grupo de usuários/solicitantes.",
        )
        parser.add_argument(
            "--tech-users",
            nargs="*",
            default=[],
            help="Usernames para adicionar ao grupo de técnicos (marca is_staff=True).",
        )
        parser.add_argument(
            "--include-all-users",
            action="store_true",
            help="Adiciona automaticamente todos os usuários que não são superuser ao grupo de usuários.",
        )

    def handle(self, *args, **options):
        tech_group_name: str = options["tech_group"]
        user_group_name: str = options["user_group"]

        tech_group, _ = Group.objects.get_or_create(name=tech_group_name)
        user_group, _ = Group.objects.get_or_create(name=user_group_name)

        # Permissões do solicitante: abre e vê chamado (restrição de 'dono' é na view)
        user_perms = self._resolve_permissions([
            ModelPerms("core", "ticket", ("add", "view")),
        ])
        user_group.permissions.set(user_perms)

        # Permissões do técnico: atende e opera inventário/estoque
        tech_perms = self._resolve_permissions([
            ModelPerms("core", "sector", ("view",)),
            ModelPerms("core", "servicetype", ("view",)),
            ModelPerms("core", "supply", ("view",)),
            ModelPerms("core", "assettype", ("view",)),

            ModelPerms("core", "assetitem", ("add", "change", "view")),
            ModelPerms("core", "stockitem", ("add", "change", "view")),

            ModelPerms("core", "assetmovement", ("add", "view")),
            ModelPerms("core", "stockmovement", ("add", "view")),

            ModelPerms("core", "ticket", ("add", "change", "view")),
            ModelPerms("core", "ticketsupply", ("add", "change", "view")),
            ModelPerms("core", "ticketasset", ("add", "change", "view")),
            ModelPerms("core", "ticketstockusage", ("add", "change", "view")),
        ])
        tech_group.permissions.set(tech_perms)

        User = get_user_model()

        added_users = 0
        if options["include_all_users"]:
            for u in User.objects.filter(is_superuser=False):
                user_group.user_set.add(u)
                added_users += 1

        tech_added = 0
        tech_staffed = 0
        for username in options.get("tech_users") or []:
            try:
                u = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Username não encontrado: {username}"))
                continue
            if not u.is_staff:
                u.is_staff = True
                u.save(update_fields=["is_staff"])
                tech_staffed += 1
            tech_group.user_set.add(u)
            tech_added += 1

        self.stdout.write(self.style.SUCCESS(f"Grupo usuários: {user_group_name} (perms: {len(user_perms)})"))
        self.stdout.write(self.style.SUCCESS(f"Grupo técnicos: {tech_group_name} (perms: {len(tech_perms)})"))
        if added_users:
            self.stdout.write(self.style.SUCCESS(f"Usuários adicionados ao grupo de usuários: {added_users}"))
        if tech_added:
            self.stdout.write(self.style.SUCCESS(f"Técnicos adicionados: {tech_added} (staff marcados: {tech_staffed})"))

    def _resolve_permissions(self, desired: list[ModelPerms]) -> list[Permission]:
        perms: list[Permission] = []
        missing: list[str] = []

        for entry in desired:
            try:
                ct = ContentType.objects.get(app_label=entry.app_label, model=entry.model)
            except ContentType.DoesNotExist:
                missing.append(f"{entry.app_label}.{entry.model}")
                continue

            for prefix in entry.codenames:
                codename = f"{prefix}_{entry.model}"
                try:
                    p = Permission.objects.get(content_type=ct, codename=codename)
                    perms.append(p)
                except Permission.DoesNotExist:
                    missing.append(codename)

        if missing:
            self.stdout.write(self.style.WARNING("Permissões não encontradas (execute migrate primeiro):"))
            for x in missing:
                self.stdout.write(self.style.WARNING(f" - {x}"))

        return perms
