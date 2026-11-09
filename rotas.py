import os

import aiohttp_jinja2
import jinja2
from aiohttp import web

import relogio

TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
HOST = "127.0.0.1"
PORTA = 10000


async def iniciar_painel(bares, host=HOST, porta=PORTA):
    """Sobe um único servidor web com o painel de todos os bares.

    `bares` é a lista de agentes Bar; o painel lê o estado deles a cada requisição,
    então bares adicionados à lista depois também aparecem.
    """
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATES_PATH))

    async def painel(request):
        return aiohttp_jinja2.render_template("painel.html", request, {"bares": bares, "relogio": relogio})

    async def raiz(request):
        raise web.HTTPFound("/painel")

    app.router.add_get("/", raiz)
    app.router.add_get("/painel", painel)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, host, porta).start()
    print(f"[Painel] http://{host}:{porta}/painel")
    return runner
