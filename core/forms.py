"""core/forms.py

Formulários do Django usados nas telas do sistema.

Dois fluxos principais:
- Usuário (solicitante): abre um chamado (Ticket) com assunto e descrição.
- Técnico: atende o chamado, podendo registrar ativos/baixa de estoque e finalizar.

Obs:
- Permissões e restrições por papel ficam nas views (e no admin enxuto).
"""

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory, inlineformset_factory
from django.utils import timezone

from .models import (
    Ticket,
    TicketSupply,
    Sector,
    ServiceType,
    AssetItem,
    TicketStockUsage,
    StockItem,
)


class RequesterTicketCreateForm(forms.ModelForm):
    """Form do usuário (solicitante) para abrir chamado."""

    class Meta:
        model = Ticket
        fields = ["sector", "service_type", "activity", "subject", "description"]

        widgets = {
            "subject": forms.TextInput(attrs={"placeholder": "Ex.: Computador não liga"}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Descreva o problema, local e qualquer detalhe útil"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].queryset = Sector.objects.filter(active=True).order_by("name")
        self.fields["service_type"].queryset = ServiceType.objects.filter(active=True).order_by("name")


class TechnicianTicketUpdateForm(forms.ModelForm):
    """Form do técnico para atualizar status/nota e finalizar."""

    attended_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text="Preencha ao concluir o atendimento (opcional).")

    class Meta:
        model = Ticket
        fields = ["status", "attended_at", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4, "placeholder": "Notas internas (TI)"}),
        }

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        attended_at = cleaned.get("attended_at")

        if status == Ticket.Status.DONE and not attended_at:
            cleaned["attended_at"] = timezone.now()
        return cleaned


# ---- Suprimentos (legado) ----

TicketSupplyFormSet = inlineformset_factory(
    Ticket,
    TicketSupply,
    fields=("supply", "quantity"),
    extra=1,
    can_delete=True,
    widgets={
        "quantity": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
    },
)


# ---- Ativos por serial (formset simples) ----

class TicketAssetRowForm(forms.Form):
    serial = forms.CharField(required=False, max_length=120)
    action = forms.CharField(required=False, max_length=120)
    note = forms.CharField(required=False, max_length=255)

    def clean_serial(self):
        serial = (self.cleaned_data.get("serial") or "").strip()
        if not serial:
            return ""
        try:
            AssetItem.objects.get(serial__iexact=serial)
        except AssetItem.DoesNotExist:
            raise ValidationError("Serial não encontrado no inventário.")
        return serial


TicketAssetFormSet = formset_factory(
    TicketAssetRowForm,
    extra=2,
    can_delete=True,
)


# ---- Baixa de estoque ----

class TicketStockUsageForm(forms.ModelForm):
    class Meta:
        model = TicketStockUsage
        fields = ("stock_item", "quantity")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stock_item"].queryset = StockItem.objects.filter(active=True).order_by("name")
        self.fields["quantity"].widget = forms.NumberInput(attrs={"step": "0.01", "min": "0"})


TicketStockUsageFormSet = inlineformset_factory(
    parent_model=__import__("core.models").models.Ticket,
    model=TicketStockUsage,
    form=TicketStockUsageForm,
    fields=("stock_item", "quantity"),
    extra=2,
    can_delete=True,
)
