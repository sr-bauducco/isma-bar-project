import spade
from agents.Atendente import Atendente
from spade.behaviour import OneShotBehaviour

# VALORES PADROES PARA O BAR
NUM_ATENDENTES = 3

class Bar(spade.agent.Agent):

    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.atendentes = []


    class Encerrar(OneShotBehaviour):
        async def run(self):
            await self.agent.stop()


    async def setup(self):
        print(f"Hello! Bar agent {self.jid} is starting...")

        # Cada bar nasce com seus próprios atendentes: bar1 -> bar1_atendente1..3
        for i in range(1, NUM_ATENDENTES + 1):
            atendente_jid = f"{self.jid.user}_atendente{i}@{self.jid.domain}"
            atendente = Atendente(atendente_jid, "senha", str(self.jid))
            await atendente.start(auto_register=True)
            self.atendentes.append(atendente)

        self.add_behaviour(self.Encerrar())
