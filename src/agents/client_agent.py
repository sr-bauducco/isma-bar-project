from spade_bdi.bdi import BDIAgent
from spade.behaviour import OneShotBehaviour
import asyncio

class CalculoUtilidadeBehav(OneShotBehaviour):
    async def run(self):
        await asyncio.sleep(1)
        print("\n[PYTHON] Cerebro logico ativado: Calculando utilidade dos bares...")
        
        pesos = {'L': 0.3, 'P': 0.4, 'T': 0.2, 'D': 0.1}
        
        # Trocamos os nomes simples pelos endereços XMPP reais
        bares = {
            "bar1_unb@xmpp.jp": {'L': 9.0, 'P': 8.0, 'T': 9.0, 'D': 8.0}, # Vencedor forçado
            "bar2_off@xmpp.jp": {'L': 5.0, 'P': 5.0, 'T': 5.0, 'D': 5.0},
            "bar3_off@xmpp.jp": {'L': 6.0, 'P': 8.0, 'T': 8.0, 'D': 5.0},
        }
        
        melhor_bar = None
        maior_utilidade = -1
        
        for nome, notas in bares.items():
            utilidade = (pesos['L'] * notas['L']) + (pesos['P'] * notas['P']) + (pesos['T'] * notas['T']) + (pesos['D'] * notas['D'])
            print(f"[PYTHON] {nome} obteve Utilidade = {utilidade:.2f}")
            
            if utilidade > maior_utilidade:
                maior_utilidade = utilidade
                melhor_bar = nome
                
        print(f"[PYTHON] Decisao tomada! Vencedor: {melhor_bar}. Injetando no BDI...\n")
        
        # A crença 'vencedor' agora carregará o JID completo ("bar1_unb@xmpp.jp")
        self.agent.bdi.set_belief("vencedor", melhor_bar)

class ClientAgent(BDIAgent):
    async def setup(self):
        print(f"[Cliente] Agente {self.jid} inicializando...")
        self.add_behaviour(CalculoUtilidadeBehav())