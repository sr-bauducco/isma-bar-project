import asyncio
import spade
from src.agents.client_agent import ClientAgent
from src.agents.bar_agent import BarAgent # Novo import

async def main():
    # Coloque suas senhas reais do xmpp.jp aqui
    cliente = ClientAgent("cliente_teste_unb@xmpp.jp", "Senh@123", "asl/client.asl")
    bar1 = BarAgent("bar1_unb@xmpp.jp", "Senh@123", "asl/bar.asl")
    
    print("=========================================")
    print("[TESTADOR] Iniciando ecossistema de agentes...")
    
    try:
        # Iniciamos o Bar primeiro, para garantir que ele esteja de portas abertas
        await bar1.start()
        # Depois iniciamos o Cliente, que vai escolher onde ir
        await cliente.start()
        
        print("[TESTADOR] SUCESSO: Ambos os agentes conectados!\n")
        
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"\n[TESTADOR] FALHA CRÍTICA ENCONTRADA: {e}\n")
    finally:
        print("\n[TESTADOR] Encerrando simulação...")
        await cliente.stop()
        await bar1.stop()

if __name__ == "__main__":
    spade.run(main())