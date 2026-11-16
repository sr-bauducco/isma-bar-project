"""Teste do servidor XMPP local, com SPADE puro (sem BDI).
Antes: bash scripts/instalar_prosody.sh && bash scripts/criar_contas.sh
Rode:  python teste_conexao.py
"""
import asyncio
import os

from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message

DOMINIO = os.getenv("XMPP_DOMAIN", "localhost")
SENHA = os.getenv("XMPP_SENHA", "senha123")
BAR = f"bar1_premium@{DOMINIO}"
CLIENTE = f"cliente1@{DOMINIO}"


class Receptor(Agent):
    class Ouvir(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            print("RECEBIDO:", msg.body if msg else "nada (timeout)")

    async def setup(self):
        self.add_behaviour(self.Ouvir())


class Emissor(Agent):
    class Enviar(OneShotBehaviour):
        async def run(self):
            msg = Message(to=BAR)
            msg.body = "ola do cliente"
            await self.send(msg)
            print("ENVIADO")

    async def setup(self):
        self.add_behaviour(self.Enviar())


async def main():
    bar = Receptor(BAR, SENHA)
    await bar.start()
    cli = Emissor(CLIENTE, SENHA)
    await cli.start()
    await asyncio.sleep(12)
    await cli.stop()
    await bar.stop()


if __name__ == "__main__":
    asyncio.run(main())
