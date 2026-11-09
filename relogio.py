"""Relógio da simulação: converte tempo simulado (minutos, horas, dias...) em segundos reais.

Tudo que tem duração na simulação deve passar por aqui, nunca usar segundos "soltos".
Assim, mudar a escala (python main.py --dia 2) acelera a simulação inteira por igual.

    relogio.horas(1)     -> quantos segundos reais dura 1 hora simulada
    relogio.dia_atual()  -> em que dia da simulação estamos (1, 2, 3...)
"""
import time

# VALORES PADROES DO RELOGIO
SEGUNDOS_REAIS_POR_DIA = 60   # 1 dia simulado = 60 s reais -> 1 semana = 7 min, 1 mês = 30 min
DIAS_SIMULACAO = 30           # duração da simulação
PERIODO_MINIMO = 0.1          # nenhum behaviour periódico roda mais rápido que isso (s reais)

_segundos_por_dia = SEGUNDOS_REAIS_POR_DIA
_inicio = None                # time.monotonic() do momento em que o relógio começou
_fim = None                   # time.monotonic() do momento em que a simulação acabou (congela o relógio)


def configurar(segundos_por_dia):
    """Define a escala. Chamar ANTES de criar os agentes."""
    global _segundos_por_dia
    if segundos_por_dia <= 0:
        raise ValueError("segundos_por_dia deve ser > 0")
    _segundos_por_dia = segundos_por_dia


def iniciar():
    """Começa a contar o tempo (chamar depois que todos os agentes subirem)."""
    global _inicio
    _inicio = time.monotonic()


def encerrar():
    """Congela o relógio no instante atual (fim da simulação)."""
    global _fim
    _fim = time.monotonic()


def rodando():
    return _inicio is not None and _fim is None


def encerrado():
    return _fim is not None


# ---- tempo simulado -> segundos reais ----

def dias(n):
    return n * _segundos_por_dia


def horas(n):
    return dias(n) / 24


def minutos(n):
    return horas(n) / 60


def semanas(n):
    return dias(7 * n)


def periodo(segundos_reais):
    """Período para PeriodicBehaviour, com piso para não travar o loop em escalas muito rápidas."""
    return max(PERIODO_MINIMO, segundos_reais)


# ---- segundos reais -> tempo simulado ----

def real_para_minutos(segundos_reais):
    return segundos_reais / minutos(1)


# ---- onde estamos na simulação ----

def dias_passados():
    """Dias simulados desde iniciar() (float). 0 se o relógio ainda não começou."""
    if _inicio is None:
        return 0.0
    agora = _fim if _fim is not None else time.monotonic()
    return (agora - _inicio) / _segundos_por_dia


def dia_atual():
    return int(dias_passados()) + 1


def semana_atual():
    return (dia_atual() - 1) // 7 + 1


def hora_do_dia():
    return int((dias_passados() % 1) * 24)


def escala():
    return _segundos_por_dia
