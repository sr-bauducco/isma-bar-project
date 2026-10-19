import spade
from spade.behaviour import OneShotBehaviour


class Bar(spade.agent.Agent):
    class Encerrar(OneShotBehaviour):
        async def run(self):
            await self.agent.stop()

    async def setup(self):
        print(f"Hello! Bar agent {self.jid} is starting...")
        self.add_behaviour(self.Encerrar())
