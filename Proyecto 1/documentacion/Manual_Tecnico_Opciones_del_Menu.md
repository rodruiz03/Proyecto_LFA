# Manual Técnico — Detalle de las 10 opciones del menú

> Este documento continúa el `MANUAL TECNICO.docx` justo donde quedó cortado
> ("...la opción 1 pedirá las siguientes entradas"). Para cada una de las 10
> opciones se detalla: **Acciones**, **Datos de entrada**, **Variables** y
> **Condiciones y cálculos**, tal como lo pide el formato del manual. Basado
> en el código real de `codigo/main.py`, `cargador.py`, `validador.py` y
> `simulador.py`.

---

## Opción 1 — Crear un AFD manualmente

**Módulo/función:** `cargador.crear_afd_manual()`, invocada desde `main.accion_crear_manual()`.

### Acciones
1. Solicita el nombre del autómata (no vacío; reintenta hasta que sea válido).
2. Solicita el conjunto de estados Q (lista separada por comas); rechaza conjunto vacío o con duplicados.
3. Solicita el alfabeto Σ (lista separada por comas); rechaza vacío, duplicados o que contenga el símbolo épsilon.
4. Solicita el estado inicial q0; reintenta hasta que pertenezca a Q.
5. Solicita el conjunto de estados finales F (puede quedar vacío); rechaza duplicados o que no sea subconjunto de Q.
6. Solicita transiciones una por una (`origen,simbolo,destino`) hasta que el usuario escribe `FIN`; rechaza en el acto estados/símbolos fuera de Q/Σ, el símbolo épsilon, y transiciones repetidas para el mismo par (origen, símbolo).
7. Construye el objeto `AFD` con `validado=False` y lo devuelve; queda como el autómata actual de la sesión.

### Datos de entrada
| Dato | Tipo | Formato / restricción |
|---|---|---|
| Nombre del autómata | `str` | No vacío |
| Estados Q | `str` (lista por comas) | Se convierte a `set`; sin vacíos ni duplicados |
| Alfabeto Σ | `str` (lista por comas) | Se convierte a `set`; sin duplicados; prohíbe `ε`/`epsilon` |
| Estado inicial q0 | `str` | Debe pertenecer a Q |
| Estados finales F | `str` (lista por comas, puede ser `""`) | Se convierte a `set`; debe ser subconjunto de Q |
| Transiciones | `str` `"origen,simbolo,destino"`, repetido hasta `"FIN"` | origen/destino ∈ Q, símbolo ∈ Σ, sin repetir (origen, símbolo) |

### Variables
- `nombre: str`, `Q: set[str]`, `sigma: set[str]`, `q0: str`, `F: set[str]`
- `delta: dict[(str, str), str]` — se construye en `_pedir_transiciones`
- `elementos: list[str]` — temporal, resultado de `_separar_lista()`
- `entrada, partes, origen, simbolo, destino: str` — temporales por cada transición ingresada
- `afd: AFD` — objeto final devuelto

### Condiciones y cálculos
- Sin duplicados: `len(elementos) == len(set(elementos))`, aplicado a Q, Σ y F.
- Épsilon prohibido: se rechaza si algún elemento de Σ (o el símbolo de una transición) está en `{'ε','epsilon','Epsilon','EPSILON','ÉPSILON'}`.
- `q0 ∈ Q` (se vuelve a pedir hasta cumplirse).
- `F ⊆ Q` → `F.issubset(Q)`.
- Por transición: `origen ∈ Q`, `destino ∈ Q`, `simbolo ∈ Σ`.
- Unicidad de δ: `(origen, simbolo) not in delta` antes de agregar — evita que el autómata se vuelva un AFND.
- δ se construye como diccionario (`delta[(origen, simbolo)] = destino`), nunca como una cadena de `if/elif` por estado.

---

## Opción 2 — Cargar un AFD desde archivo .txt

**Módulo/función:** `cargador.cargar_afd_desde_archivo(ruta)`, invocada desde `main.accion_cargar_archivo()`.

### Acciones
1. Solicita la ruta del archivo `.txt`.
2. Normaliza la ruta (`normalizar_ruta_archivo`): quita comillas envolventes, expande variables de entorno y `~`, unifica separadores.
3. Intenta abrir y leer todas las líneas; si falla (`FileNotFoundError`/`OSError`), reporta el error y regresa sin construir el AFD.
4. Recorre línea por línea, reconociendo cada una con expresiones regulares (`NOMBRE=`, `ESTADOS=`, `ALFABETO=`, `INICIAL=`, `FINALES=`, `TRANSICIONES:`, y luego cada línea de transición `origen,simbolo,destino`).
5. Acumula un error de sintaxis (con número de línea) por cada línea que no coincide con ningún patrón, **sin detener la lectura**.
6. Detecta y rechaza transiciones con símbolo épsilon y transiciones múltiples para el mismo par (origen, símbolo) — indicio de AFND.
7. Verifica que estén presentes los componentes obligatorios (`NOMBRE`, `ESTADOS`, `ALFABETO`, `INICIAL`); si falta alguno, no construye el AFD.
8. Si los componentes mínimos están presentes, construye el objeto `AFD` (`validado=False`) y lo devuelve junto con la lista de errores encontrados (puede no estar vacía aunque el AFD sí se haya construido).

### Datos de entrada
| Dato | Tipo | Formato |
|---|---|---|
| Ruta del archivo | `str` | Debe apuntar a un archivo `.txt` existente y legible, con el formato `NOMBRE=` / `ESTADOS=` / `ALFABETO=` / `INICIAL=` / `FINALES=` / `TRANSICIONES:` |

### Variables
- `ruta: str`, `lineas: list[str]`, `errores: list[str]`, `numero_linea: int`
- `nombre: str | None`, `Q: set[str] | None`, `sigma: set[str] | None`, `q0: str | None`, `F: set[str]`, `delta: dict[(str,str), str]`
- `dentro_de_transiciones: bool` — indica si ya se pasó la línea `TRANSICIONES:`
- `transiciones_vistas: set[(str,str)]` — detecta pares repetidos
- `PATRON_NOMBRE, PATRON_ESTADOS, PATRON_ALFABETO, PATRON_INICIAL, PATRON_FINALES, PATRON_ENCABEZADO_TRANSICIONES, PATRON_TRANSICION, PATRON_IDENTIFICADOR: re.Pattern` — constantes del módulo

### Condiciones y cálculos
- Cada línea se contrasta, en orden, contra los patrones regex hasta encontrar coincidencia; si ninguno coincide → error `"línea N: no coincide con ningún patrón reconocido"`.
- `ESTADOS`/`ALFABETO`/`FINALES`: se separan por comas, se valida duplicados (`len(lista)==len(set(lista))`) y nombres válidos (`^[A-Za-z0-9_]+$`).
- Épsilon prohibido: se filtra de Σ y se rechaza como símbolo de transición.
- Transición: `(origen,simbolo) not in transiciones_vistas` antes de agregar a δ; si ya existe, se reporta `"transición múltiple -> AFND"` y se descarta esa línea.
- Construcción final: solo si `nombre`, `Q`, `sigma` y `q0` son distintos de `None` (F puede quedar vacío por defecto).

---

## Opción 3 — Mostrar la definición formal del AFD

**Función:** `main.accion_mostrar_definicion(afd)`.

### Acciones
1. Verifica que haya un autómata cargado (`hay_automata_cargado`); si no, muestra error y regresa al menú.
2. Imprime la quíntupla `M = (Q, Σ, δ, q0, F)` del autómata actual: Q, Σ y F ordenados alfabéticamente; q0; y cada transición `δ(estado, símbolo) = destino` ordenada.

### Datos de entrada
Ninguno — usa el autómata ya cargado en memoria.

### Variables
- `afd: AFD` (el autómata actual)
- `estado, simbolo, destino: str` — usados al iterar `sorted(afd.delta.items())`

### Condiciones y cálculos
- Requiere `automata_actual != None`.
- Q, Σ, F se muestran con `sorted()` (un `set` de Python no garantiza orden).
- δ se recorre como `sorted(afd.delta.items())`, es decir, ordenado por la clave (estado, símbolo).

---

## Opción 4 — Mostrar la tabla de transición

**Función:** `main.accion_mostrar_tabla(afd)`.

### Acciones
1. Verifica que haya un autómata cargado.
2. Calcula el ancho de columna necesario según el nombre de estado más largo.
3. Imprime un encabezado con cada símbolo del alfabeto como columna.
4. Imprime una fila por cada estado (marcando `->` si es el inicial y `*` si es final), con el destino `δ(estado, símbolo)` en cada columna, o `-` si no está definida.

### Datos de entrada
Ninguno.

### Variables
- `estados: list[str]` — `sorted(afd.Q)`
- `simbolos: list[str]` — `sorted(afd.sigma)`
- `ancho_estado: int`, `encabezado: str`, `fila: str`, `etiqueta: str`, `marcas: str`
- `destino: str` — `afd.delta.get((estado, simbolo), "-")`

### Condiciones y cálculos
- Requiere `automata_actual != None`.
- `ancho_estado = max(len(e) for e in estados + ["Estado"]) + 3`.
- Por cada estado: `marcas = "->"` si `estado == q0`, más `"*"` si `estado ∈ F`.
- `destino = afd.delta.get((estado, simbolo), "-")` — mismo mecanismo genérico de δ que usa la simulación, sin condicionales por estado.

---

## Opción 5 — Validar la estructura del autómata

**Funciones:** `main.accion_validar(afd)` + `validador.validar_estructura`, `validador.analizar_estructura`, `validador.completar_con_estado_trampa`.

### Acciones
1. Verifica que haya un autómata cargado.
2. Ejecuta el motor de validación (`validar_estructura`): revisa `q0 ∈ Q`, `F ⊆ Q`, consistencia de cada transición, y calcula los pares (estado, símbolo) sin transición definida (`incompletas`).
3. Si hay errores estructurales graves, los muestra todos, marca `validado=False` y no continúa.
4. Si el AFD está incompleto (sin errores graves pero con pares faltantes), muestra la lista de transiciones faltantes y pregunta si se desea completar con un estado de trampa.
   - Si el usuario responde `S`: crea el estado de trampa (con nombre único, ej. `q_trampa`, `q_trampa_2`...), agrega `δ[(estado,símbolo)] = q_trampa` para cada par faltante y `δ[(q_trampa,símbolo)] = q_trampa` para cada símbolo (auto-transición); vuelve a validar.
   - Si responde cualquier otra cosa: deja `validado=False` y no continúa.
5. Si no hay errores ni pares faltantes (desde el inicio o tras completar la trampa): marca `validado=True` y ejecuta el análisis estructural (`analizar_estructura`): estados alcanzables desde q0 (recorrido sobre δ), inaccesibles (`Q - alcanzables`), finales alcanzables (`F ∩ alcanzables`) y si el lenguaje podría ser vacío.

### Datos de entrada
| Dato | Tipo | Formato |
|---|---|---|
| Confirmación de estado de trampa | `str` (`S`/`N`) | Solo se solicita si el AFD resultó incompleto |

### Variables
- `errores: list[str]`, `incompletas: list[(str,str)]`
- `respuesta: str`, `nombre_trampa: str`, `sufijo: int`
- `analisis: AnalisisEstructural` — `alcanzables: set`, `inaccesibles: set`, `finales_alcanzables: set`, `lenguaje_vacio: bool`
- `alcanzables: set[str]`, `pendientes: list[str]` — pila del recorrido

### Condiciones y cálculos
- `q0 ∈ Q`; si no, error.
- `F ⊆ Q` (`F - Q` debe ser ∅); si no, error listando los elementos que faltan.
- Por cada `(origen,simbolo) → destino` en δ: `origen ∈ Q`, `simbolo ∈ Σ`, `destino ∈ Q`; cualquier incumplimiento es error.
- `incompletas = [(estado,simbolo) para estado∈Q, simbolo∈Σ si (estado,simbolo) not in δ]` — verificación de determinismo/completitud (Funcionalidad 2, punto 3).
- Estado de trampa: `nombre_trampa = "q_trampa"`; si ya existe en Q, se prueba `"q_trampa_2"`, `"q_trampa_3"`... hasta que sea único. La trampa nunca se agrega a F.
- `alcanzables`: recorrido desde q0 siguiendo δ para cada símbolo de Σ, acumulando todo estado visitado.
- `inaccesibles = Q - alcanzables`.
- `finales_alcanzables = F ∩ alcanzables`.
- `lenguaje_vacio = (len(finales_alcanzables) == 0)`.

---

## Opción 6 — Evaluar una cadena

**Funciones:** `main.accion_evaluar_cadena` + `simulador.evaluar_cadena`, `simulador.imprimir_traza`.

### Acciones
1. Verifica que haya un autómata cargado **y validado** (`puede_evaluar`).
2. Solicita la cadena a evaluar (puede dejarse vacía = λ).
3. Simula: para cada símbolo, en orden, si no pertenece a Σ o si δ no está definida para `(estado_actual, símbolo)`, detiene el proceso y marca "Rechazada" con el motivo; si no, avanza `estado_actual` y registra el paso en la traza.
4. Si se procesaron todos los símbolos sin error, determina el veredicto según si `estado_actual ∈ F`.
5. Imprime la traza paso a paso (`δ(origen,símbolo)=destino`) y el veredicto en color (verde = Aceptada, rojo = Rechazada).
6. Agrega el resultado al historial de la sesión.

### Datos de entrada
| Dato | Tipo | Formato |
|---|---|---|
| Cadena a evaluar | `str` | Puede ser vacía (λ); si contiene un símbolo fuera de Σ, se acepta el ingreso pero se rechaza con motivo explicado |

### Variables
- `cadena: str`, `estado_actual: str`
- `traza: list[Paso]` — cada `Paso`: `estado_origen`, `simbolo`, `estado_destino`
- `resultado: ResultadoEvaluacion` — `cadena`, `traza`, `veredicto`, `motivo`
- `simbolo, siguiente: str` — temporales del bucle

### Condiciones y cálculos
- Requiere `automata_actual != None` y `automata_actual.validado == True`.
- `estado_actual ← q0` al inicio.
- Por cada símbolo `sᵢ` de la cadena, en orden: si `sᵢ ∉ Σ` → Rechazada (motivo: símbolo inválido); si `δ(estado_actual, sᵢ)` no existe → Rechazada (motivo: transición no definida); si no, `estado_actual ← δ(estado_actual, sᵢ)` y se agrega el paso a la traza.
- Si no hubo error: `veredicto = "Aceptada"` si `estado_actual ∈ F`, si no `"Rechazada"`.
- Cadena vacía (`w = λ`): no se procesa ningún símbolo; el veredicto depende únicamente de si `q0 ∈ F`.

---

## Opción 7 — Evaluar un archivo de cadenas

**Funciones:** `main.accion_evaluar_archivo` + `simulador.evaluar_lote`.

### Acciones
1. Verifica que haya un autómata cargado y validado.
2. Solicita la ruta del archivo de cadenas (una por línea).
3. Intenta abrir y leer todas las líneas; si falla, reporta el error y regresa al menú sin colapsar.
4. Evalúa cada línea con el mismo algoritmo de la opción 6 (`evaluar_cadena`), acumulando resultados.
5. Imprime la traza y el veredicto de cada cadena, y las agrega todas al historial.
6. Imprime un resumen: total evaluadas, aceptadas y rechazadas.

### Datos de entrada
| Dato | Tipo | Formato |
|---|---|---|
| Ruta del archivo de cadenas | `str` | Archivo de texto con una cadena por línea (una línea vacía = λ) |

### Variables
- `ruta: str`, `cadenas: list[str]`
- `resultados: list[ResultadoEvaluacion]`
- `resumen: dict` — `{"total": int, "aceptadas": int, "rechazadas": int}`
- `total_aceptadas, total_rechazadas: int` — acumuladores internos de `evaluar_lote`

### Condiciones y cálculos
- Requiere `automata_actual != None` y `validado == True`.
- Lectura protegida con `try/except FileNotFoundError/OSError`.
- Por cada cadena de la lista: se aplica el algoritmo de la opción 6; `total += 1`; `aceptadas += 1` si `veredicto == "Aceptada"`, si no `rechazadas += 1`.

---

## Opción 8 — Consultar el historial de evaluaciones

**Función:** `Historial.mostrar()` (clase definida en `main.py`).

### Acciones
1. Si no se ha evaluado ninguna cadena en la sesión, muestra un mensaje informativo.
2. Si hay registros, lista cada uno numerado, mostrando el autómata usado, la cadena (o `"λ (cadena vacía)"`) y el veredicto en color.

### Datos de entrada
Ninguno.

### Variables
- `historial: Historial` — envuelve `_registros: list[RegistroHistorial]`
- `RegistroHistorial`: `cadena: str`, `veredicto: str`, `traza: list[Paso]`, `automata: str`
- `i, registro` — variables de iteración (`enumerate`)
- `cadena_mostrar, resultado_coloreado: str` — temporales de formato

### Condiciones y cálculos
- No requiere `automata_actual` cargado — el historial es independiente del AFD activo en ese momento.
- Persiste aunque se descarte o cambie el autómata (opción 9): solo se reinicia al cerrar el programa.
- `cadena_mostrar = "λ (cadena vacía)"` si `registro.cadena == ""`, si no el texto tal cual.

---

## Opción 9 — Cargar o crear otro autómata

**Ubicación:** bucle principal de `main()`.

### Acciones
1. Descarta el autómata actual (`afd ← None`).
2. Muestra un mensaje confirmando que fue descartado.
3. Regresa al menú, donde las opciones 3-7 vuelven a bloquearse hasta usar 1 o 2 de nuevo.

### Datos de entrada
Ninguno.

### Variables
- `afd` — se reasigna a `None` en el bucle principal de `main()`.

### Condiciones y cálculos
- `afd ← None`.
- El historial **no** se modifica (sigue acumulando entradas de autómatas distintos, cada una etiquetada con el nombre del AFD que se usó).

---

## Opción 10 — Salir

**Ubicación:** bucle principal de `main()`.

### Acciones
1. Imprime un mensaje de despedida (`"¡Hasta luego!"`).
2. Rompe el bucle principal (`while True`) y el programa termina de forma controlada.

### Datos de entrada
Ninguno.

### Variables
Ninguna nueva — solo se sale del bucle (`break`).

### Condiciones y cálculos
Ninguna condición adicional: la opción ya fue validada como un entero entre 1 y 10 por `pedir_opcion()` antes de llegar aquí; como las opciones 1-9 ya se descartaron en el `if/elif`, 10 es la única posibilidad restante.
