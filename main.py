import time
import spade
from src.agents.client_agent import ClientAgent

async def main():
    # ADICIONADO: verify_security=False para permitir conexão local com Prosody
    cliente = ClientAgent("cliente_teste@localhost", "senha123", "asl/client.asl", verify_security=False)
    
    print("=========================================")
    print("[TESTADOR] Validando sintaxe e iniciando...")
    
    try:
        await cliente.start()
        print("[TESTADOR] SUCESSO: Sintaxe ASL e Python validadas. Agente conectado!")
        
        time.sleep(3)
        
    except Exception as e:
        print(f"\n[TESTADOR] FALHA CRÍTICA ENCONTRADA:")
        print(f"Detalhes do Erro: {e}\n")
    finally:
        print("[TESTADOR] Encerrando simulação de teste...")
        await cliente.stop()

if __name__ == "__main__":
    spade.run(main())