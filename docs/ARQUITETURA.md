# Arquitetura rápida (para manutenção)

## Domínio
- **Ticket**: atendimento registrado por um técnico.
- **Supply / TicketSupply**: suprimentos "legados" (lista simples por atendimento).
- **AssetItem**: ativo com serial (inventário).
- **TicketAsset**: vínculo N:N entre atendimento e ativo (histórico por serial).
- **StockItem**: item de estoque com saldo.
- **StockMovement**: auditoria de entradas/saídas/ajustes do estoque.
- **TicketStockUsage**: baixa de estoque ligada ao atendimento.

## Fluxo de gravação do atendimento
A tela `ticket_form.html` envia um único POST:
1) Cria `Ticket`
2) Salva `TicketSupply` (suprimentos)
3) Valida seriais e cria `TicketAsset`
4) Para estoque: agrega quantidades, trava linhas com `select_for_update()`, valida saldo, baixa e cria `StockMovement`

Arquivo chave: `core/views.py` (função `ticket_create`).
