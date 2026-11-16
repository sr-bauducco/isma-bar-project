import json
import random
from datetime import datetime, timedelta

from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.template import Template
from spade_bdi.bdi import BDIAgent

import environment
import estrategia_bar

PERIODO_ESTRATEGIA = 6  # segundos entre revisões de preço


class ReceberAvaliacaoBehaviour(CyclicBehaviour):
    """Recebe a avaliação do cliente (mensagem XMPP 'inform'), atualiza a reputação
    com a EMA de alfa nebuloso e entrega o fato ao cérebro BDI (bar.asl)."""

    async def run(self):
        msg = await self.receive(timeout=5)
        if msg is None:
            return
        meu_jid = str(self.agent.jid).split("/")[0]
        try:
            dados = json.loads(msg.body)
            nota = float(dados["nota"])
            nivel = int(dados["nivel"])
            rodada = int(dados["rodada"])
        except (ValueError, KeyError, TypeError) as erro:
            print(f"[{meu_jid}] avaliação inválida ({erro}): {msg.body!r}")
            return

        bar = environment.REGISTRO_BARES[meu_jid]
        nova = round(estrategia_bar.fuzzy_reputacao(nota, bar["reputacao"]), 3)
        bar["reputacao"] = nova
        cliente = str(msg.sender).split("/")[0]
        self.agent.bdi.set_belief("avaliacao", rodada, cliente, int(round(nota * 100)), nivel, nova)


class EstrategiaBehaviour(PeriodicBehaviour):
    """Revisa o preço periodicamente (reputação + fluxo), mesmo sem receber feedback.
    Assim um bar sem clientes também reage (ex.: faz promoção)."""

    async def run(self):
        meu_jid = str(self.agent.jid).split("/")[0]
        bar = environment.REGISTRO_BARES[meu_jid]
        delta = estrategia_bar.fuzzy_estrategia(bar["reputacao"], environment.fluxo(meu_jid))
        novo = environment.ajustar_preco(meu_jid, 0.3 * delta)
        print(f"[{meu_jid}] estrategia: reputacao={bar['reputacao']:.2f} "
              f"fluxo={environment.fluxo(meu_jid):.1f} -> score de preco {novo:.2f}")


class AgenteBar(BDIAgent):
    """Músculo do bar (Python) + cérebro BDI (bar.asl)."""

    def add_custom_actions(self, actions):
        meu_jid = str(self.jid).split("/")[0]

        @actions.add_function(".fuzzy_reputacao", (int, float))
        def _fuzzy_reputacao(nota_cent, reputacao_atual):
            nota = nota_cent / 100.0
            nova = round(estrategia_bar.fuzzy_reputacao(nota, float(reputacao_atual)), 3)
            environment.REGISTRO_BARES[meu_jid]["reputacao"] = nova
            return nova

    async def setup(self):
        print(f"[{self.jid}] Bar aberto e escutando avaliações na rede XMPP...")
        template = Template()
        template.set_metadata("performative", "inform")
        template.set_metadata("ontology", "avaliacao-bar")
        self.add_behaviour(ReceberAvaliacaoBehaviour(), template)
        inicio = datetime.now() + timedelta(seconds=random.uniform(2, PERIODO_ESTRATEGIA))
        self.add_behaviour(EstrategiaBehaviour(period=PERIODO_ESTRATEGIA, start_at=inicio))
