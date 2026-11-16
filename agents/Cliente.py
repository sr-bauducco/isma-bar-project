import json
import random
from datetime import datetime, timedelta

from spade.behaviour import PeriodicBehaviour
from spade.message import Message
from spade_bdi.bdi import BDIAgent

import avaliacao
import decisao
import environment

PERIODO = 6  # segundos entre visitas
JANELA_LOTACAO = PERIODO / 2  # 'clientes recentes' = quem chegou nos últimos 3 s


class IrAoBarBehaviour(PeriodicBehaviour):
    """Cada rodada: percebe os bares, escolhe um, visita e avalia."""

    async def on_start(self):
        self.rodada = 0

    async def run(self):
        self.rodada += 1
        lot = {j: environment.lotacao(j, JANELA_LOTACAO) for j in environment.REGISTRO_BARES}
        escolhido, modo, valores = decisao.escolher_bar(
            self.agent.perfil, environment.REGISTRO_BARES, lot)
        bar = environment.REGISTRO_BARES[escolhido]

        # avaliação nebulosa da experiência real (com ruído)
        nota, rotulo, _ = avaliacao.avaliar(avaliacao.experiencia(bar), self.agent.perfil)
        nota = round(nota, 2)
        environment.registrar_visita(escolhido)

        print(f"[{self.agent.jid}] ({self.agent.perfil}) rodada {self.rodada} "
              f"[{modo.upper()}] lotacao={list(lot.values())}: "
              f"escolheu {escolhido} (valor {valores[escolhido]:.2f})")
        # 1) fato para o cérebro BDI do cliente (cliente.asl)
        self.agent.bdi.set_belief("visita", self.rodada, escolhido, nota, rotulo)

        # 2) avaliação ao bar por mensagem XMPP (FIPA-ACL 'inform'). Não usamos o
        #    '.send ... tell' do spade-bdi 0.3.1: ele recria o literal com argumentos quebrados.
        msg = Message(to=escolhido)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("ontology", "avaliacao-bar")
        msg.body = json.dumps({"rodada": self.rodada, "nota": nota,
                               "nivel": avaliacao.NIVEIS.index(rotulo), "rotulo": rotulo})
        await self.send(msg)


class AgenteCliente(BDIAgent):
    def __init__(self, jid, password, asl, perfil="ponderado"):
        super().__init__(jid, password, asl)
        if perfil not in avaliacao.PERFIS:
            raise ValueError(f"perfil desconhecido: {perfil} (use {list(avaliacao.PERFIS)})")
        self.perfil = perfil

    async def setup(self):
        print(f"[{self.jid}] Cliente '{self.perfil}' inicializado na rede XMPP.")
        inicio = datetime.now() + timedelta(seconds=random.uniform(1, PERIODO))
        self.add_behaviour(IrAoBarBehaviour(period=PERIODO, start_at=inicio))
