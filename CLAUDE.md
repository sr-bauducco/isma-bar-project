# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A multi-agent system (SMA, *sistema multiagente*) simulating a bar, built on [SPADE](https://spade-mas.readthedocs.io/) 4.x (Python agents communicating over XMPP). Code, identifiers, log messages and commit messages are in Portuguese — keep that convention.

## Commands

```bash
source .venv/bin/activate          # virtualenv lives in .venv/
pip install -r requirements.txt
python main.py                     # runs the bar simulation (30 sim days, 1 day = 60 s real)
python main.py --dia 2 --dias 7    # faster: 1 sim day = 2 real s, run 7 sim days
python ola.py                      # standalone SPADE hello-world (Emissor -> Receptor), not part of the app
```

No XMPP server needs to be installed: both entry points call `spade.run(main(), embedded_xmpp_server=True)` and agents use `auto_register=True` against `localhost`. There is no test suite, linter, or build config yet.

`sqlalchemy[asyncio]` is listed in requirements but not used anywhere yet (presumably for future persistence).

## Simulated time

All durations are simulated time converted through `relogio.py` (`relogio.minutos/horas/dias/semanas(n)` → real seconds at the current scale; `real_para_minutos()` for the reverse). Never hard-code real seconds for anything with a simulated duration — tunable constants are named in sim units (`..._MINUTOS`, `..._HORAS`). `main.py` calls `relogio.configurar()` before creating agents and `relogio.iniciar()` only after all agents are up, then after `--dias` calls `relogio.encerrar()` (freezes the clock) and stops the agents; the web panel stays up with the final state until Ctrl+C unless `--sair-ao-fim`. Periodic behaviours get `relogio.periodo()` (floored at `PERIODO_MINIMO`), so at fast scales they tick *less often* than one sim unit: anything accumulating over time must use the actual elapsed sim time (see `Sujar`), and anything latency-sensitive should be event-driven (see `distribuir()` in `behaviours/pedidos.py`, called on new order and on order done). `tempos_espera` / `espera_media` are in sim minutes. Receive `timeout`s are plain real-time polling and are not scaled.

## Architecture

- `main.py` starts a single `Bar` agent (`bar@localhost`) and blocks with `spade.wait_until_finished` until it stops.
- `agents/Bar.py` — `Bar` agent. In `setup()` it **spawns its own `Atendente` agents** (count = module constant `NUM_ATENDENTES`), with JIDs derived from the bar's JID: `<bar_user>_atendente<i>@<domain>`. It passes its own JID to each attendant so they can message back.
  - State: `pontuacao` (current average per criterion: `limpeza`, `decoracao`, `atendimento`, `preco`, all starting at 10) and `avaliacoes` (raw list of scores per criterion). `nota_geral` is the mean of `pontuacao`. `registrar_nota` validates criterion and the 0–10 range, then recomputes that criterion's average.
  - `ReceberAvaliacao` (cyclic) receives messages with 5s timeout; on timeout it prints the current overall score.
- `agents/Atendente.py` — `Atendente` agent. `DarNota` sends a score to the bar; `Encerrar` stops the agent. Both are added as one-shot behaviours in `setup()` and run concurrently, so stop ordering vs. sending is not guaranteed.

- `agents/Faxineira.py` — `Faxineira` agent, spawned by the bar like attendants (`<bar_user>_faxineira<i>@<domain>`, `NUM_FAXINEIRAS`). Waits for cleaning requests, sleeps `TEMPO_LIMPEZA`, then replies how much it cleaned. It never mutates the bar directly.
- Cleaning loop: `behaviours.Sujar` lowers `nivel_limpeza`; `behaviours.VigiarLimpeza` (on the Bar) calls a free faxineira when it drops below `LIMITE_LIMPEZA`; the bar's `ReceberLimpeza` applies the result. "Free" is tracked bar-side in `Bar.chamados_pendentes` (JIDs called but not yet answered) to avoid double calls.

### Message protocol

Every message carries `performative` + `ontology` metadata, and each receiving behaviour is registered with a `Template` on both (`behaviours.template()`). A new message type needs its own behaviour + template, otherwise it is silently not delivered. Replies use `behaviours.responder()` (keeps the ontology via `make_reply`, JSON body). Bodies are JSON except the legacy `avaliacao` inform.

Order flow: the bar queues orders in `fila_pedidos`; `distribuir()` (run immediately on new order / order done, plus `DistribuirPedidos` as a periodic fallback) hands them to attendants with no entry in `pedidos_em_preparo` (bar-side "free" tracking, same idea as `chamados_pendentes`); the attendant's `PrepararPedido` delivers straight to the client and then tells the bar, which records the wait time in `tempos_espera`. Attendants must stay alive for this — don't re-add `Encerrar` to `Atendente.setup()`.

| From → To | performative | ontology | body |
|---|---|---|---|
| cliente → bar | `request` | `entrar` | empty → `agree` `{"clientes", "lotacao_maxima"}` or `refuse` `{"motivo": "fechado"\|"lotado"}` |
| cliente → bar | `inform` | `sair` | empty, no reply; also how a client gives up the door queue |
| bar → cliente | `inform` / later `agree` | `entrar` | bar full: `inform` `{"posicao"}` puts the client in `Bar.fila_entrada` (max `LIMITE_FILA_ENTRADA`, beyond that `refuse` `lotado`); when a seat frees, `chamar_fila()` in `behaviours/entrada.py` sends the `agree`. The client waits `PACIENCIA_FILA_MINUTOS` |
| cliente → bar | `request` | `pedido` | `{"item"}` (key of `Bar.cardapio`) → `agree` `{"pedido_id", "item", "preco", "posicao"}` or `refuse` `{"motivo": "fechado"\|"fora_do_bar"\|"item_inexistente"\|"formato_invalido"}` |
| bar → atendente | `request` | `preparar` | `{"pedido_id", "cliente", "item", "preco"}` |
| atendente → cliente | `inform` | `entrega` | `{"pedido_id", "item", "preco", "bar", "atendente"}` |
| atendente → bar | `inform` | `pedido_pronto` | `{"pedido_id"}` |
| atendente/cliente → bar | `inform` | `avaliacao` | `"<criterio>:<nota>"` (e.g. `atendimento:3`), nota parsed with `int()`, criterion ∈ `Bar.pontuacao` |
| anyone → bar | `query-ref` | `avaliacao` | empty; bar replies `inform`/`avaliacao` JSON `{"bar", "nota_geral", "pontuacao", "num_avaliacoes"}` (`behaviours.ResponderAvaliacao`) |
| bar → bar | `query-ref` | `precos` | empty; rival replies `inform`/`precos` JSON `{"bar", "cardapio"}` (`behaviours.gestao.ResponderPrecos`); the reply is read by `RevisarSemana`, registered with `template("inform", "precos")` |
| bar → faxineira | `request` | `limpar` | empty |
| faxineira → bar | `inform` | `limpeza_feita` | JSON `{"quantidade": float}` |

Parsing/validation errors are caught and logged by the bar, not raised.

New agents go in `agents/` (one class per file, PascalCase filename) and must be exported from `agents/__init__.py`. Reusable behaviours live in `behaviours/` (one per file, exported from `behaviours/__init__.py`, tunable defaults as module constants); agent-specific ones are still nested classes inside their agent.

`Bar.nivel_limpeza` is the bar's *real* cleanliness state (decayed by `behaviours.Sujar`), distinct from `pontuacao["limpeza"]`, which is the clients' average opinion.

`main.py` starts `NUM_BARES` bars (`bar1..N@localhost`); each `Bar` draws its attendant count randomly between `MIN_ATENDENTES` and `MAX_ATENDENTES` unless `num_atendentes` is passed.

Peak hours: `HORARIO_PICO_HORAS` in `agents/Cliente.py` (18h–23h). `horas_ate_proxima_visita()` draws the normal rest between visits but never lets a client skip a peak window, so every client attempts a bar once per peak (it may still be refused as `lotado`). Inside the peak the rest is short (`INTERVALO_PICO_MINUTOS`), so refused and served clients keep retrying until the peak ends. Checked offline by `python teste_pico.py`.

Weekly management: `behaviours.RevisarSemana` (on the Bar) checks every sim hour whether the week changed and then applies every action returned by the pure function `behaviours.gestao.decidir()` (a list; several actions can happen in the same week, at most one price move) (thresholds are module constants there): hire an attendant (`Bar.contratar_atendente()`, also used by `setup()`), add chairs (`lotacao_maxima`), or move prices (`Bar.ajustar_preco()` rescales the whole `cardapio` from `CARDAPIO` by `fator_preco`). If the week's revenue fell below `QUEDA_FATURAMENTO` × the previous week's, it first asks the rivals (`Bar.concorrentes`, filled by `main.py`) for their menus and the price move follows that comparison instead of reputation: pricier than them → lower, cheaper → raise. Each week is logged in `Bar.decisoes` (the week's numbers + `acao`); `main.py` calls `bar.revisao.fechar_semana_parcial()` at the end so the last incomplete week is included, and the panel's "Relatório semanal" button on each bar renders that list with week-over-week differences. The header's "Resumo geral" button compares all bars (totals, what changed since week 1, revenue per week). Checked offline by `python teste_gestao.py`. A client that leaves (`sair`) has its queued orders cancelled.

Client visit: after entering, the client orders 1–3 items (`PEDIDOS_POR_VISITA`), spending `TEMPO_CONSUMO_MINUTOS` on each, and leaves early if an order is refused or not delivered within `ESPERA_MAXIMA_HORAS`.

Web: `rotas.py` (`iniciar_painel(bares)`) runs a single standalone aiohttp server at `127.0.0.1:10000`: `/painel` serves the static `templates/painel.html` (vanilla JS, no build), which polls `/estado` (JSON snapshot of clock, bars and clients built by `rotas.estado()`) every 300 ms and animates it. A new field shown in the panel must be added to `_estado_bar()`. It deliberately does not use SPADE's per-agent `agent.web` (that would mean one server/port per bar).
