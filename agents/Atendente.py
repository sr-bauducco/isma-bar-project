import spade
from spade.behaviour import OneShotBehaviour

class Atendente(spade.agent.Agent):

    def __init__(self, jid, password, bar_jid):
        super().__init__(jid, password)
        self.bar_jid = bar_jid
        self.capacidade = 4 # capacidade de atendimento de mesas
        self.mesas_atendidas = 0


    class Encerrar(OneShotBehaviour):
        async def run(self):
            await self.agent.stop()

    class DarNota(OneShotBehaviour):
        async def run(self):
            nota = 3
            msg = spade.message.Message(to=self.agent.bar_jid)
            msg.set_metadata("performative", "inform")
            msg.body = "atendimento:" + str(nota)

            await self.send(msg)
            print(f"[Atendente] enviei nota {nota} para o bar {self.agent.bar_jid}")

    class AtenderMesa(OneShotBehaviour):
        async def run(self):
            if self.agent.mesas_atendidas < self.agent.capacidade:
                self.agent.mesas_atendidas += 1
                print(f"[Atendente] atendendo mesa. Mesas atendidas: {self.agent.mesas_atendidas}")
                return True
            else:
                print(f"[Atendente] capacidade máxima atingida. Não posso atender mais mesas.")
    
    
    async def setup(self):
        print(f"Hello! Atendente agent {self.jid} is starting...")
        print(f"Atendente is serving bar agent {self.bar_jid}")
        print(f"Atendente capacity: {self.capacidade} mesas, mesas em atendimento: {self.mesas_atendidas}")
        self.add_behaviour(self.DarNota())
        self.add_behaviour(self.Encerrar())

