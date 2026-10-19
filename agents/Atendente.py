import spade
from spade.behaviour import OneShotBehaviour

class Atendente(spade.agent.Agent):

    def __init__(self, jid, password, bar_jid):
        super().__init__(jid, password)
        self.bar_jid = bar_jid
        self.is_serving = False


    class Encerrar(OneShotBehaviour):
        async def run(self):
            await self.agent.stop()
    
    
    async def setup(self):
        print(f"Hello! Atendente agent {self.jid} is starting...")
        print(f"Atendente is serving bar agent {self.bar_jid}")
        print(f"Atendente {'is' if self.is_serving else 'is not'} currently serving.")
        self.add_behaviour(self.Encerrar())

