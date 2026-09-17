"""
cargador.py
-----------
Funcionalidad 1: Carga del AFD.

Contiene dos formas de construir un objeto AFD:
  1. crear_afd_manual()         -> ingreso interactivo por consola.
  2. cargar_afd_desde_archivo() -> lectura y parseo de un archivo .txt
                                    usando expresiones regulares.

Este módulo NO valida las propiedades teóricas del autómata (eso es
responsabilidad de validador.py) ni simula cadenas (simulador.py): solo se
encarga de reunir los cinco componentes de la quíntupla y construir el
objeto AFD, evitando duplicados en el momento del ingreso/lectura.
"""

import os
import re

from automata import AFD
from colores import titulo, info, exito, error


# ---------------------------------------------------------------------------
# Expresiones regulares para reconocer cada línea del archivo de definición.
# Formato esperado (ver enunciado):
#
#   NOMBRE=AFD_AB
#   ESTADOS=q0,q1,q2
#   ALFABETO=a,b
#   INICIAL=q0
#   FINALES=q2
#   TRANSICIONES:
#   q0,a,q1
#   q0,b,q0
#   ...
# ---------------------------------------------------------------------------
PATRON_NOMBRE = re.compile(r'^NOMBRE=(.+)$')
PATRON_ESTADOS = re.compile(r'^ESTADOS=(.+)$')
PATRON_ALFABETO = re.compile(r'^ALFABETO=(.+)$')
PATRON_INICIAL = re.compile(r'^INICIAL=(.+)$')
PATRON_FINALES = re.compile(r'^FINALES=(.*)$')
PATRON_ENCABEZADO_TRANSICIONES = re.compile(r'^TRANSICIONES:$')
# origen,simbolo,destino  (origen/destino: identificadores; simbolo: cualquier
# token sin espacios ni comas, para no restringir alfabetos con símbolos raros)
PATRON_TRANSICION = re.compile(r'^([A-Za-z0-9_]+)\s*,\s*([^\s,]+)\s*,\s*([A-Za-z0-9_]+)$')
# Identificador válido para nombres de estado (letras, números, guion bajo)
PATRON_IDENTIFICADOR = re.compile(r'^[A-Za-z0-9_]+$')

# El símbolo épsilon está prohibido en el alfabeto y en las transiciones,
# porque un AFD (a diferencia de un AFN) no tiene transiciones vacías.
SIMBOLOS_PROHIBIDOS = {'ε', 'epsilon', 'Epsilon', 'EPSILON', 'ÉPSILON'}


def _separar_lista(texto):
    """
    Convierte "q0, q1,q2" en ["q0", "q1", "q2"]: separa por comas y
    elimina espacios en blanco y entradas vacías (por ejemplo si el
    usuario deja una coma de más al final).
    """
    return [t.strip() for t in texto.split(',') if t.strip() != '']


# ---------------------------------------------------------------------------
# 1. Ingreso interactivo (creación manual)
# ---------------------------------------------------------------------------

def crear_afd_manual():
    """
    Solicita cada elemento de la quíntupla paso a paso desde la consola,
    validando duplicados y consistencia en el momento del ingreso (no se
    espera a la Funcionalidad 2 para rechazar un dato claramente inválido).

    Devuelve un objeto AFD.
    """
    print(titulo("\n--- Creación manual de un AFD ---"))

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

    delta = _pedir_transiciones(Q, sigma)

    return AFD(nombre, Q, sigma, delta, q0, F)


def _pedir_conjunto(mensaje, prohibir_epsilon=False):
    """Pide una lista separada por comas y la convierte en set, sin
    permitir duplicados ni conjuntos vacíos."""
    while True:
        texto = input(mensaje)
        elementos = _separar_lista(texto)
        if len(elementos) == 0:
            print(error("Debes ingresar al menos un elemento."))
            continue
        if len(elementos) != len(set(elementos)):
            print(error("No se permiten elementos duplicados. Intenta de nuevo."))
            continue
        if prohibir_epsilon and any(s in SIMBOLOS_PROHIBIDOS for s in elementos):
            print(error("El símbolo épsilon (ε) no está permitido: un AFD no tiene transiciones vacías."))
            continue
        return set(elementos)


def _pedir_conjunto_final(Q):
    """Pide el conjunto F. A diferencia de Q y Sigma, F puede quedar
    vacío (un AFD sin estados de aceptación es válido, aunque su
    lenguaje sea vacío)."""
    while True:
        texto = input("Estados finales F (separados por coma, puede dejarse vacío): ")
        elementos = _separar_lista(texto)
        if len(elementos) != len(set(elementos)):
            print(error("No se permiten estados finales duplicados."))
            continue
        F = set(elementos)
        if not F.issubset(Q):
            faltantes = F - Q
            print(error(f"F debe ser subconjunto de Q. No pertenecen a Q: {sorted(faltantes)}"))
            continue
        return F


def _pedir_transiciones(Q, sigma):
    """Pide las transiciones una por una hasta que el usuario escriba FIN.
    Rechaza en el acto cualquier transición que use estados/símbolos fuera
    de Q/Sigma o que duplique una transición ya definida para el mismo
    par (estado, símbolo) — eso convertiría al autómata en un AFND."""
    print(info("\nIngresa las transiciones con el formato origen,simbolo,destino."))
    print(info("Escribe FIN cuando termines.\n"))
    delta = {}
    while True:
        entrada = input("Transición (o FIN): ").strip()
        if entrada.upper() == 'FIN':
            break
        partes = _separar_lista(entrada)
        if len(partes) != 3:
            print(error("Formato inválido. Usa: origen,simbolo,destino"))
            continue
        origen, simbolo, destino = partes
        if origen not in Q:
            print(error(f"El estado origen '{origen}' no pertenece a Q."))
            continue
        if destino not in Q:
            print(error(f"El estado destino '{destino}' no pertenece a Q."))
            continue
        if simbolo in SIMBOLOS_PROHIBIDOS:
            print(error("No se permiten transiciones épsilon (ε) en un AFD."))
            continue
        if simbolo not in sigma:
            print(error(f"El símbolo '{simbolo}' no pertenece a Sigma."))
            continue
        if (origen, simbolo) in delta:
            print(error(
                f"Ya existe una transición para ({origen}, {simbolo}) -> "
                f"{delta[(origen, simbolo)]}. No se permite una segunda "
                f"(el autómata dejaría de ser determinista)."
            ))
            continue
        delta[(origen, simbolo)] = destino
        print(exito(f"  δ({origen}, {simbolo}) = {destino}  agregada."))
    return delta


# ---------------------------------------------------------------------------
# 2. Carga por archivo .txt
# ---------------------------------------------------------------------------

def normalizar_ruta_archivo(ruta):
    """
    Normaliza una ruta de archivo ingresada por el usuario para que las
    rutas absolutas (y relativas) funcionen sin importar cómo se hayan
    escrito o pegado. En concreto, admite:
      - Espacios en blanco sobrantes al inicio o al final.
      - Comillas simples o dobles envolventes, como las que agrega
        Windows al usar "Copiar como ruta de acceso" (ej. "C:\\...\\a.txt").
      - El caracter '~' como atajo del directorio del usuario.
      - Variables de entorno, como %USERPROFILE% en Windows o $HOME en
        Unix.
      - Separadores de directorio mixtos ('/' y '\\').

    No verifica que el archivo exista ni lo abre: solo deja la ruta lista
    para usarse con open(). Esa verificación sigue haciéndose en el mismo
    lugar de siempre (el try/except sobre open()).
    """
    ruta = ruta.strip()
    if len(ruta) >= 2 and ruta[0] == ruta[-1] and ruta[0] in ('"', "'"):
        ruta = ruta[1:-1].strip()
    ruta = os.path.expandvars(ruta)
    ruta = os.path.expanduser(ruta)
    return os.path.normpath(ruta)


def cargar_afd_desde_archivo(ruta):
    """
    Lee el archivo línea por línea y reconoce cada línea mediante
    expresiones regulares. Si una línea no coincide con ningún patrón
    esperado, se acumula un error de sintaxis con su número de línea, pero
    la lectura continúa: el programa nunca colapsa por un archivo mal
    formado.

    Devuelve la tupla (afd, errores):
        afd     -> objeto AFD si se pudieron extraer los componentes
                   obligatorios (NOMBRE, ESTADOS, ALFABETO, INICIAL);
                   None si faltó alguno de ellos.
        errores -> lista de strings describiendo cada problema encontrado
                   (puede no estar vacía incluso si afd no es None, por
                   ejemplo por transiciones con formato inválido).
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
    transiciones_vistas = set()  # detecta (origen, simbolo) repetidos -> AFND

    for numero_linea, linea_cruda in enumerate(lineas, start=1):
        linea = linea_cruda.strip()
        if linea == "":
            continue  # se permiten líneas en blanco entre secciones

        # --- Sección de transiciones -----------------------------------
        if dentro_de_transiciones:
            m = PATRON_TRANSICION.match(linea)
            if not m:
                errores.append(
                    f"Línea {numero_linea}: transición con formato inválido "
                    f"-> '{linea}'. Se esperaba origen,simbolo,destino."
                )
                continue
            origen, simbolo, destino = m.group(1), m.group(2), m.group(3)
            if simbolo in SIMBOLOS_PROHIBIDOS:
                errores.append(f"Línea {numero_linea}: no se permiten transiciones épsilon (ε).")
                continue
            if (origen, simbolo) in transiciones_vistas:
                errores.append(
                    f"Línea {numero_linea}: transición múltiple para "
                    f"({origen}, {simbolo}) -> el autómata sería un AFND, no un AFD."
                )
                continue
            transiciones_vistas.add((origen, simbolo))
            delta[(origen, simbolo)] = destino
            continue

        # --- Secciones de la cabecera (NOMBRE, ESTADOS, ...) ------------
        m = PATRON_NOMBRE.match(linea)
        if m:
            nombre = m.group(1).strip()
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
                errores.append(f"Línea {numero_linea}: el símbolo épsilon (ε) no está permitido en el alfabeto.")
            # Se excluye epsilon del alfabeto aunque el usuario lo haya
            # escrito: ya se reportó como error, y un AFD nunca puede tener
            # epsilon como símbolo válido de Sigma.
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

    # Verificación de componentes obligatorios presentes en el archivo
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

    afd = AFD(nombre, Q, sigma, delta, q0, F)
    return afd, errores
