"""core/admin.py

Admin "enxuto" voltado ao que um técnico precisa.

Regras:
- Superuser: tudo.
- Técnico (grupo Tecnicos):
  - Consulta apenas em cadastros-base (setores, tipos, suprimentos).
  - Opera inventário (AssetItem) e estoque (StockItem).
  - Movimentos ficam como auditoria/inlines (não aparecem no menu).
  - Tickets no admin são consulta (operação real é pela UI do sistema).

Obs: as permissões do grupo são definidas pelo comando:
  python manage.py setup_technicians
"""

from __future__ import annotations

from django.contrib import admin

from .models import (
    AssetItem,
    AssetMovement,
    AssetType,
    Sector,
    ServiceType,
    StockItem,
    StockMovement,
    Supply,
    Ticket,
    TicketSupply,
    Activity
)


class ReadOnlyForNonSuperuser(admin.ModelAdmin):
    """Base: deixa CRUD completo para superuser, e somente leitura para o resto."""

    def has_add_permission(self, request):
        return bool(request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_superuser)


class AssetMovementInline(admin.TabularInline):
    model = AssetMovement
    extra = 0
    readonly_fields = ("moved_at", "moved_by")
    autocomplete_fields = ("from_sector", "to_sector")

    def has_change_permission(self, request, obj=None):
        # Técnicos não editam histórico
        return bool(request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_superuser)


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ("moved_at", "moved_by")

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_superuser)


@admin.register(Sector)
class SectorAdmin(ReadOnlyForNonSuperuser):
    list_display = ("name", "active")
    list_filter = ("active",)
    search_fields = ("name",)


@admin.register(ServiceType)
class ServiceTypeAdmin(ReadOnlyForNonSuperuser):
    list_display = ("name", "active")
    list_filter = ("active",)
    search_fields = ("name",)


@admin.register(Supply)
class SupplyAdmin(ReadOnlyForNonSuperuser):
    list_display = ("name", "unit", "active")
    list_filter = ("active", "unit")
    search_fields = ("name",)


@admin.register(AssetType)
class AssetTypeAdmin(ReadOnlyForNonSuperuser):
    list_display = ("name", "active")
    list_filter = ("active",)
    search_fields = ("name",)


@admin.register(AssetItem)
class AssetItemAdmin(admin.ModelAdmin):
    list_display = ("serial", "asset_type", "status", "sector", "assigned_to", "location")
    list_filter = ("asset_type", "status", "sector")
    search_fields = ("serial", "tag", "brand", "model", "assigned_to", "location")
    autocomplete_fields = ("asset_type", "sector")
    inlines = [AssetMovementInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for inst in instances:
            # Seta auditoria automaticamente quando criado via inline
            if isinstance(inst, AssetMovement) and not inst.moved_by_id:
                inst.moved_by = request.user
            inst.save()
        formset.save_m2m()


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "unit", "min_quantity", "active")
    list_filter = ("active", "unit")
    search_fields = ("name",)
    inlines = [StockMovementInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for inst in instances:
            if isinstance(inst, StockMovement) and not inst.moved_by_id:
                inst.moved_by = request.user
            inst.save()
        formset.save_m2m()


class TicketSupplyInline(admin.TabularInline):
    model = TicketSupply
    extra = 0

    def has_add_permission(self, request, obj=None):
        return bool(request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_superuser)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "status", "subject", "sector", "service_type", "requester_name", "technician")
    list_filter = ("status", "sector", "service_type", "technician")
    search_fields = ("subject", "description", "notes", "requester_name", "requester_user__username")
    date_hierarchy = "created_at"
    inlines = [TicketSupplyInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Técnico consulta apenas os chamados atribuídos a ele
        return qs.filter(technician=request.user)

    def has_add_permission(self, request):
        return bool(request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_superuser)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)
