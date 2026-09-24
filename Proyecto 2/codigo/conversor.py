"""
conversor.py
------------
Funcionalidad 2 de la Fase 2: algoritmo de construcción de subconjuntos.

Transforma un AFND ya validado en un AFD equivalente, sin usar ninguna
biblioteca que implemente autómatas ni la conversión directamente: el
algoritmo se implementa a mano con las estructuras nativas de Python
(set, frozenset, dict, deque).

Idea del algoritmo
-------------------
Cada estado del AFD generado es un "macroestado": un subconjunto de
estados del AFND. Partiendo del macroestado {q0}, para cada símbolo del
alfabeto se calcula la unión de los destinos (en el AFND) de todos los
estados del macroestado actual. Ese nuevo subconjunto se registra como un
macroestado más y se repite el proceso hasta que no aparezcan
macroestados nuevos (por eso el AFD generado es siempre finito y completo:
cada macroestado tiene, por construcción, exactamente un destino por
símbolo, incluyendo el conjunto vacío ∅, que actúa como estado de trampa).

Un macroestado es final si contiene al menos un estado final del AFND.
"""

from collections import deque

from automata import AFD

ALFABETO_ETIQUETAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _siguiente_etiqueta(indice):
    """
    Genera etiquetas de macroestado al estilo de columnas de hoja de
    cálculo: A, B, C, ..., Z, AA, AB, ..., para que el AFD generado nunca
    se quede sin nombres, sin importar cuántos macroestados se descubran.
    """
    etiqueta = ""
    indice += 1
    while indice > 0:
        indice, resto = divmod(indice - 1, 26)
        etiqueta = ALFABETO_ETIQUETAS[resto] + etiqueta
    return etiqueta


def formatear_subconjunto(subconjunto):
    """Representa un macroestado (frozenset de estados del AFND) como
    texto legible: "{q0, q1}" o "∅" si está vacío."""
    if not subconjunto:
        return "∅"
    return "{" + ", ".join(sorted(subconjunto)) + "}"


def construir_afd_desde_afnd(afnd):
    """
    Aplica el algoritmo de construcción de subconjuntos sobre `afnd`
    (que debe estar ya validado por validador_afnd.validar_estructura_afnd).

    Devuelve la tupla (afd_generado, tabla_equivalencias):
      - afd_generado: instancia de AFD (la misma clase de la Fase 1), ya
        marcada como validado=True, porque por construcción es completo y
        determinista.
      - tabla_equivalencias: dict[etiqueta_macroestado] -> frozenset de
        estados del AFND que representa, en el orden en que se
        descubrieron (empezando por el estado inicial {q0}).
    """
    macroestado_inicial = frozenset({afnd.q0})

    etiquetas = {macroestado_inicial: _siguiente_etiqueta(0)}
    orden_descubrimiento = [macroestado_inicial]
    pendientes = deque([macroestado_inicial])
    delta_afd = {}

    while pendientes:
        actual = pendientes.popleft()
        for simbolo in sorted(afnd.sigma):
            destino = frozenset()
            for estado in actual:
                destino |= afnd.delta.get((estado, simbolo), frozenset())

            if destino not in etiquetas:
                etiquetas[destino] = _siguiente_etiqueta(len(etiquetas))
                orden_descubrimiento.append(destino)
                pendientes.append(destino)

            delta_afd[(etiquetas[actual], simbolo)] = etiquetas[destino]

    Q_afd = set(etiquetas.values())
    F_afd = {
        etiquetas[subconjunto]
        for subconjunto in orden_descubrimiento
        if subconjunto & afnd.F
    }

    afd_generado = AFD(
        nombre=f"{afnd.nombre}_AFD",
        Q=Q_afd,
        sigma=afnd.sigma,
        delta=delta_afd,
        q0=etiquetas[macroestado_inicial],
        F=F_afd,
    )
    # El AFD generado es completo y determinista por construcción: cada
    # macroestado tiene exactamente un destino por símbolo.
    afd_generado.validado = True

    tabla_equivalencias = {
        etiquetas[subconjunto]: subconjunto for subconjunto in orden_descubrimiento
    }
    return afd_generado, tabla_equivalencias
