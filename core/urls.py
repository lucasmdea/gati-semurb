from django.urls import path
from . import views
from .views import stock_overview, stock_entry

urlpatterns = [
    path("", views.home, name="home"),

    path("estoque/", stock_overview, name="stock_overview"),
    path("estoque/entrada/", stock_entry, name="stock_entry"),

    # Solicitante
    path("meus/", views.my_tickets, name="my_tickets"),
    path("novo/", views.ticket_new, name="ticket_new"),
    path("chamado/<int:pk>/", views.ticket_detail, name="ticket_detail"),

    # Técnico
    path("ti/fila/", views.tech_queue, name="tech_queue"),
    path("ti/chamado/<int:pk>/", views.tech_ticket_work, name="tech_ticket_work"),
    path("ti/lista/", views.tech_ticket_list, name="tech_ticket_list"),
]
