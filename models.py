from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, List, Optional
from enum import Enum

# 1. Definición del Enum para mantener la consistencia con Java
class TipoNodo(str, Enum):
    INICIO = "INICIO"
    FIN = "FIN"
    ACTIVIDAD = "ACTIVIDAD"
    DECISION = "DECISION"

# 2. Representación de CampoDefinicion
class CampoDefinicion(BaseModel):
    nombre: str      # ej: "lectura_kwh"
    etiqueta: str    # ej: "Ingrese la lectura"
    tipo: str        # ej: "NUMBER", "FILE", "TEXT"
    requerido: bool

    @field_validator("nombre", "tipo", mode="before")
    @classmethod
    def _normalize_text_fields(cls, value):
        if value is None:
            return ""
        return value

    @field_validator("etiqueta", mode="before")
    @classmethod
    def _normalize_etiqueta(cls, value):
        if value is None:
            return ""
        return value
    
class PosicionCanvas(BaseModel):
    x: int
    y: int


class NodoIA(BaseModel):
    nodoId: str
    tipoNodo: TipoNodo
    etiqueta: str
    orden: int
    salidas: Dict[str, int] = Field(default_factory=dict)
    posicionCanvas: PosicionCanvas
    departamentoId: Optional[str] = None
    formulario: List[CampoDefinicion] = Field(
        default_factory=list, 
        description="Siempre vacío: la IA no configura formularios"
    )
    condicion: Optional[str] = None
    condicionRechazo: Optional[str] = None

    @field_validator("formulario", mode="before")
    @classmethod
    def _normalize_formulario(cls, value):
        if value is None:
            return []
        return value

    @field_validator("salidas", mode="before")
    @classmethod
    def _normalize_salidas(cls, value):
        if value is None:
            return {}
        if isinstance(value, dict):
            normalized = {}
            for nodo_id, condicion in value.items():
                if nodo_id is None:
                    continue
                if condicion is None:
                    normalized[str(nodo_id)] = 1
                    continue
                try:
                    normalized[str(nodo_id)] = int(condicion)
                except (TypeError, ValueError):
                    normalized[str(nodo_id)] = 1
            return normalized
        if isinstance(value, list):
            normalized = {}
            for item in value:
                if isinstance(item, dict) and item.get("nodoId") is not None:
                    condicion = item.get("condicion", 1)
                    if condicion is None:
                        normalized[str(item["nodoId"])] = 1
                        continue
                    try:
                        normalized[str(item["nodoId"])] = int(condicion)
                    except (TypeError, ValueError):
                        normalized[str(item["nodoId"])] = 1
            return normalized
        return value

    @model_validator(mode="after")
    def _enforce_salidas_by_tipo(self):
        if self.tipoNodo == TipoNodo.DECISION:
            self.salidas = {nodo_id: 0 if int(condicion) == 0 else 1 for nodo_id, condicion in self.salidas.items()}
            return self

        self.salidas = {nodo_id: 1 for nodo_id in self.salidas.keys()}
        return self

class DiagramaActual(BaseModel):
    nodos: List[NodoIA]

class GenerateRequest(BaseModel):
    instruccion: str
    version_id: str
    diagrama_actual: List[NodoIA]


class GenerateResponse(BaseModel):
    nodos: List[NodoIA]

    @model_validator(mode="after")
    def _normalize_graph(self):
        for nodo in self.nodos:
            if nodo.salidas is None:
                nodo.salidas = {}

        self._collapse_tipo(TipoNodo.INICIO, keep_last=False)
        self._collapse_tipo(TipoNodo.FIN, keep_last=True)
        return self

    def _collapse_tipo(self, tipo: TipoNodo, keep_last: bool):
        target_nodes = [n for n in self.nodos if n.tipoNodo == tipo]
        if len(target_nodes) <= 1:
            return

        keep_node = max(target_nodes, key=lambda n: n.orden) if keep_last else min(target_nodes, key=lambda n: n.orden)
        removed_ids = {n.nodoId for n in target_nodes if n.nodoId != keep_node.nodoId}
        if not removed_ids:
            return

        updated_nodes = []
        for nodo in self.nodos:
            if nodo.nodoId in removed_ids:
                continue

            if nodo.salidas:
                redirected = {}
                for destino_id, condicion in nodo.salidas.items():
                    target_id = keep_node.nodoId if destino_id in removed_ids else destino_id
                    if nodo.tipoNodo == TipoNodo.DECISION:
                        redirected[target_id] = 0 if int(condicion) == 0 else 1
                    else:
                        redirected[target_id] = 1
                nodo.salidas = redirected
            else:
                nodo.salidas = {}

            updated_nodes.append(nodo)

        keep_node.salidas = {}
        self.nodos = updated_nodes
