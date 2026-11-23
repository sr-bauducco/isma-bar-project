import os
from collections import Counter

from aiohttp import web

import relogio
from behaviours.entrada import LIMITE_FILA_ENTRADA

PAINEL_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "painel.html")
HOST = "127.0.0.1"
PORTA = 10000


def _estado_bar(bar):
    preparando = {p["atendente"]: p["item"] for p in bar.pedidos_em_preparo.values()}
    return {
        "nome": bar.jid.user,
        "aberto": bar.is_open,
        "reputacao": bar.reputacao,
        "limpeza": bar.nivel_limpeza,
        "pontuacao": bar.pontuacao,
        "clientes": [c.split("@")[0] for c in bar.clientes],
        "lotacao_maxima": bar.lotacao_maxima,
        "fila_entrada": [c.split("@")[0] for c in bar.fila_entrada],
        "fila_entrada_maxima": LIMITE_FILA_ENTRADA,
        "atendentes": [{"nome": a.jid.user, "item": preparando.get(str(a.jid))} for a in bar.atendentes],
        "faxineiras": [{"nome": f.jid.user, "limpando": f.ocupada} for f in bar.faxineiras],
        "fila": [p["item"] for p in bar.fila_pedidos],
        "entregues": len(bar.tempos_espera),
        "espera_media": bar.espera_media,
        "faturamento": bar.faturamento,
        "recusas_lotado": bar.recusas_lotado,
        "chegadas": bar.chegadas,
        "ocupacao_por_hora": {h: [dentro / n, porta / n] for h, (n, dentro, porta) in bar.ocupacao_por_hora.items()},
        "cardapio": bar.cardapio,
        "fator_preco": bar.fator_preco,
        "tendencia_preco": bar.tendencia_preco,
        "decisoes": bar.decisoes,
    }


def _satisfacao(clientes):
    """Por perfil: quantas avaliações, a nota média e quantas de cada rótulo."""
    perfis = {}
    for c in clientes:
        p = perfis.setdefault(c.perfil, {"soma": 0.0, "rotulos": Counter()})
        p["soma"] += c.soma_satisfacao
        p["rotulos"].update(c.rotulos)
    return {perfil: {"n": (n := sum(p["rotulos"].values())), "media": p["soma"] / n if n else 0.0,
                     "rotulos": p["rotulos"]} for perfil, p in perfis.items()}


def estado(bares, clientes):
    """Retrato da simulação em JSON; o painel busca isso várias vezes por segundo."""
    fase = "encerrado" if relogio.encerrado() else "rodando" if relogio.rodando() else "aguardando"
    return {
        "relogio": {
            "fase": fase,
            "dia": relogio.dia_atual(),
            "semana": relogio.semana_atual(),
            "hora": (relogio.dias_passados() % 1) * 24,
            "escala": relogio.escala(),
        },
        "clientes": [{"nome": c.jid.user, "perfil": c.perfil} for c in clientes],
        "satisfacao": _satisfacao(clientes),
        "bares": [_estado_bar(b) for b in bares],
    }


async def iniciar_painel(bares, clientes=(), host=HOST, porta=PORTA):
    """Sobe um único servidor web com o painel de todos os bares.

    `bares` e `clientes` são as listas de agentes; o estado é lido a cada requisição,
    então agentes adicionados às listas depois também aparecem.
    """
    app = web.Application()

    async def painel(request):
        return web.FileResponse(PAINEL_HTML)

    async def dados(request):
        return web.json_response(estado(bares, clientes))

    async def raiz(request):
        raise web.HTTPFound("/painel")

    app.router.add_get("/", raiz)
    app.router.add_get("/painel", painel)
    app.router.add_get("/estado", dados)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, host, porta).start()
    print(f"[Painel] http://{host}:{porta}/painel")
    return runner
