# Guía rápida — Glosario y mapa de opciones (Fase 2)

> Esto NO es el documento de análisis y diseño. Es material de consulta para
> que armes ese documento más rápido: por cada opción del menú indica qué
> módulo/función lo implementa, qué clases usa, qué datos de entrada pide y
> qué restricciones aplica — en formato tabla/lista, sin redactar párrafos.
> La redacción final (acciones explicadas, justificación, diagramas
> integrados) la haces tú.

---

## 1. Glosario de términos y clases

| Término | Dónde vive | Qué es |
|---|---|---|
| `AFD` | `automata.py` | Quíntupla M=(Q,Σ,δ,q0,F). `delta: dict[(estado,simbolo)] -> str` (un solo destino, o ausente si está incompleto). |
| `AFND` | `automata.py` | Misma quíntupla, pero `delta: dict[(estado,simbolo)] -> frozenset[str]` (0, 1 o varios destinos). |
| Macroestado | concepto, no una clase | Un subconjunto (`frozenset`) de estados del AFND. Cada macroestado alcanzado durante la conversión se convierte en UN estado del AFD generado. |
| Etiqueta | `conversor._siguiente_etiqueta` | Nombre legible que se le asigna a un macroestado, en el orden en que se descubre: A, B, C, ..., Z, AA, AB, ... |
| `tabla_equivalencias` | variable de sesión en `main.py`, la arma `conversor.construir_afd_desde_afnd` | `dict[etiqueta] -> frozenset` (el macroestado que esa etiqueta representa). Es lo que muestra la opción 8. |
| `automata_cargado` | variable de sesión en `main.main()` | El `AFD` o `AFND` recién creado/cargado con las opciones 1-4. Puede ser de cualquiera de las dos clases; se distingue con `isinstance`. |
| `afd_generado` | variable de sesión en `main.main()` | El `AFD` que resulta de convertir `automata_cargado` (opción 7). `None` mientras no se convierta. |
| `historial` | instancia de `Historial` (clase en `main.py`) | Registro de cadenas evaluadas contra el autómata activo. Se reinicia (instancia nueva) en las opciones 1-4 y 14. |
| `ResultadoEvaluacion` / `Paso` | dataclasses en `simulador.py` | Resultado de evaluar una cadena (`cadena`, `traza`, `veredicto`, `motivo`) y cada paso de la traza (`estado_origen`, `simbolo`, `estado_destino`). |
| `AnalisisEstructural` | dataclass en `validador.py` | `alcanzables`, `inaccesibles`, `finales_alcanzables`, `lenguaje_vacio` — resultado del análisis estructural (opción 13, y automático tras validar un AFD). |
| `obtener_afd_operable` | función en `main.py` | Devuelve el AFD sobre el que deben trabajar las opciones 10, 11 y 13: `automata_cargado` si ya es un AFD validado, o `afd_generado` si `automata_cargado` es un AFND ya convertido. |

---

## 2. Mapa rápido por opción del menú

**1. Crear un AFD manualmente**
- Módulo/función: `cargador.crear_afd_manual()` (usa `_pedir_conjunto`, `_pedir_conjunto_final`, `_pedir_transiciones`)
- Clases: `AFD`
- Datos de entrada: nombre; Q (lista); Σ (lista); q0; F (lista, puede ir vacía); transiciones `origen,simbolo,destino` repetidas hasta `FIN`
- Restricciones clave: nombre no vacío; Q/Σ sin vacíos ni duplicados; Σ sin épsilon; q0∈Q; F⊆Q; por transición: origen/destino∈Q, símbolo∈Σ, (origen,símbolo) sin repetir (repetir = "sería un AFND")

**2. Cargar un AFD desde archivo .txt**
- Módulo/función: `cargador.cargar_afd_desde_archivo(ruta)` (+ `normalizar_ruta_archivo`)
- Clases: `AFD`
- Datos de entrada: ruta del archivo
- Restricciones clave: cada línea debe calzar con un `PATRON_*` (ver sección 3); símbolo épsilon prohibido; (origen,símbolo) repetido = error; deben existir `NOMBRE`, `ESTADOS`, `ALFABETO`, `INICIAL`

**3. Crear un AFND manualmente**
- Módulo/función: `cargador_afnd.crear_afnd_manual()` (+ `_pedir_transiciones_afnd`; reutiliza `_pedir_conjunto`/`_pedir_conjunto_final` de `cargador.py`)
- Clases: `AFND`
- Datos de entrada: igual que la opción 1, pero la transición es `origen,simbolo,destino1|destino2|...` (usa `∅` o vacío para "sin destino")
- Restricciones clave: igual que la 1, salvo que un mismo (origen,símbolo) SÍ admite varios destinos, siempre que se declaren juntos separados por `|`; declarar el mismo par dos veces por separado es error

**4. Cargar un AFND desde archivo .txt**
- Módulo/función: `cargador_afnd.cargar_afnd_desde_archivo(ruta)`
- Clases: `AFND`
- Datos de entrada: ruta del archivo
- Restricciones clave: regex adaptada (`PATRON_TRANSICION_AFND`); línea `TIPO=` opcional (si no dice `AFND`, se agrega un aviso pero no bloquea); `∅`/vacío = sin destino; épsilon prohibido con mensaje "no forma parte del alcance de esta fase"

**5. Mostrar la definición formal y la tabla del autómata cargado**
- Módulo/función: `main.accion_mostrar_automata_cargado` → despacha por `isinstance` a `accion_mostrar_definicion`/`accion_mostrar_tabla` (AFD) o `accion_mostrar_definicion_afnd`/`accion_mostrar_tabla_afnd` (AFND)
- Clases: `AFD` o `AFND`
- Datos de entrada: ninguno (usa `automata_cargado`)
- Restricciones clave: requiere `automata_cargado is not None`

**6. Validar la estructura del autómata**
- Módulo/función: `main.accion_validar_automata_cargado` → `accion_validar_afd` (usa `validador.validar_estructura`, `validador.completar_con_estado_trampa`, `validador.analizar_estructura`) o `accion_validar_afnd` (usa `validador_afnd.validar_estructura_afnd`)
- Clases: `AFD`/`AFND`, `AnalisisEstructural`
- Datos de entrada: (solo caso AFD incompleto) respuesta S/N para agregar estado de trampa
- Restricciones clave — AFD: q0∈Q, F⊆Q, transiciones consistentes, completitud (o se completa con trampa). AFND: q0∈Q, F⊆Q, transiciones consistentes (destinos⊆Q); **no** existe el concepto de "incompleto"

**7. Convertir el AFND cargado en un AFD equivalente**
- Módulo/función: `main.accion_convertir` → `conversor.construir_afd_desde_afnd`
- Clases: `AFND` (entrada), `AFD` (salida), `tabla_equivalencias`
- Datos de entrada: ninguno directo
- Restricciones clave: `automata_cargado` debe ser `AFND` y estar `validado`; algoritmo de construcción de subconjuntos (ver sección 4)

**8. Mostrar la tabla de equivalencias de macroestados**
- Módulo/función: `main.accion_mostrar_equivalencias`
- Datos de entrada: ninguno
- Restricciones clave: requiere que ya exista `tabla_equivalencias` (opción 7 ejecutada con éxito)

**9. Mostrar la tabla de transición del AFD generado**
- Módulo/función: `main.accion_mostrar_tabla(afd_generado)` — la MISMA función que usa la opción 5 para un AFD
- Restricciones clave: requiere `afd_generado is not None`

**10. Evaluar una cadena**
- Módulo/función: `main.accion_evaluar_cadena` → `simulador.evaluar_cadena`, `simulador.imprimir_traza`
- Clases: `ResultadoEvaluacion`, `Paso`, `Historial`
- Datos de entrada: cadena (puede ser vacía = λ)
- Restricciones clave: requiere `obtener_afd_operable(...) is not None`

**11. Evaluar un archivo de cadenas**
- Módulo/función: `main.accion_evaluar_archivo` → `simulador.evaluar_lote`
- Datos de entrada: ruta del archivo (una cadena por línea)
- Restricciones clave: igual que la 10, aplicado a cada línea

**12. Consultar el historial de evaluaciones**
- Módulo/función: `Historial.mostrar()` (clase en `main.py`)
- Clases: `Historial`, `RegistroHistorial`
- Restricciones clave: ninguna (si está vacío, solo informa); se reinicia con las opciones 1-4 y 14

**13. Realizar el análisis estructural**
- Módulo/función: `main.imprimir_analisis_estructural` → `validador.analizar_estructura`
- Clases: `AnalisisEstructural`
- Restricciones clave: misma guardia que 10/11 (`obtener_afd_operable`)

**14. Cargar o crear otro autómata**
- Módulo/función: bucle principal de `main()`, rama `opcion == 14`
- Restricciones clave: ninguna; reinicia `automata_cargado`, `afd_generado`, `tabla_equivalencias` e `historial`

**15. Salir**
- Módulo/función: bucle principal de `main()`, `break`
- Restricciones clave: ninguna (ya se validó que la opción está entre 1 y 15)

---

## 3. Expresiones regulares por módulo

| Patrón | Módulo | Qué reconoce |
|---|---|---|
| `PATRON_NOMBRE` | `cargador.py` / `cargador_afnd.py` | Línea `NOMBRE=...` |
| `PATRON_TIPO` | `cargador_afnd.py` | Línea opcional `TIPO=...` (se avisa si no dice `AFND`) |
| `PATRON_ESTADOS` | ambos | Línea `ESTADOS=...` |
| `PATRON_ALFABETO` | ambos | Línea `ALFABETO=...` |
| `PATRON_INICIAL` | ambos | Línea `INICIAL=...` |
| `PATRON_FINALES` | ambos | Línea `FINALES=...` (puede ir vacía) |
| `PATRON_ENCABEZADO_TRANSICIONES` | ambos | La línea literal `TRANSICIONES:` |
| `PATRON_TRANSICION` | `cargador.py` | `origen,simbolo,destino` — un solo destino (AFD) |
| `PATRON_TRANSICION_AFND` | `cargador_afnd.py` | `origen,simbolo,destino...` — destino es todo el resto de la línea, luego se separa por `\|` |
| `PATRON_IDENTIFICADOR` | `cargador.py` (importado por `cargador_afnd.py`) | Nombre de estado válido: `[A-Za-z0-9_]+` |

---

## 4. El algoritmo de construcción de subconjuntos, en una tabla (para no repetirlo mal)

Implementado en `conversor.construir_afd_desde_afnd`:

| Paso | Qué hace | Línea/idea clave del código |
|---|---|---|
| 1 | Macroestado inicial | `frozenset({afnd.q0})` |
| 2 | Cola de pendientes | `deque([macroestado_inicial])`, se procesa con `popleft()` (BFS) |
| 3 | Para cada macroestado y cada símbolo | `destino = union de afnd.delta.get((estado,simbolo), frozenset()) para cada estado del macroestado actual` |
| 4 | ¿Macroestado nuevo? | Si `destino` no está en `etiquetas`, se le asigna la siguiente etiqueta y se encola |
| 5 | Se registra la transición del AFD | `delta_afd[(etiqueta_actual, simbolo)] = etiqueta_destino` |
| 6 | Termina cuando la cola queda vacía | Ahí ya se descubrieron todos los macroestados alcanzables |
| 7 | Estados finales del AFD | Un macroestado es final si `macroestado & afnd.F` no es vacío |
| 8 | Resultado | Un `AFD` normal (`validado = True` porque por construcción es completo y determinista) + `tabla_equivalencias` |

El conjunto vacío `∅` no necesita tratamiento especial: si `destino` es `frozenset()`, se etiqueta como cualquier otro macroestado, y como la unión de transiciones de ningún estado siempre da `∅`, sus propias transiciones regresan a sí mismo — por eso actúa como estado de trampa automáticamente.
