from spade_bdi.bdi import BDIAgent

class ClientAgent(BDIAgent):
    async def setup(self):
        print(f"[Cliente] Agente {self.jid} inicializando...")
        
        # O SPADE_BDI já carrega o .asl automaticamente agora.
        # Registramos apenas a nossa ação customizada em Python:
        self.bdi.set_custom_action("calcular_utilidade_bar", self.acao_calcular_utilidade)
        
        print(f"[Cliente] Lógica BDI carregada. Pronto para operar.")

    def acao_calcular_utilidade(self, *args):
        # Placeholder
        return True