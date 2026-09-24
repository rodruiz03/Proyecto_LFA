"""
main.py
-------
Punto de entrada del programa: Simulador y Validador de Autómatas Finitos
Deterministas (AFD).

Este archivo contiene el menú principal y la lógica de orquestación: decide
qué módulo invocar según la opción elegida y controla las reglas de acceso
entre opciones (por ejemplo, no se puede evaluar una cadena si todavía no
hay un AFD cargado y validado). No contiene lógica de carga, validación ni
simulación de AFD: esas responsabilidades están separadas en los módulos
cargador.py, validador.py y simulador.py, tal como exige el enunciado del
proyecto.

Universidad Rafael Landívar — Lenguajes Formales y Autómatas — Proyecto 1
"""

import sys
from dataclasses import dataclass

import cargador
import validador
import simulador
from colores import titulo, info, exito, error, advertencia

# El programa imprime símbolos como delta (δ), lambda (λ) y épsilon (ε).
# Algunas consolas de Windows usan, por defecto, una página de códigos
# (cp1252 o cp437) que no puede representar esos caracteres y lanzaría
# UnicodeEncodeError al hacer print(), colapsando el programa. Se fuerza la
# salida estándar a UTF-8 (con reemplazo de caracteres no soportados como
# último recurso) para que esto nunca ocurra, sin depender de ninguna
# librería externa.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Menú y lectura de la opción
# ---------------------------------------------------------------------------

def mostrar_menu():
    """Imprime el menú principal de 10 opciones."""
    print(titulo("\n===================================================="))
    print(titulo("  SIMULADOR Y VALIDADOR DE AUTÓMATAS FINITOS (AFD)"))
    print(titulo("===================================================="))
    print(" 1. Crear un AFD manualmente")
    print(" 2. Cargar un AFD desde archivo .txt")
    print(" 3. Mostrar la definición formal del AFD")
    print(" 4. Mostrar la tabla de transición")
    print(" 5. Validar la estructura del autómata")
    print(" 6. Evaluar una cadena")
    print(" 7. Evaluar un archivo de cadenas")
    print(" 8. Consultar el historial de evaluaciones")
    print(" 9. Cargar o crear otro autómata")
    print("10. Salir")


def pedir_opcion():
    """
    Lee la opción del menú y valida que sea un número entero entre 1 y 10.
    Cualquier entrada inválida (no numérica o fuera de rango) se rechaza
    con un mensaje claro, sin cerrar el programa; devuelve None en ese caso.
    """
    texto = input("\nSeleccione una opción (1-10): ").strip()
    if not texto.isdigit():
        print(error("Entrada inválida: debes ingresar un número entero."))
        return None
    opcion = int(texto)
    if opcion < 1 or opcion > 10:
        print(error("La opción debe estar entre 1 y 10."))
        return None
    return opcion


# ---------------------------------------------------------------------------
# Reglas de acceso entre opciones (ver Analisis_y_Diseno.md, sección 1)
# ---------------------------------------------------------------------------

def hay_automata_cargado(afd):
    """Las opciones 3, 4, 5, 6 y 7 requieren un AFD cargado."""
    if afd is None:
        print(error("No hay ningún autómata cargado. Usa la opción 1 o 2 primero."))
        return False
    return True


def esta_validado(afd):
    """Las opciones 6 y 7 requieren, además, que el AFD ya haya sido
    validado exitosamente (delta completo y sin errores estructurales)."""
    if not afd.validado:
        print(error("El autómata debe validarse exitosamente (opción 5) antes de evaluar cadenas."))
        return False
    return True


def puede_evaluar(afd):
    """Combina las dos reglas de acceso que comparten las opciones 6 y 7:
    debe haber un AFD cargado y, además, ya validado."""
    return hay_automata_cargado(afd) and esta_validado(afd)


# ---------------------------------------------------------------------------
# Historial de evaluaciones de la sesión (ver opciones 6, 7 y 8)
# ---------------------------------------------------------------------------

@dataclass
class RegistroHistorial:
    """Un evento del historial: el resultado de haber evaluado una cadena
    contra el autómata que estaba cargado en ese momento."""
    cadena: str
    veredicto: str
    traza: list
    automata: str


class Historial:
    """
    Guarda todas las cadenas evaluadas durante la sesión (opciones 6 y 7),
    independientemente del autómata que esté cargado en cada momento: los
    registros persisten aunque se cargue o cree otro autómata (opción 9).
    """

    def __init__(self):
        self._registros = []

    def agregar(self, afd, resultado):
        """Agrega el ResultadoEvaluacion de simulador.py al historial,
        junto con el nombre del autómata que se usó para obtenerlo."""
        self._registros.append(RegistroHistorial(
            cadena=resultado.cadena,
            veredicto=resultado.veredicto,
            traza=resultado.traza,
            automata=afd.nombre,
        ))

    def mostrar(self):
        """Opción 8: lista todas las cadenas evaluadas en la sesión, con
        su resultado."""
        if not self._registros:
            print(info("\nAún no se ha evaluado ninguna cadena en esta sesión."))
            return
        print(titulo(f"\nHistorial de evaluaciones ({len(self._registros)} cadena(s)):"))
        for i, registro in enumerate(self._registros, start=1):
            cadena_mostrar = registro.cadena if registro.cadena != "" else "λ (cadena vacía)"
            if registro.veredicto == "Aceptada":
                resultado_coloreado = exito(registro.veredicto)
            else:
                resultado_coloreado = error(registro.veredicto)
            print(f"  {i}. [{registro.automata}] \"{cadena_mostrar}\" -> {resultado_coloreado}")


# ---------------------------------------------------------------------------
# Acciones del menú
# ---------------------------------------------------------------------------

def accion_crear_manual():
    afd = cargador.crear_afd_manual()
    print(exito(f"\nAFD '{afd.nombre}' creado. Recuerda validarlo (opción 5) antes de evaluar cadenas."))
    return afd


def accion_cargar_archivo():
    ruta = input("Ruta del archivo .txt: ").strip()
    afd, errores = cargador.cargar_afd_desde_archivo(ruta)

    if errores:
        print(advertencia(f"\nSe encontraron {len(errores)} problema(s) al leer el archivo:"))
        for e in errores:
            print(error(f"  - {e}"))

    if afd is None:
        print(error("No se pudo construir el AFD: faltan componentes obligatorios en el archivo."))
        return None

    print(exito(f"\nAFD '{afd.nombre}' cargado. Recuerda validarlo (opción 5) antes de evaluar cadenas."))
    return afd


def accion_mostrar_definicion(afd):
    """Opción 3: imprime la quíntupla formal M = (Q, Sigma, delta, q0, F)."""
    print(titulo(f"\nDefinición formal de M = (Q, Sigma, delta, q0, F)  —  '{afd.nombre}'"))
    print(f"  Q     = {{{', '.join(sorted(afd.Q))}}}")
    print(f"  Sigma = {{{', '.join(sorted(afd.sigma))}}}")
    print(f"  q0    = {afd.q0}")
    print(f"  F     = {{{', '.join(sorted(afd.F))}}}")
    print("  delta:")
    for (estado, simbolo), destino in sorted(afd.delta.items()):
        print(f"    δ({estado}, {simbolo}) = {destino}")


def accion_mostrar_tabla(afd):
    """Opción 4: imprime delta como una matriz Q x Sigma."""
    estados = sorted(afd.Q)
    simbolos = sorted(afd.sigma)
    print(titulo(f"\nTabla de transición de '{afd.nombre}'"))

    ancho_estado = max(len(e) for e in estados + ["Estado"]) + 3
    encabezado = "Estado".ljust(ancho_estado) + "".join(s.center(8) for s in simbolos)
    print(encabezado)
    print("-" * len(encabezado))

    for estado in estados:
        marcas = ""
        if estado == afd.q0:
            marcas += "->"
        if estado in afd.F:
            marcas += "*"
        etiqueta = (marcas + estado) if marcas else estado
        fila = etiqueta.ljust(ancho_estado)
        for simbolo in simbolos:
            destino = afd.delta.get((estado, simbolo), "-")
            fila += destino.center(8)
        print(fila)

    print(info("  (-> estado inicial, * estado de aceptación, '-' = transición no definida)"))


def accion_validar(afd):
    """Opción 5: ejecuta el motor de validación y, si el AFD resulta
    válido, el análisis estructural. Si detecta un AFD incompleto, ofrece
    completarlo con un estado de trampa."""
    errores, incompletas = validador.validar_estructura(afd)

    if errores:
        print(error(f"\nEl autómata NO es válido. Se encontraron {len(errores)} error(es):"))
        for e in errores:
            print(error(f"  - {e}"))
        afd.validado = False
        return

    if incompletas:
        print(advertencia(f"\nEl AFD está incompleto: faltan {len(incompletas)} transición(es):"))
        for estado, simbolo in incompletas:
            print(advertencia(f"  - δ({estado}, {simbolo}) no está definida"))

        respuesta = input("¿Deseas completar el AFD agregando un estado de trampa? (S/N): ").strip().upper()
        if respuesta == "S":
            nombre_trampa = validador.completar_con_estado_trampa(afd)
            print(exito(f"Se agregó el estado de trampa '{nombre_trampa}'. El AFD ahora está completo."))
            errores, incompletas = validador.validar_estructura(afd)
        else:
            print(advertencia("El AFD quedó incompleto. No podrá evaluarse hasta completarlo o corregirlo."))
            afd.validado = False
            return

    # En este punto, o bien no había transiciones faltantes desde el
    # principio, o bien se completaron con un estado de trampa.
    if not errores and not incompletas:
        afd.validado = True
        print(exito("\nEl autómata es válido y determinista (AFD completo)."))

        analisis = validador.analizar_estructura(afd)
        print(titulo("\nAnálisis estructural:"))
        print(f"  Estados alcanzables: {', '.join(sorted(analisis.alcanzables)) or '(ninguno)'}")
        print(f"  Estados inaccesibles: {', '.join(sorted(analisis.inaccesibles)) or '(ninguno)'}")
        print(f"  Estados finales alcanzables: {', '.join(sorted(analisis.finales_alcanzables)) or '(ninguno)'}")
        if analisis.lenguaje_vacio:
            print(advertencia("  El lenguaje reconocido podría ser VACÍO (ningún estado final es alcanzable desde q0)."))
        else:
            print(exito("  El lenguaje reconocido NO es vacío."))


def accion_evaluar_cadena(afd, historial):
    """Opción 6: pide una cadena, la evalúa, imprime su traza y la agrega
    al historial de la sesión."""
    cadena = input("\nCadena a evaluar (deja vacío para la cadena λ): ")
    resultado = simulador.evaluar_cadena(afd, cadena)
    simulador.imprimir_traza(resultado)
    historial.agregar(afd, resultado)


def accion_evaluar_archivo(afd, historial):
    """Opción 7: evaluación por lote. Lee un archivo con una cadena por
    línea, evalúa cada una y agrega todas al historial, mostrando además
    un resumen final."""
    ruta = cargador.normalizar_ruta_archivo(input("\nRuta del archivo de cadenas: "))
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            cadenas = [linea.rstrip("\n").rstrip("\r") for linea in f]
    except FileNotFoundError:
        print(error(f"No se encontró el archivo '{ruta}'."))
        return
    except OSError as e:
        print(error(f"No se pudo abrir el archivo '{ruta}': {e}"))
        return

    resultados, resumen = simulador.evaluar_lote(afd, cadenas)
    for resultado in resultados:
        simulador.imprimir_traza(resultado)
        historial.agregar(afd, resultado)

    print(titulo("\nResumen de evaluación por lote:"))
    print(f"  Total evaluadas: {resumen['total']}")
    print(exito(f"  Aceptadas: {resumen['aceptadas']}"))
    print(error(f"  Rechazadas: {resumen['rechazadas']}"))


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------

def main():
    """
    Inicializa el estado de la sesión:
      - afd: el autómata actualmente cargado (None mientras no se cree o
        cargue ninguno).
      - historial: todas las cadenas evaluadas durante la sesión,
        independiente del autómata activo.
    Luego entra en el bucle del menú hasta que el usuario elige Salir.
    """
    afd = None
    historial = Historial()

    print(titulo("Bienvenido al Simulador y Validador de AFD"))
    print(info("Universidad Rafael Landívar — Lenguajes Formales y Autómatas — Proyecto 1"))

    while True:
        mostrar_menu()
        opcion = pedir_opcion()
        if opcion is None:
            continue  # entrada inválida: se vuelve a mostrar el menú

        if opcion == 1:
            afd = accion_crear_manual()

        elif opcion == 2:
            afd = accion_cargar_archivo()

        elif opcion == 3:
            if hay_automata_cargado(afd):
                accion_mostrar_definicion(afd)

        elif opcion == 4:
            if hay_automata_cargado(afd):
                accion_mostrar_tabla(afd)

        elif opcion == 5:
            if hay_automata_cargado(afd):
                accion_validar(afd)

        elif opcion == 6:
            if puede_evaluar(afd):
                accion_evaluar_cadena(afd, historial)

        elif opcion == 7:
            if puede_evaluar(afd):
                accion_evaluar_archivo(afd, historial)

        elif opcion == 8:
            historial.mostrar()

        elif opcion == 9:
            afd = None
            print(info("\nAutómata actual descartado. Usa la opción 1 o 2 para cargar uno nuevo."))

        elif opcion == 10:
            print(titulo("\n¡Hasta luego!"))
            break


if __name__ == "__main__":
    # Se protege el punto de entrada contra el cierre inesperado de la
    # entrada estándar (EOFError, por ejemplo si el usuario presiona
    # Ctrl+Z/Ctrl+D o si la entrada viene redirigida desde un archivo que
    # se agota) y contra la interrupción manual (Ctrl+C). En ambos casos el
    # programa debe terminar de forma controlada, nunca con un traceback.
    try:
        main()
    except EOFError:
        print(error("\nEntrada finalizada inesperadamente. Cerrando el programa."))
    except KeyboardInterrupt:
        print(error("\nPrograma interrumpido por el usuario."))
