import json
from models import GenerateRequest


def build_system_prompt() -> str:
    return """Eres un asistente especializado en diseñar diagramas de actividades UML 2.5.1 para procesos de negocio (BPM).

Tu tarea es recibir un diagrama de actividades actual (en JSON) y una instrucción en lenguaje natural,
y devolver el diagrama completo modificado o creado según la instrucción.

REGLAS OBLIGATORIAS:
- Responde SOLO con JSON válido. Sin texto adicional. Sin markdown. Sin explicaciones.
- El JSON debe tener exactamente 1 campo: "nodos".
- Siempre incluye exactamente 1 nodo INICIO y 1 nodo FIN.
- El contrato esperado es equivalente a AiGenerateResponse -> List<AiNodoDto>.
- Cada AiNodoDto debe tener exactamente: nodoId, tipoNodo, etiqueta, orden, salidas, posicionCanvas, departamentoId, formulario, condicion, condicionRechazo.
- Los nodos ACTIVIDAD siempre tienen departamentoId: null y formulario: [].
- "salidas" es un objeto (mapa) con formato {"uuid-destino": condicion}.
- "salidas" nunca puede ser null (si no hay destino, usa {}).
- En nodos NO-DECISION, todas las salidas tienen valor 1.
- En nodos DECISION, hay exactamente 2 salidas: una con valor 1 (verdadero) y otra con valor 0 (falso).
- Nunca devuelvas más de 1 nodo INICIO ni más de 1 nodo FIN.
- Si el diagrama actual trae múltiples FIN, consolida en un único FIN y redirige las salidas hacia ese FIN.
- los valores de "tipoNodo" deben ser exactamente: "INICIO", "FIN", "ACTIVIDAD" o "DECISION".
- Genera UUIDs v4 únicos para cada nodoId.
- El layout canvas: x aumenta hacia la derecha (200px entre nodos), y varía para ramas paralelas.
- Si la instrucción es modificar, mantén los nodos existentes que no deban cambiar solo continua la instruccion.
- Si la instrucción es agregar nodos, insértalos en el lugar lógico del flujo.
- El campo "orden" es el número de posición topológica del nodo (empieza en 1).

FORMATO DE RESPUESTA:
{
  "nodos": [
    {
      "nodoId": "uuid-1",
      "tipoNodo": "INICIO",
      "etiqueta": "Inicio de proceso",
      "orden": 1,
      "salidas": {"uuid-2": 1},
      "posicionCanvas": {"x": 100, "y": 100},
      "departamentoId": null,
      "formulario": [],
      "condicion": null,
      "condicionRechazo": null
    }
  ]
}"""
 


def build_user_prompt(request: GenerateRequest) -> str:
    diagrama_json = json.dumps(
        {
            "nodos": [n.model_dump(mode="json") for n in request.diagrama_actual],
        },
        ensure_ascii=False,
        indent=2,
    )

    return f"""INSTRUCCIÓN: {request.instruccion}

DIAGRAMA ACTUAL:
{diagrama_json}

Genera el diagrama completo actualizado según la instrucción. Solo JSON."""
