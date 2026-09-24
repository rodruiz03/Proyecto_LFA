"""
colores.py
----------
Utilidades para imprimir texto con color en la consola, usando códigos de
escape ANSI implementados a mano (sin librerías externas como colorama,
ya que el enunciado prohíbe usar módulos de terceros para resolver parte
de la funcionalidad del proyecto).

En Windows, la consola clásica (cmd.exe) no interpreta las secuencias ANSI
por defecto: hay que activar el "Virtual Terminal Processing" del sistema
operativo. Esto se logra con el truco estándar `os.system("")`, que fuerza
a Windows a habilitar el procesamiento de estas secuencias sin necesidad de
ninguna biblioteca adicional. Se ejecuta una sola vez, al importar este
módulo.
"""

import os

os.system("")


class Color:
    """Códigos de escape ANSI usados en todo el programa."""
    RESET = "\033[0m"
    NEGRITA = "\033[1m"

    ROJO = "\033[91m"
    VERDE = "\033[92m"
    AMARILLO = "\033[93m"
    AZUL = "\033[94m"
    CIAN = "\033[96m"


def _pintar(texto, *codigos):
    """Envuelve `texto` con los códigos ANSI indicados y el reset final."""
    return "".join(codigos) + str(texto) + Color.RESET


def exito(texto):
    """Verde: usado para mensajes de éxito y veredicto 'Aceptada'."""
    return _pintar(texto, Color.VERDE)


def error(texto):
    """Rojo: usado para errores y veredicto 'Rechazada'."""
    return _pintar(texto, Color.ROJO)


def advertencia(texto):
    """Amarillo: usado para advertencias (por ejemplo, AFD incompleto)."""
    return _pintar(texto, Color.AMARILLO)


def info(texto):
    """Cian: usado para mensajes informativos generales."""
    return _pintar(texto, Color.CIAN)


def titulo(texto):
    """Azul y negrita: usado para encabezados y títulos de sección."""
    return _pintar(texto, Color.NEGRITA, Color.AZUL)
