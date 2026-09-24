"""
automata.py
-----------
Define la estructura de datos que representa un Autómata Finito
Determinista (AFD) mediante su quíntupla formal:

    M = (Q, Sigma, delta, q0, F)

No se utiliza ninguna biblioteca que implemente autómatas: la quíntupla se
modela únicamente con tipos nativos de Python (set y dict), tal como exige
el enunciado del proyecto.
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
