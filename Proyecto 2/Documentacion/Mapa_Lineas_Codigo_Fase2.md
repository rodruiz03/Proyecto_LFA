# Mapa línea por línea de los .py (Fase 2)

> Mismo ejercicio que hicimos juntos con `cargador_afnd.py` (opción 3), pero
> para los 9 archivos. Por cada función marco qué línea(s) corresponden a
> **Acción**, **Dato de entrada**, **Variable**, **Condición/Cálculo** o
> **Estructura de datos** — así no tienes que releer todo el archivo para
> saber en qué columna del manual/análisis va cada parte. Donde el patrón ya
> se explicó una vez, digo "patrón ya visto" en vez de repetirlo.
>
> Los archivos que la Fase 2 dejó **intactos** (`colores.py`, `simulador.py`,
> `validador.py`) casi no necesitan mapa nuevo: ya los documentaste en
> `Manual_Tecnico_Opciones_del_Menu.md` de la Fase 1 (opciones 5, 6 y 7 de
> ese documento). Aquí solo señalo qué cambió de contexto (quién los llama
> ahora) y confirmo que el código en sí es el mismo.

---

## `automata.py`

**Clase `AFD`** (líneas 23-71) — sin cambios respecto a Fase 1.
- Líneas 50-57 (`__init__`): Estructura de datos — construye la quíntupla; `self.delta = dict(delta)` (línea 54) es la Variable central: un destino por clave.
- Línea 57: `self.validado = False` — Condición inicial (todo autómata nace sin validar).
- Líneas 59-65 (`transicion`): Cálculo — esta es LA función de transición δ genérica (`delta.get((estado,simbolo))`), la que reemplaza cualquier if/elif. Devuelve `None` si no hay transición = AFD incompleto.

**Clase `AFND`** (líneas 74-127) — nueva en Fase 2, mismo patrón que `AFD` con una diferencia clave:
- Línea 108: `self.delta = {clave: frozenset(destinos) for clave, destinos in delta.items()}` — Estructura de datos MÁS IMPORTANTE de toda la Fase 2: cada valor de `delta` es un `frozenset`, no un `str`. Esto es lo primero que hay que explicar en la sección "estructuras de datos" del análisis.
- Líneas 113-121 (`transicion`): Cálculo — `return self.delta.get((estado, simbolo), frozenset())`. Nota el segundo argumento de `.get`: a diferencia del AFD (que devuelve `None` = incompleto = error), aquí la ausencia de la clave devuelve `frozenset()` = ∅ = **válido**, no un error. Esta única línea es la que explica por qué un AFND "no tiene incompletas".

---

## `cargador.py` (sin cambios de código; ya documentado en Fase 1)

- Líneas 38-48: Expresiones regulares (`PATRON_NOMBRE` ... `PATRON_TRANSICION`, `PATRON_IDENTIFICADOR`) y línea 52 `SIMBOLOS_PROHIBIDOS` — van directo a la tabla de regex del análisis (ver también `Guia_Rapida_Analisis_Fase2.md`, sección 3).
- `crear_afd_manual` (líneas 68-96) y sus helpers `_pedir_conjunto` (99-114), `_pedir_conjunto_final` (117-132), `_pedir_transiciones` (135-173): patrón repetido "input + while" ya visto — cada uno pide un dato, valida (sin vacíos/duplicados/épsilon/subconjunto de Q) y vuelve a pedir si falla.
- `normalizar_ruta_archivo` (180-201): Acción de saneamiento, no de validación — quita comillas, expande `~`/variables de entorno, unifica separadores. Dato de entrada: ruta (str). No aplica ninguna restricción estructural.
- `cargar_afd_desde_archivo` (204-334): documentada opción por opción en `Manual_Tecnico_Opciones_del_Menu.md` de Fase 1 (opción 2) — reutilízalo casi literal, solo renombra "opción 2" si hace falta.

**Contexto nuevo en Fase 2**: estas dos funciones ahora las llaman `main.accion_crear_manual()` y `main.accion_cargar_archivo()`, y su resultado ya no se guarda en una variable `afd` fija sino en `automata_cargado` (que también puede contener un `AFND`).

---

## `cargador_afnd.py`

- Líneas 16-23: importa de `cargador.py` en vez de duplicar — nota para la sección de "reutilización de código" del análisis: `PATRON_IDENTIFICADOR`, `SIMBOLOS_PROHIBIDOS`, `_pedir_conjunto`, `_pedir_conjunto_final`, `_separar_lista`, `normalizar_ruta_archivo`.
- Líneas 32-40: Expresiones regulares nuevas — `PATRON_TIPO` (línea 33, la única que no existe en `cargador.py`) y `PATRON_TRANSICION_AFND` (línea 40): fíjate que el grupo 3 es `(.*)$` (cualquier cosa), no `([A-Za-z0-9_]+)$` como en el AFD — ahí es donde vive la diferencia "un destino" vs "varios destinos separados por `|`".
- Línea 44: `TOKENS_SIN_DESTINO = {'∅', ''}` — Restricción/convención: qué cuenta como "sin destino".
- `_separar_destinos` (líneas 47-56): Cálculo clave — línea 54 `if texto in TOKENS_SIN_DESTINO: return frozenset()`, si no, línea 56 separa por `|` y arma el `frozenset`. Esta función es la que convierte texto en el tipo de dato que exige `AFND.delta`.
- `crear_afnd_manual` (63-91) y `_pedir_transiciones_afnd` (94-139): ya los recorrimos juntos línea por línea (ver conversación anterior). En resumen: líneas 73-75 y 82-85 = patrón "input+while" ya visto; línea 125 (`if (origen, simbolo) in delta`) es la Condición que distingue Fase 2 de Fase 1 (aquí se pide unir con `|`, en Fase 1 era error fatal); línea 131 (`destinos = _separar_destinos(...)`) + línea 132 (`invalidos = [d for d in destinos if d not in Q]`) son el Cálculo/Restricción de validar cada destino contra Q.
- `cargar_afnd_desde_archivo` (146-281): mismo esqueleto que `cargador.cargar_afd_desde_archivo`, con 3 diferencias puntuales para citar en el análisis:
  - Líneas 211-219: manejo de `TIPO=` — Dato de entrada opcional + Condición ("si no es AFND, se agrega un aviso pero NO se bloquea la carga").
  - Línea 194 (`if (origen, simbolo) in delta`): mismo cambio de criterio que en la versión manual (unir con `|` en vez de rechazar).
  - Línea 201 (`destinos = _separar_destinos(texto_destino)`): aquí NO se valida que los destinos pertenezcan a Q (eso se deja para `validador_afnd.py`, opción 6) — mismo diseño que `cargador.py` (que tampoco valida Q al leer el archivo).

---

## `validador.py` (sin cambios de código; ya documentado en Fase 1, opción 5)

- `validar_estructura` (29-80): Acciones/Restricciones ya documentadas (q0∈Q, F⊆Q, transiciones consistentes, `incompletas`).
- `analizar_estructura` (83-116): Cálculo (BFS/DFS de alcanzables, `inaccesibles = Q - alcanzables`, `finales_alcanzables = F & alcanzables`).
- `completar_con_estado_trampa` (119-150): Acción (agrega `q_trampa` y sus auto-transiciones).

**Contexto nuevo en Fase 2**: `analizar_estructura` ya no vive solo "dentro" de validar — `main.imprimir_analisis_estructural` (línea 347 de `main.py`) la llama por separado para la opción 13, y también automáticamente dentro de `accion_validar_afd` (línea 393). Es el mismo código, dos puntos de entrada — buen ejemplo de "reutilización de funciones de la Fase 1" para el análisis.

---

## `validador_afnd.py`

- `validar_estructura_afnd` (líneas 15-46): estructura idéntica en espíritu a `validador.validar_estructura`, pero más corta:
  - Línea 24: `if afnd.q0 not in afnd.Q` — Condición (igual que en AFD).
  - Línea 28: `faltantes_F = afnd.F - afnd.Q` — Cálculo (igual que en AFD).
  - Líneas 31-38 (el `for` sobre `afnd.delta.items()`): aquí está la diferencia — línea 36 `faltantes_destino = destinos - afnd.Q` usa resta de **conjuntos** (`destinos` es un `frozenset`) en vez de comparar un único string contra `Q`, porque puede haber varios destinos a la vez.
  - **Lo que NO existe aquí, y hay que decirlo explícitamente en el análisis**: no hay ningún cálculo de "incompletas" ni llamada a completar con trampa — un AFND no tiene ese concepto (ver `automata.AFND.transicion`, línea 121).

---

## `conversor.py` (todo es nuevo en Fase 2 — el corazón de la Funcionalidad 2 del enunciado)

- Línea 29: `ALFABETO_ETIQUETAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"` — Estructura de datos de apoyo (constante).
- `_siguiente_etiqueta` (32-43): Cálculo — convierte un índice en una etiqueta estilo columnas de Excel. Línea 41 (`indice, resto = divmod(indice - 1, 26)`) es la línea a explicar si te preguntan "¿por qué A,B,...,Z,AA,AB?" en la defensa.
- `formatear_subconjunto` (46-51): Acción de presentación — decide si se imprime `∅` o `{q0, q1}`. La usan `main.py` (opciones 5, 8 y 9) además de este módulo.
- `construir_afd_desde_afnd` (54-110) — repásalo con la tabla de la sección 4 de `Guia_Rapida_Analisis_Fase2.md`; aquí van las líneas exactas de cada paso:
  - Línea 67: `macroestado_inicial = frozenset({afnd.q0})` — Dato de entrada derivado (paso 1 del algoritmo).
  - Líneas 69-72: Variables del algoritmo — `etiquetas` (dict), `orden_descubrimiento` (list), `pendientes` (deque = cola), `delta_afd` (dict, se va llenando).
  - Línea 74 (`while pendientes:`) + línea 75 (`actual = pendientes.popleft()`): Condición/Acción — este es el BFS.
  - Líneas 76-79 (el `for simbolo` + el `for estado in actual`): Cálculo — la unión de destinos, símbolo por símbolo.
  - Líneas 81-84: Condición — "¿es un macroestado nuevo?" y, si sí, se etiqueta y se encola.
  - Línea 86: se registra la transición del AFD generado.
  - Líneas 88-93: Cálculo final — `Q_afd` (todas las etiquetas) y `F_afd` (macroestados que intersectan `afnd.F`, línea 92 `if subconjunto & afnd.F`).
  - Líneas 95-105: Acción — se construye el `AFD` de salida y se marca `validado = True` (línea 105) porque, por construcción, siempre es completo y determinista.
  - Líneas 107-109: se arma `tabla_equivalencias`.

---

## `simulador.py` (sin cambios de código; ya documentado en Fase 1, opciones 6 y 7)

- `evaluar_cadena` (54-94) y `evaluar_lote` (97-121): mismas Acciones/Condiciones/Cálculos de Fase 1.
- `imprimir_traza` (124-147): igual, sin cambios.

**Contexto nuevo en Fase 2**: ahora reciben el AFD que devuelve `main.obtener_afd_operable(...)` (línea 109 de `main.py`), que puede ser un AFD cargado directamente O el AFD generado por una conversión — el módulo en sí no sabe ni le importa de dónde vino, prueba clara de por qué reutilizarlo sin tocarlo cumple el "principio de compatibilidad" del enunciado.

---

## `colores.py` (sin cambios; utilitario puro)

No aporta Acciones/Datos/Restricciones propias — es infraestructura de presentación (códigos ANSI). Vale la pena mencionarlo en el análisis solo en la sección de "estructuras y decisiones de diseño" (por qué se implementó a mano en vez de usar `colorama`).

---

## `main.py` (reescrito para la Fase 2 — es el archivo con más "decisiones de diseño" para explicar)

- `mostrar_menu` (57-76) / `pedir_opcion` (79-93): Dato de entrada = opción (int); Restricción = entero entre 1 y 15 (línea 86 `texto.isdigit()`, línea 90 `1 <= opcion <= 15`).
- `hay_automata_cargado` (100-106): guardia simple, usada por la opción 5 y como primer paso de la 6.
- `obtener_afd_operable` (109-136): **la función más importante para explicar la compatibilidad Fase 1 ↔ Fase 2**. Línea 126 (`isinstance(automata_cargado, AFD)`) decide si se devuelve tal cual (compatibilidad directa) o si se exige `afd_generado` (línea 133, caso AFND). La usan las opciones 10, 11 y 13.
- `RegistroHistorial` (144-150) / `Historial` (153-189): Estructuras de datos — dataclass + clase contenedora. Línea 176-181 (`mostrar`): Acción de la opción 12.
- `accion_crear_manual` / `accion_cargar_archivo` / `accion_crear_manual_afnd` / `accion_cargar_archivo_afnd` (196-239): son envoltorios delgados — la lógica real está en `cargador.py`/`cargador_afnd.py`; aquí solo se agrega el mensaje de éxito/error (Acción de presentación).
- `accion_mostrar_definicion`/`accion_mostrar_tabla` (246-282) y sus pares `_afnd` (285-329): Cálculo de formato — `ancho_estado`/`ancho_celda` (líneas 264, 310-311) se calculan según el contenido más largo, para que la tabla no se desalinee ni con AFD ni con AFND.
- `accion_mostrar_automata_cargado` (332-340): primer despachador `isinstance` (línea 335) — patrón que se repite en `accion_validar_automata_cargado`.
- `imprimir_analisis_estructural` (347-360): Acción compartida (la llaman la opción 6 automáticamente y la opción 13 bajo demanda).
- `accion_validar_afd` (363-393) / `accion_validar_afnd` (396-410) / `accion_validar_automata_cargado` (413-419): segundo despachador `isinstance` (línea 416).
- `accion_convertir` (426-442): dos guardias en cascada — línea 432 (`isinstance(..., AFND)`) y línea 435 (`.validado`) — antes de llamar a `conversor.construir_afd_desde_afnd` (línea 439).
- `accion_mostrar_equivalencias` (445-454): Acción simple de presentación de `tabla_equivalencias`.
- `accion_evaluar_cadena` (461-467) / `accion_evaluar_archivo` (470-493): sin cambios de lógica respecto a Fase 1, salvo que reciben `afd` ya resuelto por `obtener_afd_operable`.
- `main()` (500-603): Variables de sesión (líneas 512-515) y el `if/elif` de 15 ramas (526-603). Fíjate en el patrón repetido en las opciones 1-4 (líneas 527-548): cada una reinicia `afd_generado`, `tabla_equivalencias` e `historial` — esa es la regla de la Fase 2 "al cargar un nuevo autómata se limpian los datos anteriores", en código.
