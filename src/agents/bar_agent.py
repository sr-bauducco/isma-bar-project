from spade_bdi.bdi import BDIAgent

class BarAgent(BDIAgent):
    async def setup(self):
        print(f"[Bar] Agente {self.jid} inicializando...")