"""
automata.py
-----------
Define las estructuras de datos que representan los autómatas del proyecto:

  - AFD  (Fase 1): Autómata Finito Determinista.
  añadimos las partes del proyecto 2
  - AFND (Fase 2): Autómata Finito No Determinista.

Ambos comparten la misma quíntupla formal:

    M = (Q, Sigma, delta, q0, F)

La diferencia está únicamente en delta: en el AFD cada par (estado, símbolo)
tiene UN destino (o ninguno, si está incompleto); en el AFND cada par tiene
UN CONJUNTO de destinos (que puede tener cero, uno o varios elementos).

No se utiliza ninguna biblioteca que implemente autómatas: la quíntupla se
modela únicamente con tipos nativos de Python (set, frozenset y dict), tal
como exige el enunciado del proyecto.
"""


class AFD:
    """
    Representa la quíntupla M = (Q, Sigma, delta, q0, F).

    Atributos
    ---------
    nombre : str
        Identificador legible del autómata.
    Q : set[str]
        Conjunto de estados.
    sigma : set[str]
        Alfabeto (conjunto de símbolos).
    delta : dict[(str, str), str]
        Función de transición. La clave es la tupla (estado, símbolo) y el
        valor es el estado destino. Al representarse como diccionario,
        evaluar delta[(estado, simbolo)] reemplaza cualquier cadena de
        if/else o switch: la transición es completamente genérica y sirve
        para cualquier AFD, no solo para uno en particular.
    q0 : str
        Estado inicial.
    F : set[str]
        Conjunto de estados de aceptación.
    validado : bool
        True únicamente después de que el AFD pasó el motor de validación
        (Funcionalidad 2) sin errores y sin transiciones faltantes.
    """

    def __init__(self, nombre, Q, sigma, delta, q0, F):
        self.nombre = nombre
        self.Q = set(Q)
        self.sigma = set(sigma)
        self.delta = dict(delta)
        self.q0 = q0
        self.F = set(F)
        self.validado = False

    def transicion(self, estado, simbolo):
        """
        Aplica la función de transición delta(estado, simbolo).
        Devuelve el estado destino, o None si no existe una transición
        definida para ese par (indica un AFD incompleto).
        """
        return self.delta.get((estado, simbolo))

    def __str__(self):
        return (
            f"AFD '{self.nombre}' — {len(self.Q)} estado(s), "
            f"alfabeto {sorted(self.sigma)}"
        )


class AFND:
    """
    Representa la quíntupla M = (Q, Sigma, delta, q0, F) de un Autómata
    Finito No Determinista (Fase 2).
    En este caso se cambio para que fuera mas sensillo inge ademas como tiene diferentes partes
    es necesario cambiarlo

    Atributos
    ---------
    nombre : str
        Identificador legible del autómata.
    Q : set[str]
        Conjunto de estados.
    sigma : set[str]
        Alfabeto (conjunto de símbolos).
    delta : dict[(str, str), frozenset[str]]
        Función de transición. La clave es la tupla (estado, símbolo) y el
        valor es el CONJUNTO de estados destino (puede tener 0, 1 o varios
        elementos). Igual que en el AFD, delta es un diccionario genérico:
        no hay ninguna cadena de if/elif por autómata específico.
    q0 : str
        Estado inicial.
    F : set[str]
        Conjunto de estados de aceptación.
    validado : bool
        True únicamente después de que el AFND pasó el motor de validación
        (validador_afnd.py) sin errores.
    """

    def __init__(self, nombre, Q, sigma, delta, q0, F):
        self.nombre = nombre
        self.Q = set(Q)
        self.sigma = set(sigma)
        # Se normaliza cada valor a frozenset para dejar claro que un
        # destino de un AFND es un conjunto (aunque contenga un solo
        # estado), tal como pide el enunciado.
        self.delta = {clave: frozenset(destinos) for clave, destinos in delta.items()}
        self.q0 = q0
        self.F = set(F)
        self.validado = False

    def transicion(self, estado, simbolo):
        """
        Aplica la función de transición delta(estado, simbolo).
        Devuelve el frozenset de estados destino. Un par (estado, símbolo)
        que no aparece explícitamente en delta se interpreta como una
        transición sin destinos (∅), no como un error: a diferencia del
        AFD, en un AFND esto es perfectamente válido.
        """
        return self.delta.get((estado, simbolo), frozenset())

    def __str__(self):
        return (
            f"AFND '{self.nombre}' — {len(self.Q)} estado(s), "
            f"alfabeto {sorted(self.sigma)}"
        )
