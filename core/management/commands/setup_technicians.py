"""core.management.commands.setup_technicians

Cria (ou atualiza) o grupo de Técnicos e aplica permissões mínimas para operação.

Uso típico (no container):

  docker compose run --rm web python manage.py setup_technicians

Opcional:
  - Adicionar usuários específicos ao grupo e marcar como staff:
      python manage.py setup_technicians --users joao maria
  - Adicionar automaticamente todos os usuários que já são staff (exceto superuser):
      python manage.py setup_technicians --include-existing-staff
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
    help = "Cria/atualiza o grupo de Técnicos com permissões mínimas (admin enxuto)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--group",
            default=getattr(settings, "TECHNICIANS_GROUP_NAME", "Tecnicos"),
            help="Nome do grupo de técnicos (default: settings.TECHNICIANS_GROUP_NAME ou 'Tecnicos').",
        )
        parser.add_argument(
            "--users",
            nargs="*",
            default=[],
            help="Usernames para adicionar ao grupo (também marca is_staff=True).",
        )
        parser.add_argument(
            "--include-existing-staff",
            action="store_true",
            help="Adiciona automaticamente ao grupo todos os usuários que já são staff (exceto superuser).",
        )
        parser.add_argument(
            "--include-all-non-superusers",
            action="store_true",
            help="Adiciona ao grupo TODOS os usuários que não são superuser (use com cuidado).",
        )

    def handle(self, *args, **options):
        group_name: str = options["group"]
        group, created = Group.objects.get_or_create(name=group_name)

        # Permissões mínimas por modelo
        desired = [
            # Cadastros-base (consulta apenas)
            ModelPerms("core", "sector", ("view",)),
            ModelPerms("core", "servicetype", ("view",)),
            ModelPerms("core", "supply", ("view",)),
            ModelPerms("core", "assettype", ("view",)),

            # Operação: inventário e estoque
            ModelPerms("core", "assetitem", ("add", "change", "view")),
            ModelPerms("core", "stockitem", ("add", "change", "view")),

            # Auditoria: movimentos (permitir adicionar via inline, sem deletar/editar)
            ModelPerms("core", "assetmovement", ("add", "view")),
            ModelPerms("core", "stockmovement", ("add", "view")),

            # Tickets (fluxo via UI)
            ModelPerms("core", "ticket", ("add", "change", "view")),
            ModelPerms("core", "ticketsupply", ("add", "change", "view")),
            ModelPerms("core", "ticketasset", ("add", "change", "view")),
            ModelPerms("core", "ticketstockusage", ("add", "change", "view")),
        ]

        perms = self._resolve_permissions(desired)
        group.permissions.set(perms)

        # Usuários
        User = get_user_model()
        added_users = 0
        updated_staff = 0

        qset = User.objects.none()
        if options["include_all_non_superusers"]:
            qset = User.objects.filter(is_superuser=False)
        elif options["include_existing_staff"]:
            qset = User.objects.filter(is_staff=True, is_superuser=False)

        # Adiciona usuários selecionados
        if qset.exists():
            for u in qset:
                group.user_set.add(u)
                added_users += 1

        # Adiciona usernames explícitos
        usernames: list[str] = options.get("users") or []
        if usernames:
            missing = []
            for username in usernames:
                try:
                    u = User.objects.get(username=username)
                except User.DoesNotExist:
                    missing.append(username)
                    continue
                if not u.is_staff:
                    u.is_staff = True
                    u.save(update_fields=["is_staff"])
                    updated_staff += 1
                group.user_set.add(u)
                added_users += 1

            if missing:
                self.stdout.write(self.style.WARNING(f"Usernames não encontrados: {', '.join(missing)}"))

        # Garante que quem está no grupo é staff (admin exige is_staff)
        for u in group.user_set.filter(is_superuser=False, is_staff=False):
            u.is_staff = True
            u.save(update_fields=["is_staff"])
            updated_staff += 1

        if created:
            self.stdout.write(self.style.SUCCESS(f"Grupo criado: {group_name}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Grupo atualizado: {group_name}"))

        self.stdout.write(self.style.SUCCESS(f"Permissões aplicadas: {len(perms)}"))
        self.stdout.write(self.style.SUCCESS(f"Usuários adicionados ao grupo: {added_users}"))
        if updated_staff:
            self.stdout.write(self.style.SUCCESS(f"Usuários marcados como staff: {updated_staff}"))

    def _resolve_permissions(self, desired: list[ModelPerms]) -> list[Permission]:
        perms: list[Permission] = []
        missing: list[str] = []

        for entry in desired:
            try:
                ct = ContentType.objects.get(app_label=entry.app_label, model=entry.model)
            except ContentType.DoesNotExist:
                missing.append(f"{entry.app_label}.{entry.model} (ContentType)")
                continue

            for cod in entry.codenames:
                full = f"{cod}_{entry.model}"
                try:
                    p = Permission.objects.get(content_type=ct, codename=full)
                    perms.append(p)
                except Permission.DoesNotExist:
                    missing.append(f"{entry.app_label}.{entry.model}:{full}")

        if missing:
            # Não falha duro: costuma acontecer antes da 1ª migrate.
            self.stdout.write(self.style.WARNING(
                "Algumas permissões não foram encontradas (rode migrate primeiro).\n- " + "\n- ".join(missing)
            ))

        # Remove duplicadas mantendo ordem
        seen = set()
        unique: list[Permission] = []
        for p in perms:
            if p.pk in seen:
                continue
            seen.add(p.pk)
            unique.append(p)
        return unique
