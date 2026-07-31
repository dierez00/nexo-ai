"""Búsqueda léxica BM25 (`DIE-F1-020`).

La mitad léxica existe porque las consultas ciudadanas mezclan paráfrasis
(«quiero poner una taquería») con términos que deben coincidir literalmente
(«uso de suelo», «licencia tipo A»). La similitud semántica falla en los
segundos: un modelo pone cerca «licencia tipo A» y «licencia tipo C», que es
exactamente la confusión que no podemos permitirnos en un trámite.

BM25 es el estándar de facto y es lo que implementará `ts_rank_cd` sobre el FTS
de PostgreSQL. Se implementa aquí con los mismos parámetros para que el doble en
memoria y el repositorio real ordenen igual, no solo parecido.

Normalización: minúsculas, sin acentos y sin palabras vacías del español. Sin
quitar acentos, «renovacion» y «renovación» serían términos distintos, y la
gente escribe las dos.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

# Parámetros canónicos de BM25. `k1` gradúa la saturación por frecuencia y `b`
# cuánto penaliza la longitud del documento.
K1 = 1.2
B = 0.75

_TOKEN = re.compile(r"[a-z0-9]+")

# Palabras vacías del español que aparecen en casi todo fragmento y solo añaden
# ruido al puntaje. La lista es corta a propósito: quitar demasiado borra
# términos que sí discriminan.
STOPWORDS = frozenset(
    """
    a al algo alguna algunas alguno algunos ante antes como con contra cual
    cuando de del desde donde dos el ella ellas ellos en entre era eran es esa
    esas ese eso esos esta estan estas este esto estos ha hasta hay la las le
    les lo los mas me mi mis mucho muy no nos o os otra otras otro otros para
    pero por porque que quien se sea ser si sin sobre solo son su sus tambien
    tanto te tiene tienen todo todos tu tus un una uno unos y ya
    """.split()
)


def normalize(text: str) -> str:
    """Minúsculas sin acentos. Es la misma normalización que aplicará el FTS."""
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


# Sufijos del español, ordenados de más largo a más corto: hay que quitar
# «aciones» antes que «es», o quedaría «acion» y nunca llegaría a la raíz.
#
# Van **sin acentos** porque `normalize` ya los quitó antes de tokenizar.
_SUFFIXES = (
    "amientos",
    "imientos",
    "amiento",
    "imiento",
    "aciones",
    "uciones",
    "iciones",
    "adores",
    "adora",
    "acion",
    "ucion",
    "icion",
    "ancia",
    "encia",
    "mente",
    "idades",
    "idad",
    "ador",
    "ante",
    "ivos",
    "ivas",
    "ivo",
    "iva",
    "oso",
    "osa",
)

# Longitud mínima de la raíz resultante. Protege las palabras cortas: sin ella
# «uso» quedaría en «us» y «gas» en «ga».
_MIN_STEM = 3

# Vocales finales átonas que el recorte residual elimina. La `i` y la `u` no
# entran: casi nunca son terminación flexiva y quitarlas destruye palabras.
_FINAL_VOWELS = frozenset("aeo")


def _strip_plural(token: str) -> str:
    """Quita la marca de plural del español.

    Deshacerla es ambiguo sin un diccionario: «trámites» y «oficiales» terminan
    igual y sus singulares son «trámite» y «oficial». Ninguna regla local
    distingue los dos casos, así que se quita «es» siempre y el recorte de la
    vocal final se encarga de que ambas formas converjan de todos modos.
    """
    if token.endswith("es") and len(token) - 2 >= _MIN_STEM:
        return token[:-2]
    if token.endswith("s") and len(token) - 1 >= _MIN_STEM:
        return token[:-1]
    return token


def stem(token: str) -> str:
    """Raíz aproximada de una palabra en español.

    Es un *light stemmer* de recorte de sufijos, no un Snowball completo. Existe
    por dos motivos, en este orden:

    1. **Correspondencia con el motor real.** El FTS de PostgreSQL con la
       configuración `spanish` lematiza. Un índice en memoria que no lo hiciera
       ordenaría distinto que el repositorio final, y una prueba que pasa aquí
       dejaría de significar algo allí.
    2. **Recuperación honesta.** «trámites» y «trámite», «resoluciones» y
       «resolución» son la misma palabra para quien pregunta.

    El recorte es conservador: ante la duda, no recorta. Un stemmer agresivo une
    palabras que no significan lo mismo, y en un trámite eso es peor que fallar
    una coincidencia.

    Los tres pasos van en este orden y el orden importa:

    1. **Plural.** Primero, para que la lista de sufijos no necesite duplicarse
       en singular y plural. Al revés, «licencia» caería en el sufijo «encia» y
       «licencias» no, y las dos formas divergirían.
    2. **Sufijo derivativo.** «resolución» y «resoluciones» → `resol`.
    3. **Vocal final átona.** Es lo que hace converger «trámite» y «trámites»
       pese a que el paso 1 no puede decidir cuál de los dos plurales era.
    """
    token = _strip_plural(token)

    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= _MIN_STEM:
            return token[: -len(suffix)]

    if token and token[-1] in _FINAL_VOWELS and len(token) - 1 >= _MIN_STEM:
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    """Tokens significativos y lematizados, en orden.

    Conserva repeticiones: la frecuencia del término es la mitad de BM25.
    """
    return [stem(token) for token in _TOKEN.findall(normalize(text)) if token not in STOPWORDS]


@dataclass
class BM25Index:
    """Índice léxico en memoria sobre una colección de documentos.

    Se construye por consulta a partir de los candidatos ya filtrados. Para el
    corpus del MVP —decenas de fragmentos— eso es irrelevante en costo y evita
    mantener un índice invalidable. Con el corpus real, `ts_rank_cd` de
    PostgreSQL ocupa este lugar.
    """

    documents: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._frequencies: dict[str, Counter[str]] = {
            key: Counter(tokens) for key, tokens in self.documents.items()
        }
        self._lengths = {key: len(tokens) for key, tokens in self.documents.items()}
        total = sum(self._lengths.values())
        self._average_length = total / len(self._lengths) if self._lengths else 0.0
        self._document_frequency: Counter[str] = Counter()
        for tokens in self.documents.values():
            self._document_frequency.update(set(tokens))

    @classmethod
    def from_texts(cls, texts: dict[str, str]) -> BM25Index:
        return cls(documents={key: tokenize(text) for key, text in texts.items()})

    def _idf(self, term: str) -> float:
        """IDF de BM25 con corrección `+0.5`, acotado a valores no negativos.

        Sin el acotado, un término presente en más de la mitad de la colección
        recibe IDF negativo y contenerlo *baja* el puntaje, que es un
        comportamiento imposible de explicar a quien lea una traza.
        """
        total = len(self.documents)
        if total == 0:
            return 0.0
        appearances = self._document_frequency.get(term, 0)
        return max(0.0, math.log(1 + (total - appearances + 0.5) / (appearances + 0.5)))

    def _achievable(self, terms: list[str]) -> float:
        """Puntaje máximo que un documento podría alcanzar para esta consulta.

        Es el límite de BM25 cuando la frecuencia del término tiende a infinito:
        `Σ idf(t) · (k1 + 1)`. Sirve como denominador de la normalización.
        """
        return sum(self._idf(term) * (K1 + 1) for term in set(terms))

    def score(self, query: str) -> dict[str, float]:
        """Relevancia léxica en `[0, 1]`, comparable entre consultas.

        La normalización es contra el **máximo alcanzable** de la consulta, no
        contra el mejor resultado obtenido. La diferencia es lo que hace que un
        umbral signifique algo: dividiendo por el máximo obtenido, el primer
        resultado vale 1.0 siempre —incluso cuando la consulta no tiene nada que
        ver con el corpus— y ningún umbral puede distinguir «esto responde» de
        «esto es lo menos malo que hay».

        Así el valor dice «qué fracción de la relevancia posible capturó este
        fragmento», que es comparable entre consultas y entre commits.
        """
        terms = tokenize(query)
        if not terms or not self.documents:
            return {}
        achievable = self._achievable(terms)
        if achievable <= 0:
            return {}

        scores: dict[str, float] = {}
        for key, frequencies in self._frequencies.items():
            length = self._lengths[key]
            total = 0.0
            for term in terms:
                occurrences = frequencies.get(term, 0)
                if occurrences == 0:
                    continue
                denominator = occurrences + K1 * (
                    1 - B + B * (length / self._average_length if self._average_length else 1)
                )
                total += self._idf(term) * (occurrences * (K1 + 1)) / denominator
            if total > 0:
                scores[key] = min(1.0, total / achievable)
        return scores
