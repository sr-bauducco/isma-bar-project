import asyncio
import json
import time

from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

import relogio
from behaviours.utils import ler_json, responder

# VALORES PADROES DOS PEDIDOS (em tempo simulado)
PERIODO_DISTRIBUIR_MINUTOS = 1   # a cada 1 min simulado o bar passa pedidos da fila aos atendentes
TEMPO_PREPARO_MINUTOS = 10       # um atendente leva 10 min simulados para preparar um pedido


class ReceberPedido(CyclicBehaviour):
    """Behaviour do Bar: cliente faz um pedido; o bar coloca na fila.

    Recebe:   request / pedido  {"item": "cerveja"}
    Responde: agree  / pedido  {"pedido_id": 1, "item": "cerveja", "preco": 12, "posicao": 1}
              refuse / pedido  {"motivo": "fechado" | "fora_do_bar" | "item_inexistente", ...}
    A entrega chega depois, enviada pelo atendente (inform / entrega).
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return

        bar = self.agent
        cliente = str(msg.sender.bare)

        try:
            item = ler_json(msg).get("item")
        except json.JSONDecodeError:
            await responder(self, msg, "refuse", {"motivo": "formato_invalido", "esperado": {"item": "nome"}})
            return

        if not bar.is_open:
            await responder(self, msg, "refuse", {"motivo": "fechado"})
            return
        if cliente not in bar.clientes:
            await responder(self, msg, "refuse", {"motivo": "fora_do_bar"})
            return
        if item not in bar.cardapio:
            await responder(self, msg, "refuse", {"motivo": "item_inexistente", "cardapio": bar.cardapio})
            return

        pedido = {
            "pedido_id": next(bar.proximo_pedido_id),
            "cliente": cliente,
            "item": item,
            "preco": bar.cardapio[item],
            "feito_em": time.monotonic(),
        }
        bar.fila_pedidos.append(pedido)

        await responder(self, msg, "agree", {
            "pedido_id": pedido["pedido_id"],
            "item": item,
            "preco": pedido["preco"],
            "posicao": len(bar.fila_pedidos),
        })
        print(f"[{bar.jid.user}] pedido #{pedido['pedido_id']} de {msg.sender.user}: {item} "
              f"(fila: {len(bar.fila_pedidos)})")
        await distribuir(self)  # se tem atendente livre, já vai para ele


async def distribuir(behaviour):
    """Passa pedidos da fila para atendentes livres (usada por qualquer behaviour do Bar).

    Envia: request / preparar  {"pedido_id", "cliente", "item", "preco"}  -> atendente
    "Livre" é decidido pelo bar: atendente sem pedido em bar.pedidos_em_preparo.
    """
    bar = behaviour.agent
    ocupados = {p["atendente"] for p in bar.pedidos_em_preparo.values()}

    for atendente in bar.atendentes:
        if not bar.fila_pedidos:
            return
        jid = str(atendente.jid)
        if jid in ocupados:
            continue

        pedido = bar.fila_pedidos.popleft()
        pedido["atendente"] = jid
        bar.pedidos_em_preparo[pedido["pedido_id"]] = pedido

        msg = Message(to=jid)
        msg.set_metadata("performative", "request")
        msg.set_metadata("ontology", "preparar")
        msg.body = json.dumps({k: pedido[k] for k in ("pedido_id", "cliente", "item", "preco")})
        await behaviour.send(msg)
        print(f"[{bar.jid.user}] pedido #{pedido['pedido_id']} -> {atendente.jid.user}")


class DistribuirPedidos(PeriodicBehaviour):
    """Behaviour do Bar: garantia periódica de que nenhum pedido fica parado na fila.

    A distribuição normal acontece na hora (ReceberPedido e ReceberPedidoPronto chamam
    distribuir()); este behaviour só cobre algum caso que escape disso.
    """

    def __init__(self, period=None, **kwargs):
        if period is None:
            period = relogio.periodo(relogio.minutos(PERIODO_DISTRIBUIR_MINUTOS))
        super().__init__(period=period, **kwargs)

    async def run(self):
        await distribuir(self)


class PrepararPedido(CyclicBehaviour):
    """Behaviour do Atendente: prepara o pedido, entrega ao cliente e avisa o bar.

    Recebe: request / preparar  (do bar)
    Envia:  inform / entrega       {"pedido_id", "item", "preco", "bar", "atendente"}  -> cliente
            inform / pedido_pronto {"pedido_id"}                                      -> bar
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return

        atendente = self.agent
        pedido = ler_json(msg)
        atendente.is_serving = True
        print(f"[{atendente.jid.user}] preparando pedido #{pedido['pedido_id']}: {pedido['item']}...")
        await asyncio.sleep(relogio.minutos(TEMPO_PREPARO_MINUTOS))

        entrega = Message(to=pedido["cliente"])
        entrega.set_metadata("performative", "inform")
        entrega.set_metadata("ontology", "entrega")
        entrega.body = json.dumps({
            "pedido_id": pedido["pedido_id"],
            "item": pedido["item"],
            "preco": pedido["preco"],
            "bar": atendente.bar_jid,
            "atendente": str(atendente.jid),
        })
        await self.send(entrega)

        pronto = msg.make_reply()
        pronto.set_metadata("performative", "inform")
        pronto.set_metadata("ontology", "pedido_pronto")
        pronto.body = json.dumps({"pedido_id": pedido["pedido_id"]})
        await self.send(pronto)

        atendente.is_serving = False
        print(f"[{atendente.jid.user}] entreguei pedido #{pedido['pedido_id']} a {pedido['cliente']}")


class ReceberPedidoPronto(CyclicBehaviour):
    """Behaviour do Bar: atendente terminou; libera o atendente e registra o tempo de espera.

    Recebe: inform / pedido_pronto  {"pedido_id"}
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return

        bar = self.agent
        pedido_id = ler_json(msg).get("pedido_id")
        pedido = bar.pedidos_em_preparo.pop(pedido_id, None)
        if pedido is None:
            print(f"[{bar.jid.user}] pedido_pronto desconhecido: {pedido_id}")
            return

        # medido em segundos reais, guardado em minutos simulados (vale para qualquer escala)
        espera = relogio.real_para_minutos(time.monotonic() - pedido["feito_em"])
        bar.tempos_espera.append(espera)
        bar.faturamento = round(bar.faturamento + pedido["preco"], 2)
        print(f"[{bar.jid.user}] pedido #{pedido_id} entregue em {espera:.0f} min "
              f"(média: {bar.espera_media:.0f} min)")
        await distribuir(self)  # atendente ficou livre: pega o próximo da fila
