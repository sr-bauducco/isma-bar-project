import asyncio
import os

import environment
from agents.Bar import AgenteBar
from agents.Cliente import AgenteCliente

SENHA = os.getenv("XMPP_SENHA", "senha123")
DURACAO = int(os.getenv("DURACAO", "120"))  # segundos de simulação
# As contas são criadas por scripts/criar_contas.sh; use AUTO_REGISTER=1 só se preferir registro in-band.
AUTO_REGISTER = os.getenv("AUTO_REGISTER", "0") == "1"

PERFIS_CLIENTES = ["universitario"] * 3 + ["ponderado"] * 3


async def main():
    print("Iniciando Simulação Multiagente Híbrida - ISMA Bar Project")
    agentes = []

    for jid_bar in environment.REGISTRO_BARES:
        bar = AgenteBar(jid_bar, SENHA, "asl/bar.asl")
        await bar.start(auto_register=AUTO_REGISTER)
        agentes.append(bar)

    for i, perfil in enumerate(PERFIS_CLIENTES, start=1):
        cli = AgenteCliente(environment.jid(f"cliente{i}"), SENHA, "asl/cliente.asl", perfil)
        await cli.start(auto_register=AUTO_REGISTER)
        agentes.append(cli)

    print(f"Agentes online. Simulação por {DURACAO}s (Ctrl+C para encerrar antes).")
    try:
        await asyncio.sleep(DURACAO)
    finally:
        for a in agentes:
            await a.stop()
        print(environment.resumo())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrando simulação...")
