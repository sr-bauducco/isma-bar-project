"""Diagnóstico da comunicação BDI (1 bar + 1 cliente, sem a simulação).
Rode: python teste_bdi.py
Mostra qual das 4 camadas funciona: T1 (mensagem chega), T2 ([source]),
T3 (contexto com crença inicial) e T4 (função fuzzy chamada do ASL).
"""
import asyncio
import logging
import os

from spade_bdi.bdi import BDIAgent

import environment
from agents.Bar import AgenteBar

logging.basicConfig(level=logging.WARNING)
logging.getLogger("agentspeak").setLevel(logging.DEBUG)

SENHA = os.getenv("XMPP_SENHA", "senha123")
BAR = environment.jid("bar1_premium")
CLI = environment.jid("cliente1")


async def main():
    bar = AgenteBar(BAR, SENHA, "asl/teste_bar.asl")
    await bar.start()
    cli = BDIAgent(CLI, SENHA, "asl/teste_cliente.asl")
    await cli.start()
    await asyncio.sleep(3)

    print("\n>>> cliente dispara os 4 testes\n")
    cli.bdi.set_belief("visita", BAR)
    await asyncio.sleep(6)

    print("\n>>> crenças do bar ao final:")
    bar.bdi.print_beliefs()
    print(">>> reputacao no ambiente:", environment.REGISTRO_BARES[BAR]["reputacao"])

    await cli.stop()
    await bar.stop()


if __name__ == "__main__":
    asyncio.run(main())
