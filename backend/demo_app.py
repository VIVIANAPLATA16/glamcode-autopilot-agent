"""Flask JSON API for the GlamCode Autopilot Agent demo."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

import agente_proactivo
import agente_reservas
import revision_humana as rh

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

rh.init_db()


def _error_response(message: str, status_code: int = 400):
    return jsonify({"ok": False, "error": message}), status_code


def _success_response(data: dict, status_code: int = 200):
    payload = {"ok": True, **data}
    return jsonify(payload), status_code


@app.errorhandler(404)
def not_found(_error):
    return _error_response("Endpoint no encontrado.", 404)


@app.errorhandler(405)
def method_not_allowed(_error):
    return _error_response("Método HTTP no permitido.", 405)


@app.errorhandler(500)
def internal_error(_error):
    logger.exception("Internal server error")
    return _error_response("Error interno del servidor.", 500)


@app.route("/api/health", methods=["GET"])
def health():
    return _success_response({"status": "ok", "service": "glamcode-autopilot-agent"})


@app.route("/api/simular-mensaje", methods=["POST"])
def simular_mensaje():
    """
    Flujo REACTIVO: recibe un mensaje simulado de WhatsApp y devuelve
    la respuesta del agente con intención, herramienta y escalamiento.
    """
    body = request.get_json(silent=True)
    if not body or "mensaje" not in body:
        return _error_response('Se requiere JSON con campo "mensaje".')

    mensaje = str(body["mensaje"]).strip()
    if not mensaje:
        return _error_response("El campo 'mensaje' no puede estar vacío.")

    conversacion_id = body.get("conversacion_id")
    if conversacion_id is not None:
        try:
            conversacion_id = int(conversacion_id)
        except (TypeError, ValueError):
            return _error_response("conversacion_id debe ser un entero.")

    try:
        resultado = agente_reservas.procesar_mensaje(
            mensaje,
            conversacion_id=conversacion_id,
        )
        return _success_response({"resultado": resultado})
    except ValueError as exc:
        logger.warning("Validation error in reactive flow: %s", exc)
        return _error_response(str(exc), 422)
    except Exception as exc:
        logger.exception("Error in reactive flow")
        return _error_response(f"Error procesando mensaje: {exc}", 500)


@app.route("/api/ejecutar-seguimiento-proactivo", methods=["POST"])
def ejecutar_seguimiento_proactivo():
    """
    Flujo PROACTIVO: dispara jobs de seguimiento y promociones.
    Todos los mensajes quedan como borradores pendientes de aprobación.
    """
    body = request.get_json(silent=True) or {}
    dias_umbral = body.get("dias_umbral")
    incluir_promociones = body.get("incluir_promociones", True)

    if dias_umbral is not None:
        try:
            dias_umbral = int(dias_umbral)
            if dias_umbral < 1:
                return _error_response("dias_umbral debe ser un entero positivo.")
        except (TypeError, ValueError):
            return _error_response("dias_umbral debe ser un entero.")

    try:
        resultado = agente_proactivo.ejecutar_jobs_proactivos(
            dias_umbral=dias_umbral,
            incluir_promociones=bool(incluir_promociones),
        )
        return _success_response({"resultado": resultado})
    except ValueError as exc:
        return _error_response(str(exc), 422)
    except Exception as exc:
        logger.exception("Error in proactive flow")
        return _error_response(f"Error ejecutando jobs proactivos: {exc}", 500)


@app.route("/api/revision-humana", methods=["GET"])
def listar_revision_humana():
    """Lista tareas de revisión humana y borradores proactivos pendientes."""
    estado = request.args.get("estado", "pendiente")
    try:
        if estado == "todos":
            items = rh.listar_todos(estado=None)
        else:
            items = rh.listar_pendientes(estado=estado)
        return _success_response(
            {
                "filtro_estado": estado,
                "total": len(items),
                "items": items,
            }
        )
    except Exception as exc:
        logger.exception("Error listing revision items")
        return _error_response(f"Error listando items: {exc}", 500)


@app.route("/api/revision-humana/<int:item_id>/aprobar", methods=["POST"])
def aprobar_revision(item_id: int):
    """Aprueba un item pendiente y simula el envío/resolución."""
    try:
        item = rh.aprobar_item(item_id)
        return _success_response(
            {
                "mensaje": "Item aprobado. Envío simulado registrado en logs.",
                "item": item,
            }
        )
    except KeyError:
        return _error_response(f"Item {item_id} no encontrado.", 404)
    except ValueError as exc:
        return _error_response(str(exc), 409)
    except Exception as exc:
        logger.exception("Error approving item %s", item_id)
        return _error_response(f"Error aprobando item: {exc}", 500)


@app.route("/api/revision-humana/<int:item_id>/descartar", methods=["POST"])
def descartar_revision(item_id: int):
    """Descarta un item pendiente."""
    try:
        item = rh.descartar_item(item_id)
        return _success_response(
            {
                "mensaje": "Item descartado.",
                "item": item,
            }
        )
    except KeyError:
        return _error_response(f"Item {item_id} no encontrado.", 404)
    except ValueError as exc:
        return _error_response(str(exc), 409)
    except Exception as exc:
        logger.exception("Error discarding item %s", item_id)
        return _error_response(f"Error descartando item: {exc}", 500)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    logger.info("Starting GlamCode Autopilot Agent API on port %s", port)
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1")
