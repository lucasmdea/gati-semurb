"""
core/models.py

Modelagem do domínio do sistema "Atendimentos TI".

Visão geral (resumo):
- Ticket: um atendimento registrado por um técnico (usuário autenticado).
- Supply / TicketSupply: suprimentos "legados" associados ao atendimento.
- AssetType / AssetItem: inventário de ativos com SERIAL (computadores, impressoras, monitores etc).
- StockItem / StockMovement / TicketStockUsage: estoque quantitativo + auditoria + baixa por atendimento.

Obs: comentários aqui são intencionais e servem como guia para manutenção futura.
"""

# Create your models here.
from django.conf import settings
from django.db import models

class Sector(models.Model):
    name = models.CharField(max_length=120, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ServiceType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Supply(models.Model):
    name = models.CharField(max_length=120, unique=True)
    unit = models.CharField(max_length=20, default="un")
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.unit})"
        
class ActivityCategory(models.TextChoices):
    SUPORTE = "SUPORTE", "Suporte"
    EQUIPAMENTOS = "EQUIP", "Equipamentos"
    IMPRESSORAS = "IMPRESS", "Impressoras"


class Activity(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=10, choices=ActivityCategory.choices)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"

class Ticket(models.Model):
    activity = models.ForeignKey(
        Activity,
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True
    )
    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberto"
        IN_PROGRESS = "IN_PROGRESS", "Em andamento"
        DONE = "DONE", "Concluído"
        CANCELED = "CANCELED", "Cancelado"

    # Quem abriu o chamado (usuário do sistema). Mantemos requester_name como "fallback" para casos legados/seed.
    requester_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_tickets",
    )
    requester_name = models.CharField(max_length=120, blank=True)

    sector = models.ForeignKey(Sector, on_delete=models.PROTECT)
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)

    subject = models.CharField(max_length=200)
    description = models.TextField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    # Técnico responsável (pode ser atribuído depois)
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True,
    )

    # Quando foi efetivamente atendido/fechado (pode ser nulo enquanto aberto)
    attended_at = models.DateTimeField(null=True, blank=True)

    # Notas internas (TI)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["attended_at"]),
            models.Index(fields=["technician"]),
            models.Index(fields=["sector"]),
            models.Index(fields=["service_type"]),
            models.Index(fields=["requester_name"]),
        ]
        ordering = ["-created_at", "-id"]

    def requester_display(self) -> str:
        if self.requester_user_id:
            full = (self.requester_user.get_full_name() or "").strip()
            return full or self.requester_user.get_username()
        return self.requester_name or "(sem solicitante)"

    def __str__(self):
        return f"#{self.id} - {self.subject} ({self.get_status_display()})"
class TicketSupply(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="items")
    supply = models.ForeignKey(Supply, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    class Meta:
        unique_together = [("ticket", "supply")]

    def __str__(self):
        return f"{self.supply.name} x {self.quantity}"
class AssetType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de ativo"
        verbose_name_plural = "Tipos de ativos"

    def __str__(self):
        return self.name


class AssetItem(models.Model):
    class Status(models.TextChoices):
        IN_STOCK = "IN_STOCK", "Em estoque"
        IN_USE = "IN_USE", "Em uso"
        MAINTENANCE = "MAINTENANCE", "Em manutenção"
        DISCARDED = "DISCARDED", "Baixado"

    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)
    serial = models.CharField(max_length=120, unique=True)
    tag = models.CharField(max_length=80, blank=True)  # patrimônio/etiqueta
    brand = models.CharField(max_length=80, blank=True)
    model = models.CharField(max_length=120, blank=True)

    sector = models.ForeignKey("Sector", on_delete=models.PROTECT, null=True, blank=True)
    location = models.CharField(max_length=120, blank=True)
    assigned_to = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_STOCK)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ativo (serial)"
        verbose_name_plural = "Ativos (serial)"
        indexes = [models.Index(fields=["serial"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.asset_type.name} - {self.serial}"


class AssetMovement(models.Model):
    class Kind(models.TextChoices):
        MOVE = "MOVE", "Movimentação"
        STATUS = "STATUS", "Mudança de status"
        ASSIGN = "ASSIGN", "Mudança de responsável"

    asset_item = models.ForeignKey(AssetItem, on_delete=models.CASCADE, related_name="movements")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.MOVE)

    from_sector = models.ForeignKey("Sector", on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    to_sector = models.ForeignKey("Sector", on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    from_location = models.CharField(max_length=120, blank=True)
    to_location = models.CharField(max_length=120, blank=True)

    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)

    moved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    moved_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Movimentação de ativo"
        verbose_name_plural = "Movimentações de ativos"
        ordering = ["-moved_at", "-id"]


class StockItem(models.Model):
    name = models.CharField(max_length=120, unique=True)  # Mouse, Teclado, Toner...
    unit = models.CharField(max_length=20, default="un")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Item de estoque"
        verbose_name_plural = "Itens de estoque"

    def __str__(self):
        return f"{self.name} ({self.quantity:g} {self.unit})"


class StockMovement(models.Model):
    class Kind(models.TextChoices):
        IN = "IN", "Entrada"
        OUT = "OUT", "Saída"
        ADJUST = "ADJUST", "Ajuste"

    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name="movements")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)  # sempre positivo
    moved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    moved_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Movimento de estoque"
        verbose_name_plural = "Movimentos de estoque"
        ordering = ["-moved_at", "-id"]


class TicketAsset(models.Model):
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, related_name="assets")
    asset_item = models.ForeignKey(AssetItem, on_delete=models.PROTECT)
    action = models.CharField(max_length=120, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = [("ticket", "asset_item")]
        verbose_name = "Ativo no atendimento"
        verbose_name_plural = "Ativos no atendimento"


class TicketStockUsage(models.Model):
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, related_name="stock_usages")
    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)

    class Meta:
        verbose_name = "Baixa de estoque no atendimento"
        verbose_name_plural = "Baixas de estoque no atendimento"