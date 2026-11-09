from spade_bdi.bdi import BDIAgent

class BarAgent(BDIAgent):
    async def setup(self):
        print(f"[Bar] Agente {self.jid} inicializando...")
        # No futuro, adicionaremos comportamentos para receber mensagens (FIPA-ACL) aqui