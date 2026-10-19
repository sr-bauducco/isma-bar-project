import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template


class Receptor(Agent):
    class Ouvir(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                print(f"[Receptor] recebi: {msg.body}")
                await self.agent.stop()

    async def setup(self):
        t = Template()
        t.set_metadata("performative", "inform")
        self.add_behaviour(self.Ouvir(), t)


class Emissor(Agent):
    class Enviar(OneShotBehaviour):
        async def run(self):
            msg = Message(to="receptor@localhost")
            msg.set_metadata("performative", "inform")
            msg.body = "Olá, SMA!"
            await self.send(msg)
            print("[Emissor] mensagem enviada")
            await self.agent.stop()

    async def setup(self):
        self.add_behaviour(self.Enviar())


async def main():
    receptor = Receptor("receptor@localhost", "senha")
    await receptor.start(auto_register=True)
    emissor = Emissor("emissor@localhost", "senha")
    await emissor.start(auto_register=True)
    await spade.wait_until_finished(receptor)


if __name__ == "__main__":
    spade.run(main(), embedded_xmpp_server=True)
