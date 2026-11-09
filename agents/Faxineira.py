import asyncio
import json

import spade
from spade.behaviour import CyclicBehaviour
from spade.template import Template

import relogio

# VALORES PADROES DA FAXINEIRA (em tempo simulado)
TEMPO_LIMPEZA_MINUTOS = 60  # ela leva 1 hora simulada para limpar
QUANTIDADE_LIMPEZA = 3.0    # quanto o nível de limpeza sobe por limpeza


class Faxineira(spade.agent.Agent):
    """Fica esperando chamados do bar; quando chamada, limpa e avisa o bar quanto limpou.

    Ela não altera o estado do bar diretamente: só informa por mensagem.
    """

    def __init__(self, jid, password, bar_jid):
        super().__init__(jid, password)
        self.bar_jid = bar_jid
        self.ocupada = False

    class AtenderChamado(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return

            nome = self.agent.jid.user
            self.agent.ocupada = True
            print(f"[{nome}] chamada para limpar, limpando por {TEMPO_LIMPEZA_MINUTOS} min...")
            await asyncio.sleep(relogio.minutos(TEMPO_LIMPEZA_MINUTOS))

            resp = msg.make_reply()
            resp.set_metadata("performative", "inform")
            resp.set_metadata("ontology", "limpeza_feita")
            resp.body = json.dumps({"quantidade": QUANTIDADE_LIMPEZA})
            await self.send(resp)

            self.agent.ocupada = False
            print(f"[{nome}] terminei de limpar (+{QUANTIDADE_LIMPEZA})")

    async def setup(self):
        print(f"Hello! Faxineira agent {self.jid} is starting (bar {self.bar_jid})...")
        t = Template()
        t.set_metadata("performative", "request")
        t.set_metadata("ontology", "limpar")
        self.add_behaviour(self.AtenderChamado(), t)
