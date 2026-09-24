"""
validador_afnd.py
------------------
Funcionalidad 1 (validación) de la Fase 2: verifica que la quíntupla de un
AFND ya construido sea estructuralmente correcta.

A diferencia de validador.py (AFD), aquí NO existe el concepto de
"incompleto": un par (estado, símbolo) sin transición declarada
simplemente se interpreta como una transición hacia ∅ (ver
AFND.transicion en automata.py), lo cual es válido en un AFND. Por eso
esta función solo puede devolver errores estructurales graves.
"""


def validar_estructura_afnd(afnd):
    """
    Aplica las reglas de validación de un AFND:

      1. El estado inicial q0 pertenece a Q.
      2. F es subconjunto de Q.
      3. El origen, el símbolo y cada uno de los destinos de toda
         transición declarada pertenecen a Q y a Sigma respectivamente.

    Devuelve la lista `errores` (vacía si el AFND es válido).
    """
    errores = []

    if afnd.q0 not in afnd.Q:
        errores.append(f"El estado inicial '{afnd.q0}' no pertenece a Q = {sorted(afnd.Q)}.")

    faltantes_F = afnd.F - afnd.Q
    if faltantes_F:
        errores.append(f"F no es subconjunto de Q. Estados finales inválidos: {sorted(faltantes_F)}.")

    for (origen, simbolo), destinos in afnd.delta.items():
        if origen not in afnd.Q:
            errores.append(f"Transición inconsistente: el estado origen '{origen}' no pertenece a Q.")
        if simbolo not in afnd.sigma:
            errores.append(f"Transición inconsistente: el símbolo '{simbolo}' no pertenece a Sigma.")
        faltantes_destino = destinos - afnd.Q
        if faltantes_destino:
            errores.append(
                f"Transición inconsistente: los siguientes destinos de "
                f"({origen}, {simbolo}) no pertenecen a Q: {sorted(faltantes_destino)}."
            )

    return errores
