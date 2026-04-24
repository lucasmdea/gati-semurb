"""core/views.py

Fluxos:
- Solicitante (usuário comum):
  - abre chamado
  - acompanha "Meus chamados"
- Técnico (grupo Tecnicos / superuser):
  - fila de chamados (abertos / em andamento)
  - atendimento (aba Ativos / Estoque + status)

Obs: permissões de "dono do chamado" são controladas aqui (não via perms do Django),
porque o Django não tem object-level perms por padrão.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    RequesterTicketCreateForm,
    TechnicianTicketUpdateForm,
    TicketSupplyFormSet,
    TicketAssetFormSet,
    TicketStockUsageFormSet,
)
from .models import (
    Ticket,
    Sector,
    ServiceType,
    Supply,
    AssetItem,
    TicketAsset,
    StockItem,
    StockMovement,
)

User = get_user_model()


def is_technician(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    group_name = getattr(settings, "TECHNICIANS_GROUP_NAME", "Tecnicos")
    return user.groups.filter(name=group_name).exists()


def technician_required(view_func):
    return login_required(user_passes_test(is_technician)(view_func))


@login_required
def home(request):
    # Home inteligente: técnico cai na fila; solicitante cai em "meus chamados".
    if is_technician(request.user):
        return redirect("tech_queue")
    return redirect("my_tickets")


# ---------------------------
# Solicitante
# ---------------------------

@login_required
def my_tickets(request):
    qs = Ticket.objects.select_related("sector", "service_type", "technician").filter(requester_user=request.user)
    qs = qs.order_by("-created_at")[:200]
    return render(request, "core/my_tickets.html", {"tickets": qs})


@login_required
def ticket_detail(request, pk: int):
    t = get_object_or_404(
        Ticket.objects.select_related("sector", "service_type", "technician")
        .prefetch_related("items__supply", "assets__asset_item", "stock_usages__stock_item"),
        pk=pk,
    )

    if not (is_technician(request.user) or t.requester_user_id == request.user.id):
        return redirect("home")

    return render(request, "core/ticket_detail.html", {"t": t})


@login_required
def ticket_new(request):
    if request.method == "POST":
        form = RequesterTicketCreateForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.requester_user = request.user
            # fallback
            ticket.requester_name = (request.user.get_full_name() or request.user.get_username()).strip()
            ticket.status = Ticket.Status.OPEN
            ticket.save()
            messages.success(request, "Chamado aberto com sucesso.")
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = RequesterTicketCreateForm()

    return render(request, "core/ticket_new.html", {"form": form})


# ---------------------------
# Técnico
# ---------------------------

@technician_required
def tech_queue(request):
    qs = (
        Ticket.objects.select_related("requester_user", "sector", "service_type", "technician")
        .filter(status__in=[Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS])
        .order_by("status", "-created_at")
    )

    # filtros rápidos
    status = request.GET.get("status", "").strip()
    mine = request.GET.get("mine", "").strip()
    q = request.GET.get("q", "").strip()

    if status:
        qs = qs.filter(status=status)
    if mine == "1":
        qs = qs.filter(technician=request.user)
    if q:
        qs = qs.filter(
            Q(subject__icontains=q)
            | Q(description__icontains=q)
            | Q(requester_name__icontains=q)
            | Q(requester_user__username__icontains=q)
        )

    return render(
        request,
        "core/tech_queue.html",
        {
            "tickets": qs[:400],
            "filters": {"status": status, "mine": mine, "q": q},
        },
    )


@technician_required
def tech_ticket_work(request, pk: int):
    ticket = get_object_or_404(
        Ticket.objects.select_related("requester_user", "sector", "service_type", "technician")
        .prefetch_related("items__supply", "assets__asset_item", "stock_usages__stock_item"),
        pk=pk,
    )

    # Se ainda não tem técnico, "assumir" ao entrar
    if ticket.technician_id is None:
        ticket.technician = request.user
        ticket.status = Ticket.Status.IN_PROGRESS if ticket.status == Ticket.Status.OPEN else ticket.status
        ticket.save(update_fields=["technician", "status"])

    if request.method == "POST":
        update_form = TechnicianTicketUpdateForm(request.POST, instance=ticket)
        supply_formset = TicketSupplyFormSet(request.POST, instance=ticket)
        asset_formset = TicketAssetFormSet(request.POST, prefix="assets")
        stock_formset = TicketStockUsageFormSet(request.POST, instance=ticket, prefix="stock")

        if update_form.is_valid() and supply_formset.is_valid() and asset_formset.is_valid() and stock_formset.is_valid():
            try:
                with transaction.atomic():
                    update_form.save()

                    # Suprimentos (legado)
                    supply_formset.save()

                    # Ativos por serial (sem duplicar)
                    seen_serials = set()
                    for row in asset_formset.cleaned_data:
                        if not row or row.get("DELETE"):
                            continue
                        serial = (row.get("serial") or "").strip()
                        if not serial:
                            continue
                        serial_key = serial.lower()
                        if serial_key in seen_serials:
                            continue
                        seen_serials.add(serial_key)

                        asset_item = AssetItem.objects.get(serial__iexact=serial)
                        TicketAsset.objects.get_or_create(
                            ticket=ticket,
                            asset_item=asset_item,
                            defaults={
                                "action": (row.get("action") or "").strip(),
                                "note": (row.get("note") or "").strip(),
                            },
                        )

                    # Baixa de estoque (quantitativos)
                    stock_usages = stock_formset.save(commit=False)

                    # Agregar por item
                    to_decrement: dict[int, Decimal] = {}
                    for u in stock_usages:
                        if not u.stock_item_id:
                            continue
                        qty = u.quantity or Decimal("0")
                        if qty <= 0:
                            continue
                        to_decrement[u.stock_item_id] = to_decrement.get(u.stock_item_id, Decimal("0")) + qty

                    if to_decrement:
                        items = StockItem.objects.select_for_update().filter(id__in=to_decrement.keys())
                        items_map = {i.id: i for i in items}

                        for item_id, qty in to_decrement.items():
                            item = items_map[item_id]
                            if item.quantity - qty < 0:
                                raise ValueError(
                                    f"Estoque insuficiente para '{item.name}'. Saldo: {item.quantity:g} {item.unit}"
                                )

                        for u in stock_usages:
                            qty = u.quantity or Decimal("0")
                            if not u.stock_item_id or qty <= 0:
                                continue
                            u.ticket = ticket
                            u.save()

                        for item_id, qty in to_decrement.items():
                            item = items_map[item_id]
                            item.quantity -= qty
                            item.save(update_fields=["quantity"])

                            StockMovement.objects.create(
                                stock_item=item,
                                kind=StockMovement.Kind.OUT,
                                quantity=qty,
                                moved_by=request.user,
                                note=f"Baixa por chamado #{ticket.id}",
                            )

                    stock_formset.save_m2m()
                    for obj in stock_formset.deleted_objects:
                        obj.delete()

                messages.success(request, "Chamado atualizado.")
                return redirect("tech_ticket_work", pk=ticket.pk)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Corrija os campos destacados.")

    else:
        update_form = TechnicianTicketUpdateForm(instance=ticket)
        supply_formset = TicketSupplyFormSet(instance=ticket)
        asset_formset = TicketAssetFormSet(prefix="assets")
        stock_formset = TicketStockUsageFormSet(instance=ticket, prefix="stock")

    return render(
        request,
        "core/tech_ticket_work.html",
        {
            "ticket": ticket,
            "update_form": update_form,
            "supply_formset": supply_formset,
            "asset_formset": asset_formset,
            "stock_formset": stock_formset,
        },
    )


@technician_required
def tech_ticket_list(request):
    # Listagem completa (inclui concluídos) com filtros parecidos com o antigo ticket_list.
    qs = (
        Ticket.objects.select_related("technician", "sector", "service_type", "requester_user")
        .prefetch_related("items__supply", "assets__asset_item", "stock_usages__stock_item")
    )

    status = request.GET.get("status", "").strip()
    tech_id = request.GET.get("tech", "").strip()
    sector_id = request.GET.get("sector", "").strip()
    type_id = request.GET.get("type", "").strip()
    requester = request.GET.get("requester", "").strip()
    q = request.GET.get("q", "").strip()
    serial = request.GET.get("serial", "").strip()

    if status:
        qs = qs.filter(status=status)
    if tech_id:
        qs = qs.filter(technician_id=tech_id)
    if sector_id:
        qs = qs.filter(sector_id=sector_id)
    if type_id:
        qs = qs.filter(service_type_id=type_id)
    if requester:
        qs = qs.filter(Q(requester_name__icontains=requester) | Q(requester_user__username__icontains=requester))
    if q:
        qs = qs.filter(Q(subject__icontains=q) | Q(description__icontains=q) | Q(notes__icontains=q))
    if serial:
        qs = qs.filter(assets__asset_item__serial__icontains=serial).distinct()

    return render(
        request,
        "core/tech_ticket_list.html",
        {
            "tickets": qs.order_by("-created_at")[:700],
            "techs": User.objects.filter(is_active=True).order_by("first_name", "username"),
            "sectors": Sector.objects.filter(active=True).order_by("name"),
            "types": ServiceType.objects.filter(active=True).order_by("name"),
            "supplies": Supply.objects.filter(active=True).order_by("name"),
            "filters": {
                "status": status,
                "tech": tech_id,
                "sector": sector_id,
                "type": type_id,
                "requester": requester,
                "q": q,
                "serial": serial,
            },
            "status_choices": Ticket.Status.choices,
        },
    )
