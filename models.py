from pydantic import BaseModel
from typing import Optional


class PosicionCanvas(BaseModel):
    x: int
    y: int


class NodoIA(BaseModel):
    nodoId: str
    tipoNodo: str  # INICIO | FIN | ACTIVIDAD | DECISION | PARALELO
    etiqueta: str
    orden: int
    posicionCanvas: PosicionCanvas
    departamentoId: None = None
    formulario: list = []
    precondiciones: dict = {}
    condicionesRechazo: dict = {}


class ConexionIA(BaseModel):
    nodoOrigenId: str
    nodoDestinoId: str
    tipoConexion: str  # SECUENCIAL | CONDICIONAL | PARALELO
    condicion: Optional[str] = None


class DiagramaActual(BaseModel):
    nodos: list[NodoIA]
    conexiones: list[ConexionIA]


class GenerateRequest(BaseModel):
    instruccion: str
    version_id: str
    diagrama_actual: DiagramaActual


class GenerateResponse(BaseModel):
    nodos: list[NodoIA]
    conexiones: list[ConexionIA]
