"""
simulador.py
------------
Funcionalidad 3: Motor de evaluación y simulación paso a paso.

Procesa una cadena de entrada símbolo a símbolo, aplicando la función de
transición delta del AFD, generando la traza completa de ejecución y
determinando el veredicto final (Aceptada / Rechazada). También ofrece la
evaluación en lote de varias cadenas a la vez.

Fase 2: se agrega la simulación directa de un AFND (evaluar_cadena_afnd).
No sustituye al AFD generado (las opciones 10 y 11 siguen evaluando sobre
el AFD), sino que se usa para COMPARAR ambos veredictos y comprobar, con
cada cadena evaluada, que el AFD generado reconoce el mismo lenguaje que
el AFND original.
"""

from dataclasses import dataclass, field

from colores import exito, error, info
from conversor import formatear_subconjunto


@dataclass
class Paso:
    """Un paso de la traza de ejecución: el resultado de aplicar delta
    una sola vez."""
    estado_origen: str
    simbolo: str
    estado_destino: str


@dataclass
class ResultadoEvaluacion:
    """
    Resultado de evaluar una cadena contra un AFD.

    Se usa una dataclass (en vez de un diccionario suelto) para que los
    campos sean explícitos y el editor los autocomplete, en vez de tener
    que recordar de memoria claves como "traza" o "resultado".

    Atributos
    ---------
    cadena : str
        La cadena que se evaluó.
    traza : list[Paso]
        Secuencia de transiciones aplicadas, en orden.
    veredicto : str
        "Aceptada" o "Rechazada".
    motivo : str | None
        Explica por qué se rechazó antes de terminar de procesar la
        cadena (símbolo fuera de Sigma o transición faltante). None si
        la cadena se procesó por completo.
    """
    cadena: str
    traza: list = field(default_factory=list)
    veredicto: str = "Rechazada"
    motivo: str = None


def evaluar_cadena(afd, cadena):
    """
    Simula el AFD sobre `cadena` (puede ser la cadena vacía "", es decir,
    lambda). Aplica exactamente el algoritmo descrito en el análisis:

        estado_actual <- q0
        para cada símbolo de la cadena:
            si el símbolo no pertenece a Sigma -> Rechazada
            siguiente <- delta(estado_actual, símbolo)
            si no existe esa transición -> Rechazada (AFD incompleto)
            estado_actual <- siguiente
        al terminar: Aceptada si estado_actual pertenece a F, si no Rechazada

    Devuelve un ResultadoEvaluacion.
    """
    estado_actual = afd.q0
    traza = []

    for simbolo in cadena:
        if simbolo not in afd.sigma:
            return ResultadoEvaluacion(
                cadena=cadena,
                traza=traza,
                veredicto="Rechazada",
                motivo=f"El símbolo '{simbolo}' no pertenece al alfabeto Sigma = {sorted(afd.sigma)}.",
            )
        siguiente = afd.transicion(estado_actual, simbolo)
        if siguiente is None:
            return ResultadoEvaluacion(
                cadena=cadena,
                traza=traza,
                veredicto="Rechazada",
                motivo=f"No existe transición definida para ({estado_actual}, {simbolo}).",
            )
        traza.append(Paso(estado_actual, simbolo, siguiente))
        estado_actual = siguiente

    # La cadena vacía (lambda) es válida: no se procesa ningún símbolo y el
    # veredicto depende únicamente de si q0 pertenece a F.
    veredicto = "Aceptada" if estado_actual in afd.F else "Rechazada"
    return ResultadoEvaluacion(cadena=cadena, traza=traza, veredicto=veredicto, motivo=None)


def evaluar_lote(afd, cadenas):
    """
    Evalúa una lista de cadenas (una por línea de un archivo, típicamente).
    Devuelve (resultados, resumen), donde:
        resultados -> lista de ResultadoEvaluacion, uno por cadena
        resumen    -> {"total": int, "aceptadas": int, "rechazadas": int}
    """
    resultados = []
    total_aceptadas = 0
    total_rechazadas = 0

    for cadena in cadenas:
        resultado = evaluar_cadena(afd, cadena)
        resultados.append(resultado)
        if resultado.veredicto == "Aceptada":
            total_aceptadas += 1
        else:
            total_rechazadas += 1

    resumen = {
        "total": len(cadenas),
        "aceptadas": total_aceptadas,
        "rechazadas": total_rechazadas,
    }
    return resultados, resumen


def imprimir_traza(resultado_evaluacion):
    """
    Imprime en consola la traza paso a paso (estado actual, símbolo
    procesado, siguiente estado) y el veredicto final, resaltando con
    color verde las cadenas aceptadas y rojo las rechazadas.
    """
    cadena = resultado_evaluacion.cadena
    etiqueta_cadena = cadena if cadena != "" else "λ (cadena vacía)"
    print(info(f"\nEvaluando cadena: {etiqueta_cadena}"))

    if not resultado_evaluacion.traza:
        print(info("  (no se procesó ningún símbolo)"))
    for paso in resultado_evaluacion.traza:
        print(f"  δ({paso.estado_origen}, {paso.simbolo}) = {paso.estado_destino}")

    if resultado_evaluacion.motivo:
        print(error(f"  Motivo: {resultado_evaluacion.motivo}"))

    veredicto = resultado_evaluacion.veredicto
    if veredicto == "Aceptada":
        print(exito(f"Veredicto: {veredicto}"))
    else:
        print(error(f"Veredicto: {veredicto}"))


# ---------------------------------------------------------------------------
# Fase 2: simulación directa del AFND (para comparar con el AFD generado)
# ---------------------------------------------------------------------------

@dataclass
class PasoAFND:
    """Un paso de la traza de un AFND: desde un CONJUNTO de estados
    activos, con un símbolo, se llega a otro conjunto de estados."""
    conjunto_origen: frozenset
    simbolo: str
    conjunto_destino: frozenset


@dataclass
class ResultadoEvaluacionAFND:
    """Igual que ResultadoEvaluacion, pero la traza es de PasoAFND."""
    cadena: str
    traza: list = field(default_factory=list)
    veredicto: str = "Rechazada"
    motivo: str = None


def evaluar_cadena_afnd(afnd, cadena):
    """
    Simula el AFND sobre `cadena` siguiendo TODOS los caminos posibles a la
    vez, es decir, manteniendo el conjunto de estados activos:

        activos <- {q0}
        para cada símbolo a de la cadena:
            si a no pertenece a Sigma -> Rechazada
            activos <- unión de delta(q, a) para cada q en activos
        al terminar: Aceptada si activos contiene algún estado de F

    Si en algún momento `activos` queda vacío (∅), ningún camino sigue vivo
    y la cadena ya no puede aceptarse; aun así se procesan los símbolos
    restantes para que la traza sea comparable paso a paso con la del AFD
    generado (donde ∅ es el estado de trampa).
    """
    activos = frozenset({afnd.q0})
    traza = []

    for simbolo in cadena:
        if simbolo not in afnd.sigma:
            return ResultadoEvaluacionAFND(
                cadena=cadena,
                traza=traza,
                veredicto="Rechazada",
                motivo=f"El símbolo '{simbolo}' no pertenece al alfabeto Sigma = {sorted(afnd.sigma)}.",
            )
        siguientes = frozenset()
        for estado in activos:
            siguientes |= afnd.transicion(estado, simbolo)
        traza.append(PasoAFND(activos, simbolo, siguientes))
        activos = siguientes

    veredicto = "Aceptada" if activos & afnd.F else "Rechazada"
    return ResultadoEvaluacionAFND(cadena=cadena, traza=traza, veredicto=veredicto, motivo=None)


def imprimir_traza_afnd(resultado_afnd):
    """Imprime la traza del AFND como secuencia de conjuntos de estados."""
    print(info("  Simulación directa sobre el AFND original (conjuntos de estados activos):"))
    if not resultado_afnd.traza:
        print(info("    (no se procesó ningún símbolo)"))
    for paso in resultado_afnd.traza:
        print(
            f"    {formatear_subconjunto(paso.conjunto_origen)} "
            f"--{paso.simbolo}--> {formatear_subconjunto(paso.conjunto_destino)}"
        )
    if resultado_afnd.motivo:
        print(error(f"    Motivo: {resultado_afnd.motivo}"))
    if resultado_afnd.veredicto == "Aceptada":
        print(exito(f"  Veredicto del AFND: {resultado_afnd.veredicto}"))
    else:
        print(error(f"  Veredicto del AFND: {resultado_afnd.veredicto}"))


def imprimir_comparacion(resultado_afd, resultado_afnd):
    """Muestra si el AFND original y el AFD generado coinciden en el
    veredicto de una cadena. Devuelve True si coinciden."""
    coinciden = resultado_afd.veredicto == resultado_afnd.veredicto
    texto = (
        f"  Comparación -> AFND: {resultado_afnd.veredicto} | "
        f"AFD generado: {resultado_afd.veredicto}"
    )
    if coinciden:
        print(exito(texto + "  (COINCIDEN)"))
    else:
        print(error(texto + "  (NO COINCIDEN)"))
    return coinciden
