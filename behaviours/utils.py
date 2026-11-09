import json

from spade.template import Template


def template(performative, ontology):
    """Filtro de mensagens por performative + ontology."""
    t = Template()
    t.set_metadata("performative", performative)
    t.set_metadata("ontology", ontology)
    return t


async def responder(behaviour, msg, performative, dados=None):
    """Responde `msg` com o mesmo ontology e body JSON."""
    resp = msg.make_reply()
    resp.set_metadata("performative", performative)
    resp.body = json.dumps(dados or {})
    await behaviour.send(resp)


def ler_json(msg):
    """Body da mensagem como dict (body vazio -> {})."""
    return json.loads(msg.body) if msg.body else {}
