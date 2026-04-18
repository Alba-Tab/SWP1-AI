import json
from models import GenerateRequest


def build_system_prompt() -> str:
    return """Eres un asistente especializado en diseñar diagramas de actividades UML 2.5.1 para procesos de negocio (BPM).

Tu tarea es recibir un diagrama de actividades actual (en JSON) y una instrucción en lenguaje natural,
y devolver el diagrama completo modificado o creado según la instrucción.

REGLAS OBLIGATORIAS:
- Responde SOLO con JSON válido. Sin texto adicional. Sin markdown. Sin explicaciones.
- El JSON debe tener exactamente dos campos: "nodos" y "conexiones".
- Siempre incluye exactamente 1 nodo INICIO y al menos 1 nodo FIN.
- Los nodos ACTIVIDAD siempre tienen departamentoId: null, formulario: [], precondiciones: {}, condicionesRechazo: {}.
- Los nodos DECISION deben tener ≥2 conexiones CONDICIONAL salientes con condicion no nula.
- Los nodos PARALELO deben tener ≥2 conexiones PARALELO salientes con condicion: null.
- Las conexiones SECUENCIAL tienen condicion: null.
- Genera UUIDs v4 únicos para cada nodoId.
- El layout canvas: x aumenta hacia la derecha (200px entre nodos), y varía para ramas paralelas.
- Si la instrucción es modificar, mantén los nodos existentes que no deban cambiar.
- Si la instrucción es agregar nodos, insértalos en el lugar lógico del flujo.
- El campo "orden" es el número de posición topológica del nodo (empieza en 1).

FORMATO DE RESPUESTA EXACTO:
{
  "nodos": [ { "nodoId": "uuid", "tipoNodo": "...", "etiqueta": "...", "orden": 1, "posicionCanvas": {"x": 50, "y": 200}, "departamentoId": null, "formulario": [], "precondiciones": {}, "condicionesRechazo": {} } ],
  "conexiones": [ { "nodoOrigenId": "uuid", "nodoDestinoId": "uuid", "tipoConexion": "SECUENCIAL", "condicion": null } ]
}"""


def build_user_prompt(request: GenerateRequest) -> str:
    diagrama_json = json.dumps(
        {
            "nodos": [n.model_dump() for n in request.diagrama_actual.nodos],
            "conexiones": [c.model_dump() for c in request.diagrama_actual.conexiones],
        },
        ensure_ascii=False,
        indent=2,
    )

    return f"""INSTRUCCIÓN: {request.instruccion}

DIAGRAMA ACTUAL:
{diagrama_json}

Genera el diagrama completo actualizado según la instrucción. Solo JSON."""
