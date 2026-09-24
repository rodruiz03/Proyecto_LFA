"""
cargador_afnd.py
----------------
Funcionalidad 1 de la Fase 2: carga y creación de un AFND.

Es el equivalente de cargador.py (Fase 1) pero para autómatas donde un
mismo par (estado, símbolo) puede tener cero, uno o varios destinos. Se
reutilizan de cargador.py las piezas que no dependen de esa diferencia
(separar listas, pedir conjuntos, normalizar rutas de archivo, patrón de
identificador, símbolos épsilon prohibidos) en vez de duplicarlas.
"""

import re

from automata import AFND
from cargador import (
    PATRON_IDENTIFICADOR,
    SIMBOLOS_PROHIBIDOS,
    _pedir_conjunto,
    _pedir_conjunto_final,
    _separar_lista,
    normalizar_ruta_archivo,
)
from colores import titulo, info, exito, error

# ---------------------------------------------------------------------------
# Expresiones regulares para el archivo de definición de un AFND. El formato
# de cabecera (NOMBRE, ESTADOS, ALFABETO, INICIAL, FINALES) es idéntico al
# del AFD; solo cambia la línea de transición, cuyo destino puede traer
# varios estados separados por "|", o el símbolo ∅ para "sin destino".
# ---------------------------------------------------------------------------
PATRON_NOMBRE = re.compile(r'^NOMBRE=(.+)$')
PATRON_TIPO = re.compile(r'^TIPO=(.+)$')
PATRON_ESTADOS = re.compile(r'^ESTADOS=(.+)$')
PATRON_ALFABETO = re.compile(r'^ALFABETO=(.+)$')
PATRON_INICIAL = re.compile(r'^INICIAL=(.+)$')
PATRON_FINALES = re.compile(r'^FINALES=(.*)$')
PATRON_ENCABEZADO_TRANSICIONES = re.compile(r'^TRANSICIONES:$')
# origen,simbolo,destino1|destino2|...  (o ∅ / vacío para "sin destino")
PATRON_TRANSICION_AFND = re.compile(r'^([A-Za-z0-9_]+)\s*,\s*([^\s,]+)\s*,\s*(.*)$')

# Tokens que representan "sin destino" (conjunto vacío) en la columna de
# destino de una transición.
TOKENS_SIN_DESTINO = {'∅', ''}


def _separar_destinos(texto):
    """
    Convierte la columna de destino de una transición ("q0|q1", "∅" o "")
    en un frozenset de nombres de estado. "∅" y la cadena vacía representan
    una transición sin destinos, no un error.
    """
    texto = texto.strip()
    if texto in TOKENS_SIN_DESTINO:
        return frozenset()
    return frozenset(_separar_lista(texto.replace('|', ',')))


# ---------------------------------------------------------------------------
# 1. Ingreso interactivo (creación manual)
# ---------------------------------------------------------------------------

def crear_afnd_manual():
    """
    Solicita cada elemento de la quíntupla de un AFND paso a paso desde la
    consola. A diferencia de crear_afd_manual, cada transición admite 0, 1
    o varios destinos para el mismo par (estado, símbolo).

    Devuelve un objeto AFND.
    """
    print(titulo("\n--- Creación manual de un AFND ---"))

    nombre = input("Nombre del autómata: ").strip()
    while nombre == "":
        nombre = input(error("El nombre no puede estar vacío. Nombre: ")).strip()

    Q = _pedir_conjunto("Estados Q (separados por coma, ej. q0,q1,q2): ")
    sigma = _pedir_conjunto(
        "Alfabeto Sigma (separado por coma, ej. a,b): ", prohibir_epsilon=True
    )

    q0 = input("Estado inicial q0: ").strip()
    while q0 not in Q:
        print(error(f"El estado inicial debe pertenecer a Q = {sorted(Q)}."))
        q0 = input("Estado inicial q0: ").strip()

    F = _pedir_conjunto_final(Q)

    delta = _pedir_transiciones_afnd(Q, sigma)

    return AFND(nombre, Q, sigma, delta, q0, F)


def _pedir_transiciones_afnd(Q, sigma):
    """
    Pide las transiciones de un AFND una por una hasta que el usuario
    escriba FIN. Cada transición se ingresa con el formato
    origen,simbolo,destino1|destino2|... (usa ∅ o deja el destino vacío
    para una transición sin destinos). No se permite declarar dos veces el
    mismo par (estado, símbolo): si tiene varios destinos, deben listarse
    todos juntos separados por "|" en una sola línea.
    """
    print(info("\nIngresa las transiciones con el formato origen,simbolo,destino1|destino2|..."))
    print(info("Usa ∅ (o deja el destino vacío) para una transición sin destinos."))
    print(info("Escribe FIN cuando termines.\n"))
    delta = {}
    while True:
        entrada = input("Transición (o FIN): ").strip()
        if entrada.upper() == 'FIN':
            break
        partes = entrada.split(',', 2)
        if len(partes) != 3:
            print(error("Formato inválido. Usa: origen,simbolo,destino1|destino2|..."))
            continue
        origen, simbolo, texto_destino = (p.strip() for p in partes)
        if origen not in Q:
            print(error(f"El estado origen '{origen}' no pertenece a Q."))
            continue
        if simbolo in SIMBOLOS_PROHIBIDOS:
            print(error("No se admiten transiciones épsilon (ε): no forman parte del alcance de esta fase."))
            continue
        if simbolo not in sigma:
            print(error(f"El símbolo '{simbolo}' no pertenece a Sigma."))
            continue
        if (origen, simbolo) in delta:
            print(error(
                f"Ya existe una transición para ({origen}, {simbolo}). "
                f"Si tiene varios destinos, ingrésalos juntos separados por '|'."
            ))
            continue
        destinos = _separar_destinos(texto_destino)
        invalidos = [d for d in destinos if d not in Q]
        if invalidos:
            print(error(f"Los siguientes destinos no pertenecen a Q: {sorted(invalidos)}"))
            continue
        delta[(origen, simbolo)] = destinos
        etiqueta_destinos = "{" + ", ".join(sorted(destinos)) + "}" if destinos else "∅"
        print(exito(f"  δ({origen}, {simbolo}) = {etiqueta_destinos}  agregada."))
    return delta


# ---------------------------------------------------------------------------
# 2. Carga por archivo .txt
# ---------------------------------------------------------------------------

def cargar_afnd_desde_archivo(ruta):
    """
    Lee y parsea un archivo de definición de AFND (ver formato en el
    enunciado de la Fase 2). Igual que cargar_afd_desde_archivo, nunca
    lanza una excepción por un archivo mal formado: acumula errores y
    sigue leyendo.

    Devuelve la tupla (afnd, errores).
    """
    ruta = normalizar_ruta_archivo(ruta)
    errores = []
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
    except FileNotFoundError:
        return None, [f"No se encontró el archivo '{ruta}'."]
    except OSError as e:
        return None, [f"No se pudo abrir el archivo '{ruta}': {e}"]

    nombre = None
    Q = None
    sigma = None
    q0 = None
    F = set()
    delta = {}
    dentro_de_transiciones = False

    for numero_linea, linea_cruda in enumerate(lineas, start=1):
        linea = linea_cruda.strip()
        if linea == "":
            continue

        # --- Sección de transiciones -----------------------------------
        if dentro_de_transiciones:
            m = PATRON_TRANSICION_AFND.match(linea)
            if not m:
                errores.append(
                    f"Línea {numero_linea}: transición con formato inválido "
                    f"-> '{linea}'. Se esperaba origen,simbolo,destino1|destino2|..."
                )
                continue
            origen, simbolo, texto_destino = m.group(1), m.group(2), m.group(3)
            if simbolo in SIMBOLOS_PROHIBIDOS:
                errores.append(
                    f"Línea {numero_linea}: las transiciones épsilon (ε) no "
                    f"forman parte del alcance solicitado en esta fase."
                )
                continue
            if (origen, simbolo) in delta:
                errores.append(
                    f"Línea {numero_linea}: ya existía una transición para "
                    f"({origen}, {simbolo}). Declara todos sus destinos juntos "
                    f"separados por '|' en una sola línea."
                )
                continue
            destinos = _separar_destinos(texto_destino)
            delta[(origen, simbolo)] = destinos
            continue

        # --- Secciones de la cabecera ------------------------------------
        m = PATRON_NOMBRE.match(linea)
        if m:
            nombre = m.group(1).strip()
            continue

        m = PATRON_TIPO.match(linea)
        if m:
            tipo = m.group(1).strip().upper()
            if tipo != 'AFND':
                errores.append(
                    f"Línea {numero_linea}: TIPO='{tipo}' no coincide con AFND "
                    f"(se cargó de todas formas con la opción de AFND)."
                )
            continue

        m = PATRON_ESTADOS.match(linea)
        if m:
            elementos = _separar_lista(m.group(1))
            if len(elementos) != len(set(elementos)):
                errores.append(f"Línea {numero_linea}: ESTADOS contiene elementos duplicados.")
            invalidos = [e for e in elementos if not PATRON_IDENTIFICADOR.match(e)]
            if invalidos:
                errores.append(f"Línea {numero_linea}: nombres de estado inválidos: {invalidos}.")
            Q = set(elementos)
            continue

        m = PATRON_ALFABETO.match(linea)
        if m:
            elementos = _separar_lista(m.group(1))
            if len(elementos) != len(set(elementos)):
                errores.append(f"Línea {numero_linea}: ALFABETO contiene símbolos duplicados.")
            if any(s in SIMBOLOS_PROHIBIDOS for s in elementos):
                errores.append(
                    f"Línea {numero_linea}: el símbolo épsilon (ε) no forma "
                    f"parte del alcance solicitado en esta fase."
                )
            sigma = set(s for s in elementos if s not in SIMBOLOS_PROHIBIDOS)
            continue

        m = PATRON_INICIAL.match(linea)
        if m:
            valor = m.group(1).strip()
            if not PATRON_IDENTIFICADOR.match(valor):
                errores.append(f"Línea {numero_linea}: INICIAL contiene un valor inválido -> '{valor}'.")
            q0 = valor
            continue

        m = PATRON_FINALES.match(linea)
        if m:
            elementos = _separar_lista(m.group(1))
            invalidos = [e for e in elementos if not PATRON_IDENTIFICADOR.match(e)]
            if invalidos:
                errores.append(f"Línea {numero_linea}: nombres de estado final inválidos: {invalidos}.")
            F = set(elementos)
            continue

        if PATRON_ENCABEZADO_TRANSICIONES.match(linea):
            dentro_de_transiciones = True
            continue

        errores.append(f"Línea {numero_linea}: no coincide con ningún patrón reconocido -> '{linea}'.")

    if nombre is None:
        errores.append("Falta la línea NOMBRE= en el archivo.")
    if Q is None:
        errores.append("Falta la línea ESTADOS= en el archivo.")
    if sigma is None:
        errores.append("Falta la línea ALFABETO= en el archivo.")
    if q0 is None:
        errores.append("Falta la línea INICIAL= en el archivo.")

    if nombre is None or Q is None or sigma is None or q0 is None:
        return None, errores

    afnd = AFND(nombre, Q, sigma, delta, q0, F)
    return afnd, errores
