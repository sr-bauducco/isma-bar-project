import asyncio
import json
import random
import time

from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade_bdi.bdi import BDIAgent

import avaliacao
import decisao
import relogio
from behaviours import ler_json

# VALORES PADROES DO CLIENTE (em tempo simulado)
INTERVALO_VISITA_HORAS = (2, 8)   # descanso entre uma visita e a próxima (sorteado)
ESPERA_MAXIMA_HORAS = 2           # desiste do pedido depois disso
MINUTOS_POR_PONTO = 6             # cada 6 min de espera tira 1 ponto do atendimento
REAIS_POR_PONTO = 3               # cada R$ 3 tira 1 ponto do preço (maior nota = mais barato)
TIMEOUT_RESPOSTA = 5              # s reais esperando resposta do bar (polling, não escala)


def _nota(valor):
    return max(0.0, min(10.0, valor))


class IrAoBarBehaviour(CyclicBehaviour):
    """Cada rodada: consulta os bares, escolhe um, entra, pede, avalia e sai."""

    async def on_start(self):
        self.rodada = 0

    async def pedir(self, para, performative, ontology, dados=None):
        msg = Message(to=para)
        msg.set_metadata("performative", performative)
        msg.set_metadata("ontology", ontology)
        msg.body = json.dumps(dados) if dados else ""
        await self.send(msg)

    async def esperar(self, ontology, de=None, timeout=TIMEOUT_RESPOSTA):
        """Próxima mensagem desse ontology (e remetente); descarta respostas atrasadas."""
        fim = time.monotonic() + timeout
        while (resta := fim - time.monotonic()) > 0:
            msg = await self.receive(timeout=resta)
            if msg and msg.get_metadata("ontology") == ontology and (
                    de is None or str(msg.sender.bare) == de):
                return msg
        return None

    async def consultar_bares(self):
        """query-ref/avaliacao a todos -> ({jid: atributos 0-10}, {jid: clientes dentro})."""
        for jid in self.agent.bares:
            await self.pedir(jid, "query-ref", "avaliacao")
        bares, lotacao = {}, {}
        while len(bares) < len(self.agent.bares):
            msg = await self.esperar("avaliacao")
            if msg is None:
                break
            dados = ler_json(msg)
            p = dados["pontuacao"]
            bares[str(msg.sender.bare)] = {
                "limpeza": p["limpeza"], "preco": p["preco"], "decoracao": p["decoracao"],
                # o bar não publica temperatura: bebida que demora chega quente
                "temperatura": p["atendimento"],
                "reputacao": dados["reputacao"],
            }
            lotacao[str(msg.sender.bare)] = dados.get("clientes", 0)
        return bares, lotacao

    async def run(self):
        if not relogio.rodando():
            await asyncio.sleep(0.2)
            return
        cliente = self.agent
        nome = cliente.jid.user
        self.rodada += 1

        bares, lotacao = await self.consultar_bares()
        if not bares:
            print(f"[{nome}] nenhum bar respondeu")
            return
        escolhido, modo, valores = decisao.escolher_bar(cliente.perfil, bares, lotacao)
        print(f"[{nome}] ({cliente.perfil}) rodada {self.rodada} [{modo.upper()}]: "
              f"escolheu {escolhido} (valor {valores[escolhido]:.2f})")

        await self.pedir(escolhido, "request", "entrar")
        resp = await self.esperar("entrar", escolhido)
        if resp is None or resp.get_metadata("performative") != "agree":
            motivo = ler_json(resp).get("motivo") if resp else "sem resposta"
            print(f"[{nome}] não entrei em {escolhido}: {motivo}")
        else:
            limpeza = ler_json(resp).get("limpeza", bares[escolhido]["limpeza"])
            await self.consumir(escolhido, limpeza, bares[escolhido]["decoracao"])
            await self.pedir(escolhido, "inform", "sair")

        await asyncio.sleep(relogio.horas(random.uniform(*INTERVALO_VISITA_HORAS)))

    async def consumir(self, bar, limpeza, decoracao):
        """Pede um item, espera a entrega e manda ao bar a satisfação nebulosa + o que sentiu."""
        cliente = self.agent
        nome = cliente.jid.user
        pedido_em = time.monotonic()
        await self.pedir(bar, "request", "pedido", {"item": random.choice(cliente.itens)})
        resp = await self.esperar("pedido", bar)
        if resp is None or resp.get_metadata("performative") != "agree":
            print(f"[{nome}] pedido recusado em {bar}")
            return
        pedido = ler_json(resp)

        entrega = await self.esperar(
            "entrega", timeout=max(TIMEOUT_RESPOSTA, relogio.horas(ESPERA_MAXIMA_HORAS)))
        espera = relogio.real_para_minutos(time.monotonic() - pedido_em)
        sentiu = {
            "limpeza": _nota(limpeza),
            "preco": _nota(10 - pedido["preco"] / REAIS_POR_PONTO),
            "temperatura": _nota(10 - espera / MINUTOS_POR_PONTO) if entrega else 0.0,
            "decoracao": _nota(decoracao),
        }
        nota, rotulo, _ = avaliacao.avaliar(sentiu, cliente.perfil)
        print(f"[{nome}] {pedido['item']} em {bar}: "
              f"{f'{espera:.0f} min' if entrega else 'desisti de esperar'}, achei {rotulo} ({nota:.1f})")
        # fato para o cérebro BDI do cliente (cliente.asl)
        cliente.bdi.set_belief("visita", self.rodada, bar, round(nota, 2), rotulo)

        # o bar não tem como medir decoração, então ela não é avaliada
        notas = {"satisfacao": nota, "limpeza": sentiu["limpeza"], "preco": sentiu["preco"],
                 "atendimento": sentiu["temperatura"]}
        for criterio, valor in notas.items():
            msg = Message(to=bar)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "avaliacao")
            msg.body = f"{criterio}:{valor:.2f}"
            await self.send(msg)


class AgenteCliente(BDIAgent):
    """Cliente: músculo em Python (protocolo do Bar) + cérebro BDI (cliente.asl)."""

    def __init__(self, jid, password, asl, bares, perfil="ponderado", itens=("cerveja", "refrigerante", "drink", "porcao")):
        super().__init__(jid, password, asl)
        if perfil not in avaliacao.PERFIS:
            raise ValueError(f"perfil desconhecido: {perfil} (use {list(avaliacao.PERFIS)})")
        self.perfil = perfil
        self.bares = list(bares)   # JIDs dos bares que o cliente conhece
        self.itens = list(itens)

    async def setup(self):
        print(f"[{self.jid}] Cliente '{self.perfil}' inicializado.")
        self.add_behaviour(IrAoBarBehaviour())
