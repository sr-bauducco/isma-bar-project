from agents import Bar
import spade

async def main():
    bar_agent = Bar("bar@localhost", "senha")
    await bar_agent.start(auto_register=True)
    await spade.wait_until_finished(bar_agent)


if __name__ == "__main__":
    spade.run(main(), embedded_xmpp_server=True)