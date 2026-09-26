"""
main.py
-------
Punto de entrada del programa: Motor de Conversión de Autómatas Finitos No
Deterministas (AFND) a Autómatas Finitos Deterministas (AFD) y Simulación.

Este archivo contiene el menú principal y la lógica de orquestación: decide
qué módulo invocar según la opción elegida y controla las reglas de acceso
entre opciones. No contiene lógica de carga, validación, conversión ni
simulación: esas responsabilidades siguen separadas en cargador.py /
cargador_afnd.py, validador.py / validador_afnd.py, conversor.py y
simulador.py, tal como exige el enunciado del proyecto poruqe piden cierta 
modularidad de que existan de minimo 6 archivos para las actualizaciones

Fase 2 — evoluciona el programa de la Fase 1 sin eliminar ninguna de sus
funciones: un AFD creado o cargado directamente (opciones 1-2) sigue
operando exactamente igual que en la Fase 1 (mismos módulos validador.py y
simulador.py, sin modificar). Lo nuevo es que ahora también se puede
crear o cargar un AFND (opciones 3-4) y convertirlo a un AFD equivalente
(opción 7) para reutilizar sobre él todas las herramientas ya existentes.

Universidad Rafael Landívar — Lenguajes Formales y Autómatas — Proyecto 2
"""

import sys
from dataclasses import dataclass

import cargador
import cargador_afnd
import validador
import validador_afnd
import simulador
import conversor
from automata import AFD, AFND
from colores import titulo, info, exito, error, advertencia

# El programa imprime y ahora también LEE símbolos como delta (δ), lambda
# (λ) y conjunto vacío (∅) — este último se ingresa por teclado al crear un
# AFND manualmente (opción 3). Algunas consolas de Windows usan, por
# defecto, una página de códigos (cp1252 o cp437) que no puede representar
# esos caracteres: al imprimirlos lanzaría UnicodeEncodeError, y al leerlos
# desde teclado o desde una entrada redirigida los decodificaría mal (por
# ejemplo, ∅ llegaría como "âˆ…"), sin que el símbolo se reconociera nunca
# como "sin destino". Se fuerza tanto la entrada como la salida estándar a
# UTF-8 (con reemplazo de caracteres no soportados como último recurso)
# para que esto nunca ocurra, sin depender de ninguna librería externa.
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Menú y lectura de la opción
# ---------------------------------------------------------------------------

def mostrar_menu():
    """Imprime el menú principal de 15 opciones (Fase 1 + Fase 2)."""
    print(titulo("\n============================================================"))
    print(titulo("  MOTOR DE CONVERSIÓN AFND -> AFD Y SIMULACIÓN"))
    print(titulo("============================================================"))
    print(" 1. Crear un AFD manualmente")
    print(" 2. Cargar un AFD desde archivo .txt")
    print(" 3. Crear un AFND manualmente")
    print(" 4. Cargar un AFND desde archivo .txt")
    print(" 5. Mostrar la definición formal y la tabla del autómata cargado")
    print(" 6. Validar la estructura del autómata")
    print(" 7. Convertir el AFND cargado en un AFD equivalente")
    print(" 8. Mostrar la tabla de equivalencias de macroestados")
    print(" 9. Mostrar la tabla de transición del AFD generado")
    print("10. Evaluar una cadena")
    print("11. Evaluar un archivo de cadenas")
    print("12. Consultar el historial de evaluaciones")
    print("13. Realizar el análisis estructural")
    print("14. Cargar o crear otro autómata")
    print("15. Salir")


def pedir_opcion():
    """
    Lee la opción del menú y valida que sea un número entero entre 1 y 15.
    Cualquier entrada inválida (no numérica o fuera de rango) se rechaza
    con un mensaje claro, sin cerrar el programa; devuelve None en ese caso.
    """
    texto = input("\nSeleccione una opción (1-15): ").strip()
    if not texto.isdigit():
        print(error("Entrada inválida: debes ingresar un número entero."))
        return None
    opcion = int(texto)
    if opcion < 1 or opcion > 15:
        print(error("La opción debe estar entre 1 y 15."))
        return None
    return opcion


# ---------------------------------------------------------------------------
# Reglas de acceso entre opciones
# ---------------------------------------------------------------------------

def hay_automata_cargado(automata_cargado):
    """Las opciones 5 y 6 requieren un AFD o AFND cargado (recién creado
    o leído de archivo, sin importar si ya se validó)."""
    if automata_cargado is None:
        print(error("No hay ningún autómata cargado. Usa las opciones 1 a 4 primero."))
        return False
    return True


def obtener_afd_operable(automata_cargado, afd_generado):
    """
    Devuelve el AFD sobre el que deben operar las opciones 10, 11 y 13:

      - Si `automata_cargado` es un AFD (cargado directamente con las
        opciones 1 o 2), se devuelve tal cual: esto es lo que da
        compatibilidad total con la Fase 1, sin necesitar conversión.
      - Si `automata_cargado` es un AFND, se devuelve `afd_generado`
        (el resultado de la opción 7), o None si todavía no se convirtió.

    Si no hay nada disponible para operar, imprime un mensaje de error
    específico para el caso y devuelve None.
    """
    if automata_cargado is None:
        print(error("No hay ningún autómata cargado. Usa las opciones 1 a 4 primero."))
        return None

    if isinstance(automata_cargado, AFD):
        if not automata_cargado.validado:
            print(error("El AFD debe validarse (opción 6) antes de evaluar cadenas o analizar su estructura."))
            return None
        return automata_cargado

    # automata_cargado es un AFND
    if afd_generado is None:
        print(error("Este es un AFND: primero conviértelo a un AFD equivalente (opción 7)."))
        return None
    return afd_generado


# ---------------------------------------------------------------------------
# Historial de evaluaciones de la sesión (ver opciones 10, 11 y 12)
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
    Guarda las cadenas evaluadas (opciones 10 y 11) mientras el autómata
    activo no cambie. A diferencia de la Fase 1, el enunciado de la Fase 2
    exige limpiar el historial cada vez que se crea o carga un nuevo
    autómata (opciones 1-4 y 14): por eso main() crea una instancia nueva
    de Historial en cada una de esas acciones, en vez de reutilizar una
    sola instancia durante toda la sesión.
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
        """Opción 12: lista las cadenas evaluadas contra el autómata
        actualmente cargado."""
        if not self._registros:
            print(info("\nAún no se ha evaluado ninguna cadena con el autómata actual."))
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
# Acciones del menú — opciones 1 a 4 (creación / carga)
# ---------------------------------------------------------------------------

def accion_crear_manual():
    afd = cargador.crear_afd_manual()
    print(exito(f"\nAFD '{afd.nombre}' creado. Recuerda validarlo (opción 6) antes de evaluar cadenas."))
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

    print(exito(f"\nAFD '{afd.nombre}' cargado. Recuerda validarlo (opción 6) antes de evaluar cadenas."))
    return afd


def accion_crear_manual_afnd():
    afnd = cargador_afnd.crear_afnd_manual()
    print(exito(f"\nAFND '{afnd.nombre}' creado. Recuerda validarlo (opción 6) y luego convertirlo (opción 7)."))
    return afnd


def accion_cargar_archivo_afnd():
    ruta = input("Ruta del archivo .txt: ").strip()
    afnd, errores = cargador_afnd.cargar_afnd_desde_archivo(ruta)

    if errores:
        print(advertencia(f"\nSe encontraron {len(errores)} problema(s) al leer el archivo:"))
        for e in errores:
            print(error(f"  - {e}"))

    if afnd is None:
        print(error("No se pudo construir el AFND: faltan componentes obligatorios en el archivo."))
        return None

    print(exito(f"\nAFND '{afnd.nombre}' cargado. Recuerda validarlo (opción 6) y luego convertirlo (opción 7)."))
    return afnd


# ---------------------------------------------------------------------------
# Acciones del menú — opción 5 (definición + tabla del autómata cargado)
# ---------------------------------------------------------------------------

def accion_mostrar_definicion(afd):
    """Imprime la quíntupla formal M = (Q, Sigma, delta, q0, F) de un AFD."""
    print(titulo(f"\nDefinición formal de M = (Q, Sigma, delta, q0, F)  —  '{afd.nombre}' (AFD)"))
    print(f"  Q     = {{{', '.join(sorted(afd.Q))}}}")
    print(f"  Sigma = {{{', '.join(sorted(afd.sigma))}}}")
    print(f"  q0    = {afd.q0}")
    print(f"  F     = {{{', '.join(sorted(afd.F))}}}")
    print("  delta:")
    for (estado, simbolo), destino in sorted(afd.delta.items()):
        print(f"    δ({estado}, {simbolo}) = {destino}")


def accion_mostrar_tabla(afd):
    """Imprime delta como una matriz Q x Sigma para un AFD."""
    estados = sorted(afd.Q)
    simbolos = sorted(afd.sigma)
    print(titulo(f"\nTabla de transición de '{afd.nombre}' (AFD)"))

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


def accion_mostrar_definicion_afnd(afnd):
    """Igual que accion_mostrar_definicion, pero cada destino de delta es
    un conjunto (puede tener 0, 1 o varios estados)."""
    print(titulo(f"\nDefinición formal de M = (Q, Sigma, delta, q0, F)  —  '{afnd.nombre}' (AFND)"))
    print(f"  Q     = {{{', '.join(sorted(afnd.Q))}}}")
    print(f"  Sigma = {{{', '.join(sorted(afnd.sigma))}}}")
    print(f"  q0    = {afnd.q0}")
    print(f"  F     = {{{', '.join(sorted(afnd.F))}}}")
    print("  delta:")
    for (estado, simbolo), destinos in sorted(afnd.delta.items()):
        print(f"    δ({estado}, {simbolo}) = {conversor.formatear_subconjunto(destinos)}")


def accion_mostrar_tabla_afnd(afnd):
    """Igual que accion_mostrar_tabla, pero cada celda muestra un
    subconjunto de estados ("{q0, q1}") o ∅ en vez de un único destino."""
    estados = sorted(afnd.Q)
    simbolos = sorted(afnd.sigma)
    print(titulo(f"\nTabla de transición de '{afnd.nombre}' (AFND)"))

    celdas = {
        (estado, simbolo): conversor.formatear_subconjunto(afnd.transicion(estado, simbolo))
        for estado in estados
        for simbolo in simbolos
    }
    ancho_estado = max(len(e) for e in estados + ["Estado"]) + 3
    ancho_celda = max([len(v) for v in celdas.values()] + [6]) + 2

    encabezado = "Estado".ljust(ancho_estado) + "".join(s.center(ancho_celda) for s in simbolos)
    print(encabezado)
    print("-" * len(encabezado))

    for estado in estados:
        marcas = ""
        if estado == afnd.q0:
            marcas += "->"
        if estado in afnd.F:
            marcas += "*"
        etiqueta = (marcas + estado) if marcas else estado
        fila = etiqueta.ljust(ancho_estado)
        for simbolo in simbolos:
            fila += celdas[(estado, simbolo)].center(ancho_celda)
        print(fila)

    print(info("  (-> estado inicial, * estado de aceptación, ∅ = sin destino)"))


def accion_mostrar_automata_cargado(automata_cargado):
    """Opción 5: despacha a la impresión de AFD o de AFND según el tipo
    de lo que haya en `automata_cargado`."""
    if isinstance(automata_cargado, AFND):
        accion_mostrar_definicion_afnd(automata_cargado)
        accion_mostrar_tabla_afnd(automata_cargado)
    else:
        accion_mostrar_definicion(automata_cargado)
        accion_mostrar_tabla(automata_cargado)


# ---------------------------------------------------------------------------
# Acciones del menú — opción 6 (validar) y 13 (análisis estructural)
# ---------------------------------------------------------------------------

def imprimir_analisis_estructural(afd):
    """Ejecuta y muestra el análisis estructural (alcanzables,
    inaccesibles, finales alcanzables, lenguaje potencialmente vacío) de
    un AFD ya validado. La usan tanto la opción 6 (automáticamente, justo
    después de validar con éxito) como la opción 13 (bajo demanda)."""
    analisis = validador.analizar_estructura(afd)
    print(titulo("\nAnálisis estructural:"))
    print(f"  Estados alcanzables: {', '.join(sorted(analisis.alcanzables)) or '(ninguno)'}")
    print(f"  Estados inaccesibles: {', '.join(sorted(analisis.inaccesibles)) or '(ninguno)'}")
    print(f"  Estados finales alcanzables: {', '.join(sorted(analisis.finales_alcanzables)) or '(ninguno)'}")
    if analisis.lenguaje_vacio:
        print(advertencia("  El lenguaje reconocido podría ser VACÍO (ningún estado final es alcanzable desde q0)."))
    else:
        print(exito("  El lenguaje reconocido NO es vacío."))


def accion_validar_afd(afd):
    """Motor de validación de un AFD (Fase 1): estructura, completitud y,
    si es válido, estado de trampa opcional y análisis estructural."""
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

    if not errores and not incompletas:
        afd.validado = True
        print(exito("\nEl autómata es válido y determinista (AFD completo)."))
        imprimir_analisis_estructural(afd)


def accion_validar_afnd(afnd):
    """Motor de validación de un AFND (Fase 2): solo estructura (un AFND
    no tiene concepto de "incompleto")."""
    errores = validador_afnd.validar_estructura_afnd(afnd)

    if errores:
        print(error(f"\nEl AFND NO es válido. Se encontraron {len(errores)} error(es):"))
        for e in errores:
            print(error(f"  - {e}"))
        afnd.validado = False
        return

    afnd.validado = True
    print(exito("\nEl AFND es válido."))
    print(info("Usa la opción 7 para convertirlo en un AFD equivalente mediante construcción de subconjuntos."))


def accion_validar_automata_cargado(automata_cargado):
    """Opción 6: despacha a la validación de AFD o de AFND según el tipo
    de lo que haya en `automata_cargado`."""
    if isinstance(automata_cargado, AFND):
        accion_validar_afnd(automata_cargado)
    else:
        accion_validar_afd(automata_cargado)


# ---------------------------------------------------------------------------
# Acciones del menú — opción 7, 8 y 9 (conversión AFND -> AFD)
# ---------------------------------------------------------------------------

def accion_convertir(automata_cargado):
    """
    Opción 7: aplica el algoritmo de construcción de subconjuntos sobre
    `automata_cargado`. Devuelve (afd_generado, tabla_equivalencias), o
    (None, None) si todavía no hay un AFND válido cargado.
    """
    if not isinstance(automata_cargado, AFND):
        print(error("No hay ningún AFND cargado. Usa la opción 3 o 4 primero."))
        return None, None
    if not automata_cargado.validado:
        print(error("El AFND debe validarse exitosamente (opción 6) antes de convertirlo."))
        return None, None

    afd_generado, tabla_equivalencias = conversor.construir_afd_desde_afnd(automata_cargado)
    print(exito(f"\nConversión completada: se generaron {len(afd_generado.Q)} macroestado(s)."))
    print(info("Usa la opción 8 para ver la tabla de equivalencias, o la 9 para ver la tabla del AFD generado."))
    return afd_generado, tabla_equivalencias


def accion_mostrar_equivalencias(tabla_equivalencias):
    """Opción 8: relaciona cada macroestado del AFD generado con el
    subconjunto de estados del AFND que representa."""
    print(titulo("\nTabla de equivalencias de macroestados"))
    ancho = max(len(etiqueta) for etiqueta in tabla_equivalencias) + 3
    encabezado = "Macroestado".ljust(ancho) + "Conjunto de estados del AFND"
    print(encabezado)
    print("-" * len(encabezado))
    for etiqueta, subconjunto in tabla_equivalencias.items():
        print(etiqueta.ljust(ancho) + conversor.formatear_subconjunto(subconjunto))


# ---------------------------------------------------------------------------
# Acciones del menú — opciones 10 y 11 (evaluación)
# ---------------------------------------------------------------------------

def accion_evaluar_cadena(afd, historial):
    """Pide una cadena, la evalúa, imprime su traza y la agrega al
    historial del autómata actual."""
    cadena = input("\nCadena a evaluar (deja vacío para la cadena λ): ")
    resultado = simulador.evaluar_cadena(afd, cadena)
    simulador.imprimir_traza(resultado)
    historial.agregar(afd, resultado)


def accion_evaluar_archivo(afd, historial):
    """Evaluación por lote. Lee un archivo con una cadena por línea,
    evalúa cada una y agrega todas al historial, mostrando además un
    resumen final."""
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
      - automata_cargado: el AFD o AFND actualmente creado/cargado
        (opciones 1-4), None mientras no se cree o cargue ninguno.
      - afd_generado, tabla_equivalencias: resultado de la conversión
        (opción 7); None hasta que se convierta un AFND.
      - historial: cadenas evaluadas contra el autómata activo. Se
        reinicia cada vez que cambia el autómata (opciones 1-4 y 14), tal
        como exige el enunciado de la Fase 2.
    Luego entra en el bucle del menú hasta que el usuario elige Salir.
    """
    automata_cargado = None
    afd_generado = None
    tabla_equivalencias = None
    historial = Historial()

    print(titulo("Bienvenido al Motor de Conversión de Autómatas Finitos"))
    print(info("Universidad Rafael Landívar — Lenguajes Formales y Autómatas — Proyecto 2"))

    while True:
        mostrar_menu()
        opcion = pedir_opcion()
        if opcion is None:
            continue  # entrada inválida: se vuelve a mostrar el menú

        if opcion == 1:
            automata_cargado = accion_crear_manual()
            afd_generado = None
            tabla_equivalencias = None
            historial = Historial()

        elif opcion == 2:
            automata_cargado = accion_cargar_archivo()
            afd_generado = None
            tabla_equivalencias = None
            historial = Historial()

        elif opcion == 3:
            automata_cargado = accion_crear_manual_afnd()
            afd_generado = None
            tabla_equivalencias = None
            historial = Historial()

        elif opcion == 4:
            automata_cargado = accion_cargar_archivo_afnd()
            afd_generado = None
            tabla_equivalencias = None
            historial = Historial()

        elif opcion == 5:
            if hay_automata_cargado(automata_cargado):
                accion_mostrar_automata_cargado(automata_cargado)

        elif opcion == 6:
            if hay_automata_cargado(automata_cargado):
                accion_validar_automata_cargado(automata_cargado)

        elif opcion == 7:
            nuevo_afd_generado, nueva_tabla = accion_convertir(automata_cargado)
            if nuevo_afd_generado is not None:
                afd_generado = nuevo_afd_generado
                tabla_equivalencias = nueva_tabla

        elif opcion == 8:
            if tabla_equivalencias is None:
                print(error("Todavía no se ha convertido ningún AFND. Usa la opción 7 primero."))
            else:
                accion_mostrar_equivalencias(tabla_equivalencias)

        elif opcion == 9:
            if afd_generado is None:
                print(error("Todavía no se ha convertido ningún AFND. Usa la opción 7 primero."))
            else:
                accion_mostrar_tabla(afd_generado)

        elif opcion == 10:
            afd = obtener_afd_operable(automata_cargado, afd_generado)
            if afd is not None:
                accion_evaluar_cadena(afd, historial)

        elif opcion == 11:
            afd = obtener_afd_operable(automata_cargado, afd_generado)
            if afd is not None:
                accion_evaluar_archivo(afd, historial)

        elif opcion == 12:
            historial.mostrar()

        elif opcion == 13:
            afd = obtener_afd_operable(automata_cargado, afd_generado)
            if afd is not None:
                imprimir_analisis_estructural(afd)

        elif opcion == 14:
            automata_cargado = None
            afd_generado = None
            tabla_equivalencias = None
            historial = Historial()
            print(info("\nAutómata actual descartado. Usa las opciones 1 a 4 para cargar uno nuevo."))

        elif opcion == 15:
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
