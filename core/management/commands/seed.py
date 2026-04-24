"""
seed.py (manage.py seed)

Este comando popula dados iniciais do sistema para uso rápido:
- Setores
- Tipos de atendimento
- Suprimentos
- Tipos de ativo e alguns ativos de exemplo
- Itens de estoque com quantidades iniciais

Importante:
- Usa get_or_create para ser idempotente (pode rodar mais de uma vez sem duplicar).
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from core.models import (
    Activity,
    ActivityCategory,
    Sector,
    ServiceType,
    Supply,
    AssetType,
    AssetItem,
    StockItem
)

User = get_user_model()


class Command(BaseCommand):
    help = "Popula dados iniciais do sistema (seed)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Iniciando seed do sistema..."))
        
        seed_activities()

        # -------------------------
        # SETORES
        # -------------------------
        sectors = [
            "Central de Atendimento",
            "Recepçao",
            "SLE",
            "DLOS",
            "SLOPU",
            "SLOPR",
            "SCT",
            "SPA",
            "SGFU",
            "SGFA",
            "GAB",
            "IMP",
            "ATEC",
            "DAGE",
            "AJUR",
            "SADRH",
            "SJPI",
            "DGP",
            "DICP",
            "SACT",
            "CONPLAM",
            "SPUA",
            "SMCA",
            "OUV",
        ]

        for s in sectors:
            Sector.objects.get_or_create(name=s, defaults={"active": True})

        self.stdout.write(self.style.SUCCESS("✔ Setores criados"))

        # -------------------------
        # TIPOS DE ATENDIMENTO
        # -------------------------
        service_types = [
            "HelpDesk",
            "Manutençao Preventiva",
            "Manutencao Corretiva",
            "Substituiçao de Suprimento",
        ]

        for st in service_types:
            ServiceType.objects.get_or_create(name=st, defaults={"active": True})

        self.stdout.write(self.style.SUCCESS("✔ Tipos de atendimento criados"))

        # -------------------------
        # SUPRIMENTOS (legado / simples)
        # -------------------------
        supplies = [
            "Mouse",
            "Teclado",
            "Monitor",
            "HP ELite Desk",
            "Positivo Master D6200",
            "Positivo Master MiniPRO C8200",
            "HP Compaq 6005 Pro",
            "All-In-One Dell",
            "ALL-In-One LG",
            "Miranda L4100",
            "Modulo Isolador",
            "Estabilizador",
            "Cabo de rede",
            "RJ-45",
            "Tonner 4080",
            "Tonner 4020",
            "Tonner 4062",
            "Tonner 7400",
        ]

        for sup in supplies:
            Supply.objects.get_or_create(name=sup, defaults={"active": True})

        self.stdout.write(self.style.SUCCESS("✔ Suprimentos criados"))

        # -------------------------
        # TIPOS DE ATIVO (SERIAL)
        # -------------------------
        asset_types = [
            "Computador",
            "Impressora",
            "Monitor",
            "Scanner de Mesa",
        ]

        asset_type_objs = {}
        for at in asset_types:
            obj, _ = AssetType.objects.get_or_create(name=at, defaults={"active": True})
            asset_type_objs[at] = obj

        self.stdout.write(self.style.SUCCESS("✔ Tipos de ativo criados"))

        # -------------------------
        # ATIVOS COM SERIAL (EXEMPLOS)
        # -------------------------
        assets = [
            {
                "asset_type": "Computador",
                "serial": "PC-001-ABC",
                "brand": "Dell",
                "model": "OptiPlex 3080",
                "status": AssetItem.Status.IN_USE,
            },
            {
                "asset_type": "Monitor",
                "serial": "MON-002-XYZ",
                "brand": "LG",
                "model": "24MK430",
                "status": AssetItem.Status.IN_USE,
            },
            {
                "asset_type": "Impressora",
                "serial": "IMP-003-QWE",
                "brand": "HP",
                "model": "LaserJet M404",
                "status": AssetItem.Status.IN_STOCK,
            },
        ]

        for a in assets:
            AssetItem.objects.get_or_create(
                serial=a["serial"],
                defaults={
                    "asset_type": asset_type_objs[a["asset_type"]],
                    "brand": a.get("brand", ""),
                    "model": a.get("model", ""),
                    "status": a.get("status", AssetItem.Status.IN_STOCK),
                },
            )

        self.stdout.write(self.style.SUCCESS("✔ Ativos com serial criados"))

        # -------------------------
        # ITENS DE ESTOQUE (QUANTITATIVOS)
        # -------------------------
        stock_items = [
            {"name": "Mouse", "unit": "un", "quantity": 50, "min_quantity": 10},
            {"name": "Teclado", "unit": "un", "quantity": 40, "min_quantity": 10},
            {"name": "Monitor", "unit": "un", "quantity": 15, "min_quantity": 5},
        ]

        for item in stock_items:
            StockItem.objects.get_or_create(
                name=item["name"],
                defaults={
                    "unit": item["unit"],
                    "quantity": item["quantity"],
                    "min_quantity": item["min_quantity"],
                    "active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("✔ Itens de estoque criados"))

        self.stdout.write(self.style.SUCCESS("✅ Seed finalizado com sucesso!"))

def seed_activities():
    data = [
        # SUPORTE
        ("Email Institucionais", ActivityCategory.SUPORTE),
        ("Directa", ActivityCategory.SUPORTE),
        ("E-Doc", ActivityCategory.SUPORTE),
        ("Licenças de Software", ActivityCategory.SUPORTE),

        # EQUIPAMENTOS
        ("Manutenção Preventiva", ActivityCategory.EQUIPAMENTOS),
        ("Manutenção Corretiva", ActivityCategory.EQUIPAMENTOS),
        ("Reparos", ActivityCategory.EQUIPAMENTOS),
        ("Gerenciamento de Estoque de Ativos", ActivityCategory.EQUIPAMENTOS),

        # IMPRESSORAS
        ("Abertura de Chamados", ActivityCategory.IMPRESSORAS),
        ("Controle de Suprimentos", ActivityCategory.IMPRESSORAS),
        ("Cadastro de Atividades", ActivityCategory.IMPRESSORAS),
]

    for name, category in data:
        Activity.objects.get_or_create(name=name, category=category)
