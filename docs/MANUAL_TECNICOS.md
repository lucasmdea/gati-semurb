# Manual dos Técnicos — Atendimentos TI (SEMURB)

Este manual é para uso diário (sem detalhes técnicos de programação).

---

## 1) Acessar o sistema

1. Abra o navegador (Chrome/Firefox).
2. Acesse: `http://IP_DO_HOST:8000/`
3. Faça login com seu usuário e senha.

Se você não tiver usuário, peça para a equipe de TI criar via Admin.

---

## 2) Registrar um novo atendimento

1. Clique no botão **Novo** (no topo).
2. Aba **Novo atendimento**:
   - Data/Hora: confirme se está correto
   - Setor: selecione o setor atendido
   - Tipo de atendimento: selecione (ex.: Suporte, Manutenção...)
   - Solicitante: digite o nome de quem pediu
   - Observações: detalhe o que foi feito (quanto mais claro, melhor)

3. (Opcional) Aba **Ativos**
   - Preencha o **Serial** do equipamento atendido (ex.: PC-001-ABC).
   - Se o serial não existir, o sistema avisa. Nesse caso, peça para cadastrar o ativo no Admin.

4. (Opcional) Aba **Baixa de estoque**
   - Se utilizou itens (mouse, teclado, toner...), selecione o item e informe quantidade.
   - O sistema dá baixa automática no estoque.

5. Clique em **Salvar**.

---

## 3) Consultar atendimentos (filtros)

Na tela principal (lista de atendimentos), use os filtros:
- por setor
- por tipo
- por solicitante
- por serial do ativo (quando habilitado na listagem)

Dica: use parte do nome (ex.: “joão”) para achar mais rápido.

---

## 4) Regras importantes (para não dar problema)

- Não invente serial: se não souber, deixe em branco e anote na observação.
- Se retirar item do estoque, registre em **Baixa de estoque**.
- Observações devem permitir que outro técnico entenda o que foi feito.

---

## 5) Problemas comuns

### “Serial não encontrado”
O equipamento ainda não está cadastrado no inventário.
- Solução: pedir para cadastrar no Admin (Inventário → Ativos (serial)).

### “Estoque insuficiente”
O item não tem saldo suficiente.
- Solução: registrar entrada/ajuste no estoque via Admin (Itens de estoque).

### Não consigo entrar (senha)
- Solução: pedir reset de senha para o administrador do sistema.

---

## 6) O que é o Admin e quem usa?

O **Admin** é para a equipe responsável por cadastros (normalmente TI):
- Setores
- Tipos de atendimento
- Inventário (ativos com serial)
- Estoque (quantidades e movimentações)

URL: `http://IP_DO_HOST:8000/admin/`

Se você não tem permissão, não se preocupe — use apenas o sistema principal.
