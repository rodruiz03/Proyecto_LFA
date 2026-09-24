"""
validador.py
------------
Funcionalidad 2: Motor de Validación de la Tupla, y análisis estructural
del AFD (estados alcanzables, inaccesibles, etc.).

Este módulo no lee archivos ni pide datos por consola (eso es
responsabilidad de cargador.py) ni simula cadenas (simulador.py): solo
verifica que la quíntupla ya construida sea, en efecto, un AFD válido.
"""

from dataclasses import dataclass


@dataclass
class AnalisisEstructural:
    """
    Resultado del análisis estructural de un AFD ya validado (ver
    analizar_estructura). Se usa una dataclass, en vez de un diccionario,
    para que los cuatro resultados viajen juntos con nombres explícitos
    que el editor autocompleta, sin tener que recordar claves de memoria.
    """
    alcanzables: set
    inaccesibles: set
    finales_alcanzables: set
    lenguaje_vacio: bool


def validar_estructura(afd):
    """
    Aplica las tres reglas de validación exigidas por el enunciado:

      1. Validación de estados: q0 pertenece a Q, y F es subconjunto de Q.
      2. Consistencia de transiciones: el estado origen, el estado destino
         y el símbolo de cada transición deben pertenecer a Q y a Sigma.
      3. Verificación determinista: debe existir EXACTAMENTE una transición
         por cada par (estado, símbolo) de Q x Sigma.

    Nota sobre "exactamente una": la posibilidad de tener MÁS de una
    transición para el mismo par ya queda descartada por construcción,
    porque delta es un diccionario (una clave = un único valor) y tanto
    cargador.py (creación manual y lectura de archivo) rechazan/reportan
    esos duplicados en el momento en que aparecen. Aquí solo puede faltar
    (contador == 0), nunca sobrar.

    Devuelve la tupla (errores, incompletas):
      - errores: violaciones estructurales graves que invalidan el AFD
        (no se pueden reparar automáticamente).
      - incompletas: lista de pares (estado, símbolo) sin transición
        definida. No se trata como error fatal porque el programa puede
        ofrecer completarlo con un estado de trampa (ver CE9).

    El AFD es válido, completo y determinista solo cuando ambas listas
    están vacías.
    """
    errores = []

    if afd.q0 not in afd.Q:
        errores.append(f"El estado inicial '{afd.q0}' no pertenece a Q = {sorted(afd.Q)}.")

    faltantes_F = afd.F - afd.Q
    if faltantes_F:
        errores.append(f"F no es subconjunto de Q. Estados finales inválidos: {sorted(faltantes_F)}.")

    for (origen, simbolo), destino in afd.delta.items():
        if origen not in afd.Q:
            errores.append(f"Transición inconsistente: el estado origen '{origen}' no pertenece a Q.")
        if simbolo not in afd.sigma:
            errores.append(f"Transición inconsistente: el símbolo '{simbolo}' no pertenece a Sigma.")
        if destino not in afd.Q:
            errores.append(f"Transición inconsistente: el estado destino '{destino}' no pertenece a Q.")

    incompletas = [
        (estado, simbolo)
        for estado in sorted(afd.Q)
        for simbolo in sorted(afd.sigma)
        if (estado, simbolo) not in afd.delta
    ]

    return errores, incompletas


def analizar_estructura(afd):
    """
    Análisis estructural del AFD (solo tiene sentido una vez validado):

      - Estados alcanzables desde q0: recorrido BFS/DFS siguiendo delta.
      - Estados inaccesibles: Q - alcanzables.
      - Estados finales alcanzables: F ∩ alcanzables.
      - Lenguaje potencialmente vacío: no hay ningún estado final
        alcanzable desde q0, por lo que ninguna cadena podría ser aceptada.

    Devuelve un AnalisisEstructural con los cuatro resultados anteriores.
    """
    alcanzables = set()
    pendientes = [afd.q0]
    while pendientes:
        estado = pendientes.pop()
        if estado in alcanzables:
            continue
        alcanzables.add(estado)
        for simbolo in afd.sigma:
            destino = afd.delta.get((estado, simbolo))
            if destino is not None and destino not in alcanzables:
                pendientes.append(destino)

    inaccesibles = afd.Q - alcanzables
    finales_alcanzables = afd.F & alcanzables
    lenguaje_vacio = len(finales_alcanzables) == 0

    return AnalisisEstructural(
        alcanzables=alcanzables,
        inaccesibles=inaccesibles,
        finales_alcanzables=finales_alcanzables,
        lenguaje_vacio=lenguaje_vacio,
    )


def completar_con_estado_trampa(afd):
    """
    CE9: completa un AFD incompleto agregando un estado de trampa (o
    "sumidero"), al que se dirigen todas las transiciones faltantes.
    Desde la trampa, cualquier símbolo del alfabeto regresa a la propia
    trampa (auto-transición), y la trampa nunca es estado de aceptación.

    Con esto el AFD queda completo y determinista sin alterar el lenguaje
    que reconocía originalmente: ninguna cadena que antes era aceptada deja
    de serlo, y las cadenas que antes "se caían" del autómata ahora
    terminan, de forma explícita, en un estado de rechazo.

    Modifica `afd` en el lugar y devuelve el nombre asignado al estado de
    trampa (evitando colisiones si ya existiera un estado con ese nombre).
    """
    nombre_trampa = "q_trampa"
    sufijo = 2
    while nombre_trampa in afd.Q:
        nombre_trampa = f"q_trampa_{sufijo}"
        sufijo += 1

    afd.Q.add(nombre_trampa)

    # Se recorre una copia de Q (que ya incluye la trampa) para que, de
    # una vez, se generen también las auto-transiciones de la propia
    # trampa hacia sí misma en cada símbolo del alfabeto.
    for estado in list(afd.Q):
        for simbolo in afd.sigma:
            if (estado, simbolo) not in afd.delta:
                afd.delta[(estado, simbolo)] = nombre_trampa

    return nombre_trampa
