"""Adapter de embeddings semánticos locales (`DIE-F1-017`).

El doble determinista de Fase 0 deriva vectores de un hash: sirve para verificar
que el pipeline registra modelo y dimensión, pero **no tiene semántica**, así
que medir recall con él produce un número sin significado (TD-02). El baseline
de calidad de `DIE-F1-029` exige embeddings de verdad.

Se usa `model2vec` con un modelo estático multilingüe. La elección responde a
tres restricciones simultáneas:

- **español**, porque el corpus lo está;
- **sin `torch`**, que añadiría ~2.5 GB a un repositorio donde el resto de
  dependencias suma decenas de megas;
- **determinista**, porque los baselines se comparan entre commits y un modelo
  con muestreo los haría ruido.

Un modelo estático (una tabla de vectores por token, promediada) es menos
preciso que un transformer, y es una limitación consciente: da relaciones
semánticas reales sin arrastrar un runtime de inferencia.

**Este adapter no forma parte del perfil offline.** La primera carga descarga el
modelo, así que el default de la suite y de la demo sigue siendo
`DeterministicEmbeddings`; las pruebas que lo usan llevan el marcador
`integration` y quedan fuera de la ejecución por defecto.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - solo para tipos
    from model2vec import StaticModel
    from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = "minishlab/potion-multilingual-128M"
DEFAULT_DIMENSION = 256

# Modelo transformer multilingüe. E5 se eligió por su calidad en recuperación
# asimétrica (consulta corta contra pasaje largo), que es exactamente la forma
# de nuestras consultas.
TRANSFORMER_MODEL = "intfloat/multilingual-e5-base"

_TRANSFORMER_HINT = (
    "el adapter de transformers requiere `sentence-transformers`. Instálalo con "
    "`pip install 'nexo-rag[transformer]'`. La suite y la demo offline no lo "
    "necesitan: usan DeterministicEmbeddings."
)

_INSTALL_HINT = (
    "el adapter de embeddings semánticos requiere `model2vec`. Instálalo con "
    "`pip install 'nexo-rag[semantic]'`. La suite y la demo offline no lo "
    "necesitan: usan DeterministicEmbeddings."
)


class StaticSemanticEmbeddings:
    """Implementación de `EmbeddingsPort` sobre un modelo estático local.

    La carga es perezosa: construir el objeto no descarga nada, de modo que
    importar este módulo en un entorno sin red no rompe nada.
    """

    def __init__(self, *, model_id: str = DEFAULT_MODEL) -> None:
        self._model_id = model_id
        self._model: StaticModel | None = None

    @property
    def model_name(self) -> str:
        """Nombre completo, registrado junto a cada chunk indexado.

        Incluye el proveedor de la implementación además del modelo: reindexar
        con otro backend sobre el mismo modelo debe ser detectable.
        """
        return f"model2vec:{self._model_id}"

    @property
    def dimension(self) -> int:
        return int(self._load().dim)

    @property
    def is_semantic(self) -> bool:
        """Verdadero: el retriever puede usar la mitad vectorial de la fusión."""
        return True

    def _load(self) -> StaticModel:
        if self._model is None:
            try:
                from model2vec import StaticModel
            except ImportError as exc:  # pragma: no cover - depende del entorno
                raise RuntimeError(_INSTALL_HINT) from exc
            self._model = StaticModel.from_pretrained(self._model_id)
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Vectores normalizados, en el mismo orden que los textos recibidos.

        Se normalizan aquí para que el coseno del retriever sea un producto
        punto y para que dos backends con convenciones distintas de escala
        produzcan el mismo orden.
        """
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(texts)
        return [_unit(list(map(float, vector))) for vector in vectors]


class TransformerEmbeddings:
    """Implementación de `EmbeddingsPort` sobre `sentence-transformers`.

    Más preciso que el modelo estático y bastante más pesado: arrastra `torch`.
    Se adopta porque la calidad de recuperación es lo que sostiene el gate de
    grounding, y un fragmento no recuperado es un claim sin fuente.

    **Prefijos asimétricos.** Los modelos de la familia E5 se entrenaron con
    `query:` delante de la consulta y `passage:` delante del documento, y usarlos
    no es cosmético: sin ellos, el modelo trata la pregunta como si fuera otro
    documento y la similitud cae de forma apreciable. Por eso `embed` y
    `embed_documents` son operaciones distintas aquí, aunque el puerto solo
    exija la primera.
    """

    def __init__(
        self,
        *,
        model_id: str = TRANSFORMER_MODEL,
        query_prefix: str = "query: ",
        passage_prefix: str = "passage: ",
    ) -> None:
        self._model_id = model_id
        self._query_prefix = query_prefix
        self._passage_prefix = passage_prefix
        self._model: SentenceTransformer | None = None

    @property
    def model_name(self) -> str:
        return f"sentence-transformers:{self._model_id}"

    @property
    def dimension(self) -> int:
        dimension = self._load().get_sentence_embedding_dimension()
        if dimension is None:  # pragma: no cover - depende del modelo cargado
            raise RuntimeError(
                f"el modelo {self._model_id!r} no declara dimensión de embedding; "
                f"no se puede indexar contra él"
            )
        return int(dimension)

    @property
    def is_semantic(self) -> bool:
        return True

    def _load(self) -> SentenceTransformer:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - depende del entorno
                raise RuntimeError(_TRANSFORMER_HINT) from exc
            self._model = SentenceTransformer(self._model_id)
        return self._model

    def _encode(self, texts: list[str], prefix: str) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._load().encode(
            [f"{prefix}{text}" for text in texts],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [list(map(float, vector)) for vector in vectors]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Vectoriza como **consulta**.

        Es el lado que usa el retriever al buscar. La ingesta debe llamar a
        `embed_documents`, que aplica el prefijo de pasaje.
        """
        return self._encode(texts, self._query_prefix)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Vectoriza como **pasaje**, para indexar."""
        return self._encode(texts, self._passage_prefix)


class DocumentSideEmbeddings:
    """Envoltura que fuerza el lado «pasaje» de un adapter asimétrico.

    La ingesta recibe un `EmbeddingsPort` y llama a `embed`. Un adapter
    asimétrico necesita que esa llamada use el prefijo de documento, no el de
    consulta, y la ingesta no tiene por qué saberlo. Esta envoltura traduce.
    """

    def __init__(self, inner: TransformerEmbeddings) -> None:
        self._inner = inner

    @property
    def model_name(self) -> str:
        return self._inner.model_name

    @property
    def dimension(self) -> int:
        return self._inner.dimension

    @property
    def is_semantic(self) -> bool:
        return True

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self._inner.embed_documents(texts)


def _unit(vector: list[float]) -> list[float]:
    norm = sum(value * value for value in vector) ** 0.5
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]


def is_available() -> bool:
    """Si `model2vec` está instalado. Las pruebas de integración lo consultan."""
    try:
        import model2vec  # noqa: F401
    except ImportError:
        return False
    return True
