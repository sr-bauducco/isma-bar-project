# Bar SMA

Simulação de bares com agentes [SPADE](https://spade-mas.readthedocs.io/): cada **Bar** cria seus **Atendentes** e **Faxineiras**, e **Clientes** entram, pedem, avaliam e saem, tudo por troca de mensagens.

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py               # 3 bares, 30 dias simulados, 1 dia = 60 s (mês em 30 min)
python main.py --dia 2       # acelerado: 1 dia = 2 s (mês em 1 min)
python main.py --dia 5 --dias 7   # só 1 semana, 1 dia = 5 s
```

Painel: http://127.0.0.1:10000/painel (mostra dia, hora e semana da simulação).

---

## Tempo da simulação

Todo tempo é **simulado** e passa pelo [relogio.py](relogio.py): `relogio.minutos(10)`, `relogio.horas(1)`, `relogio.semanas(1)` devolvem quantos segundos **reais** isso dura na escala atual. Por isso mudar `--dia` acelera ou desacelera tudo por igual.

| 1 dia = | 1 semana | 1 mês |
|---|---|---|
| 60 s (padrão) | 7 min | 30 min |
| 5 s | 35 s | 2,5 min |
| 2 s | 14 s | 1 min |

- O relógio só começa **depois** que todos os agentes sobem; ao fim de `--dias` a simulação encerra sozinha.
- Escala abaixo de ~2 s/dia começa a distorcer: o atraso real das mensagens XMPP (alguns ms) não acelera junto.
- Ao criar algo com duração, use o relógio, nunca segundos fixos: `asyncio.sleep(relogio.minutos(10))`.

---

## Fluxo de pedidos

### Visão geral

```mermaid
sequenceDiagram
    autonumber
    participant C as Cliente
    participant B as Bar
    participant A as Atendente

    C->>B: request / entrar
    B-->>C: agree / entrar {clientes, lotacao_maxima}

    C->>B: request / pedido {"item": "cerveja"}
    Note over B: ReceberPedido<br/>valida e põe na fila_pedidos
    B-->>C: agree / pedido {pedido_id, preco, posicao}

    Note over B: distribuir() na hora:<br/>tem atendente livre? (senão espera na fila)
    B->>A: request / preparar {pedido_id, cliente, item, preco}
    Note over B: pedido sai da fila e vai<br/>para pedidos_em_preparo

    Note over A: PrepararPedido<br/>is_serving = True<br/>espera TEMPO_PREPARO_MINUTOS (10 min simulados)
    A->>C: inform / entrega {pedido_id, item, preco, bar, atendente}
    A->>B: inform / pedido_pronto {pedido_id}
    Note over B: ReceberPedidoPronto<br/>libera o atendente, registra a espera (min simulados)<br/>e chama distribuir() para o próximo da fila

    C->>B: inform / avaliacao "atendimento:9"
    C->>B: inform / sair
```

### Quando o bar recusa

```mermaid
flowchart TD
    E["request / entrar"] --> E1{bar aberto?}
    E1 -- não --> R1["refuse {motivo: fechado}"]
    E1 -- sim --> E2{"já está dentro<br/>ou tem vaga?"}
    E2 -- não --> R2["refuse {motivo: lotado}"]
    E2 -- sim --> OK1["agree / entrar<br/>cliente entra em bar.clientes"]

    P["request / pedido"] --> P0{body é JSON?}
    P0 -- não --> R3["refuse {motivo: formato_invalido}"]
    P0 -- sim --> P1{bar aberto?}
    P1 -- não --> R4["refuse {motivo: fechado}"]
    P1 -- sim --> P2{cliente está dentro?}
    P2 -- não --> R5["refuse {motivo: fora_do_bar}"]
    P2 -- sim --> P3{item no cardápio?}
    P3 -- não --> R6["refuse {motivo: item_inexistente,<br/>cardapio: {...}}"]
    P3 -- sim --> OK2["agree / pedido<br/>pedido entra na fila_pedidos"]
```

### Vida de um pedido

```mermaid
stateDiagram-v2
    direction LR
    [*] --> NaFila: ReceberPedido<br/>(agree)
    NaFila --> EmPreparo: distribuir()<br/>(atendente livre)
    EmPreparo --> Entregue: PrepararPedido<br/>(entrega + pedido_pronto)
    Entregue --> [*]: ReceberPedidoPronto<br/>(mede espera)

    NaFila: na fila<br/>bar.fila_pedidos
    EmPreparo: em preparo<br/>bar.pedidos_em_preparo
    Entregue: entregue<br/>bar.tempos_espera
```

---

## Mensagens

Toda mensagem tem `performative` + `ontology`. O bar só entrega cada mensagem ao behaviour cujo `Template` bate com esses dois valores; **mensagem sem `ontology` é ignorada sem erro**.

| De → Para | performative | ontology | body (JSON) | Resposta |
|---|---|---|---|---|
| Cliente → Bar | `request` | `entrar` | — | `agree` `{clientes, lotacao_maxima}` · `refuse` `{motivo}` |
| Cliente → Bar | `request` | `pedido` | `{"item": "cerveja"}` | `agree` `{pedido_id, item, preco, posicao}` · `refuse` `{motivo}` |
| Bar → Atendente | `request` | `preparar` | `{pedido_id, cliente, item, preco}` | — |
| Atendente → Cliente | `inform` | `entrega` | `{pedido_id, item, preco, bar, atendente}` | — |
| Atendente → Bar | `inform` | `pedido_pronto` | `{pedido_id}` | — |
| Cliente → Bar | `query-ref` | `avaliacao` | — | `inform` `{bar, nota_geral, pontuacao, num_avaliacoes}` |
| Cliente → Bar | `inform` | `avaliacao` | `"criterio:nota"` (texto, ex. `preco:7`) | — |
| Cliente → Bar | `inform` | `sair` | — | — |

**Cardápio** (`CARDAPIO` em `agents/Bar.py`): `cerveja` 12 · `refrigerante` 6 · `drink` 25 · `porcao` 30

### Exemplo: cliente pedindo uma cerveja

```python
import json
from spade.message import Message

msg = Message(to="bar1@localhost")
msg.set_metadata("performative", "request")
msg.set_metadata("ontology", "pedido")
msg.body = json.dumps({"item": "cerveja"})
await self.send(msg)

resp = await self.receive(timeout=5)          # agree ou refuse
dados = json.loads(resp.body)                 # {"pedido_id": 1, "preco": 12, ...}
```

---

## Variação de preço

A cada 6 s (`PERIODO_ESTRATEGIA` em [agents/AgenteBar.py](agents/AgenteBar.py)) cada bar revisa o próprio preço com lógica nebulosa (Sugeno). O preço é um **score de 0 a 10, não reais**, e a escala é invertida: **maior = mais barato**.

1. **Entradas** (0 a 10):
   - `reputacao`: média móvel das notas dos clientes.
   - `fluxo`: `5 × visitas do bar / média de visitas dos bares`, com teto em 10 (5 = igual à média). Usa as visitas acumuladas, então reage devagar no fim da simulação.
2. **Fuzzificação** (`NIVEL` em [estrategia_bar.py](estrategia_bar.py)): cada entrada ganha um grau de 0 a 1 em `baixo` (vale 1 até 2.5, cai a 0 em 5), `medio` (triângulo com pico em 5) e `alto` (sobe a partir de 5, vale 1 de 7.5 em diante).
3. **Regras** (`REGRAS_PRECO`): a força de cada regra é o mínimo dos dois graus, e o delta é a média das saídas ponderada pelas forças: `delta = Σ(força × saída) / Σ(força)`.
4. **Aplicação** (`ajustar_preco` em [environment.py](environment.py)): `preco = preco + 0.3 × delta`, limitado a `preco_base ± LIMITE_PRECO` (3 pontos) e depois a 0–10.

Saída de cada regra (positivo = ficar mais barato):

| reputação \ fluxo | baixo | medio | alto |
|---|---|---|---|
| **baixo** | +1.0 | +0.4 | 0.0 |
| **medio** | +0.6 | 0.0 | −0.3 |
| **alto** | +0.3 | −0.3 | −0.8 |

O delta fica entre −0.8 e +1.0, então cada revisão move o score entre **−0.24 e +0.30**. Bar vazio faz promoção; bar cheio e bem avaliado encarece.

### Exemplo: reputação 6, fluxo 3.5

Reputação 6 → `medio` 0.6, `alto` 0.4. Fluxo 3.5 → `baixo` 0.6, `medio` 0.4.

| Regra (reputação / fluxo) | Força | Saída | Força × saída |
|---|---|---|---|
| medio / baixo | 0.6 | +0.6 | +0.36 |
| medio / medio | 0.4 | 0.0 | 0.00 |
| alto / baixo | 0.4 | +0.3 | +0.12 |
| alto / medio | 0.4 | −0.3 | −0.12 |
| **Soma** | **1.8** | | **+0.36** |

`delta = 0.36 / 1.8 = +0.2`, passo aplicado `0.3 × 0.2 = +0.06`: o bar fica um pouco mais barato porque está com pouco movimento.

### Faixa de cada bar

| Bar | Base | Faixa possível |
|---|---|---|
| bar1_premium | 3.0 | 0.0 a 6.0 |
| bar2_coposujo | 9.5 | 6.5 a 10.0 |
| bar3_modinha | 5.0 | 2.0 a 8.0 |
