import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour

class AgenteDeTeste(Agent):
    # Definimos um comportamento simples que roda apenas uma vez
    class ComportamentoInicial(OneShotBehaviour):
        async def run(self):
            print(f"\n[SUCESSO] Olá! Eu sou o agente: {self.agent.jid}")
            print("[SUCESSO] Se você está lendo isso, o SPADE está funcionando perfeitamente no seu ambiente!\n")

    # O método setup é executado assim que o agente é iniciado
    async def setup(self):
        print("Iniciando o agente e configurando o servidor local...")
        b = self.ComportamentoInicial()
        self.add_behaviour(b)

async def main():
    # Cria o agente usando @localhost para aproveitar o servidor embutido do SPADE
    agente = AgenteDeTeste("agente_teste@localhost", "senha_super_secreta")
    
    # Inicia o agente
    await agente.start()
    
    # Aguarda até que todos os comportamentos terminem de executar
    await spade.wait_until_finished(agente)
    print("Agente finalizado e desconectado.")

if __name__ == "__main__":
    # Inicia o loop assíncrono do SPADE
    spade.run(main())