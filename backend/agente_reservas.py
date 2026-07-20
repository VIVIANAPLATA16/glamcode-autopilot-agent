"""Flujo REACTIVO: clasificación de intención y herramientas del agente de reservas."""

from __future__ import annotations

import logging
from typing import Any

from mock_data import HORARIO_APERTURA, HORARIO_CIERRE, SERVICIOS
from qwen_client import chat_completion, parse_json_response
import revision_humana as rh

logger = logging.getLogger(__name__)

INTENCIONES_VALIDAS = {"gestion_cita", "cotizacion", "queja", "otro"}
UMBRAL_CONFIANZA = 0.6

MENSAJE_QUEJA_CLIENTE = (
    "Lamentamos mucho lo que nos cuentas. Un miembro de nuestro equipo "
    "se pondrá en contacto contigo personalmente para escucharte. "
    "Gracias por avisarnos."
)

MENSAJE_ESCALAMIENTO = (
    "Gracias por escribirnos. Un miembro de nuestro equipo revisará "
    "tu solicitud y te contactará pronto para ayudarte."
)

HistorialTurno = dict[str, Any]


def procesar_mensaje(
    mensaje: str,
    conversacion_id: int | None = None,
) -> dict[str, Any]:
    """
    Punto de entrada del flujo reactivo.
    Clasifica la intención y enruta a la herramienta correspondiente.
    """
    if conversacion_id is not None and not rh.conversacion_existe(conversacion_id):
        raise ValueError(f"Conversación {conversacion_id} no encontrada.")

    if conversacion_id is None:
        conversacion_id = rh.crear_sesion_conversacion()

    historial = rh.obtener_historial(conversacion_id, limite=6)
    resultado = _enrutar_mensaje(mensaje, historial)

    rh.guardar_turno(conversacion_id, "cliente", mensaje)
    rh.guardar_turno(conversacion_id, "agente", resultado["respuesta"])
    rh.actualizar_conversacion_sesion(
        conversacion_id,
        mensaje_cliente=mensaje,
        intencion=resultado.get("intencion"),
        herramienta=resultado.get("herramienta"),
        respuesta_agente=resultado["respuesta"],
        escalado_revision=resultado.get("escalado_revision_humana", False),
        revision_id=resultado.get("revision_humana_id"),
    )

    resultado["conversacion_id"] = conversacion_id
    return resultado


def _enrutar_mensaje(mensaje: str, historial: list[HistorialTurno]) -> dict[str, Any]:
    clasificacion = _clasificar_intencion(mensaje, historial)
    intencion = clasificacion["intencion"]
    confianza = clasificacion.get("confianza", 0.0)

    logger.info(
        "Mensaje clasificado: intencion=%s confianza=%.2f",
        intencion,
        confianza,
    )

    if confianza < UMBRAL_CONFIANZA or intencion == "otro":
        return _escalar_revision(
            mensaje=mensaje,
            intencion=intencion,
            motivo=clasificacion.get("razon", "Intención no clara o confianza baja"),
            origen="reactivo_baja_confianza",
            clasificacion=clasificacion,
        )

    if intencion == "queja":
        return _manejar_queja(mensaje, clasificacion)

    if intencion == "gestion_cita":
        return _herramienta_gestionar_cita(mensaje, clasificacion, historial)

    if intencion == "cotizacion":
        return _herramienta_cotizar_servicios(mensaje, clasificacion, historial)

    return _escalar_revision(
        mensaje=mensaje,
        intencion=intencion,
        motivo="Intención no reconocida",
        origen="reactivo_desconocido",
        clasificacion=clasificacion,
    )


def _historial_a_mensajes_qwen(
    historial: list[HistorialTurno],
) -> list[dict[str, str]]:
    mensajes: list[dict[str, str]] = []
    for turno in historial:
        role = "user" if turno["rol"] == "cliente" else "assistant"
        mensajes.append({"role": role, "content": turno["mensaje"]})
    return mensajes


def _clasificar_intencion(
    mensaje: str,
    historial: list[HistorialTurno] | None = None,
) -> dict[str, Any]:
    """Usa Qwen para clasificar la intención del mensaje del cliente."""
    system_prompt = """Eres un clasificador de intenciones para un salón de belleza en Colombia.
Analiza el mensaje del cliente considerando el historial de la conversación si existe.
Responde SOLO con JSON válido con esta estructura:
{
  "intencion": "gestion_cita" | "cotizacion" | "queja" | "otro",
  "confianza": 0.0 a 1.0,
  "razon": "breve explicación"
}

Reglas:
- "gestion_cita": agendar, reagendar, cancelar o modificar citas
- "cotizacion": preguntas de precio, costos, cuánto cuesta, alternativas de servicios
- "queja": insatisfacción, mal servicio, cobro incorrecto, reclamos, quejas
- "otro": saludos, horarios generales, preguntas fuera de alcance, ambigüedad
- Usa el historial para interpretar mensajes cortos o de seguimiento (ej. "¿y qué otro hay?")."""

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        *_historial_a_mensajes_qwen(historial or []),
        {"role": "user", "content": f'Mensaje actual del cliente: "{mensaje}"'},
    ]

    raw = chat_completion(messages, response_format_json=True)
    result = parse_json_response(raw)

    if result.get("intencion") not in INTENCIONES_VALIDAS:
        result["intencion"] = "otro"
        result["confianza"] = min(float(result.get("confianza", 0)), 0.5)

    result["confianza"] = float(result.get("confianza", 0))
    return result


def _manejar_queja(mensaje: str, clasificacion: dict[str, Any]) -> dict[str, Any]:
    """
    Compuerta de queja: NUNCA resolver automáticamente.
    Siempre escala a revisión humana con prioridad alta.
    """
    revision = rh.crear_revision_humana(
        origen="reactivo_queja",
        titulo="Queja de cliente — atención prioritaria",
        descripcion=clasificacion.get("razon", "Cliente reporta una queja"),
        mensaje_cliente=mensaje,
        mensaje_respuesta=MENSAJE_QUEJA_CLIENTE,
        prioridad="alta",
        metadata={"clasificacion": clasificacion},
    )

    return {
        "intencion": "queja",
        "confianza": clasificacion.get("confianza"),
        "herramienta": "compuerta_queja",
        "respuesta": MENSAJE_QUEJA_CLIENTE,
        "escalado_revision_humana": True,
        "revision_humana_id": revision["id"],
        "detalle": {"motivo": "Queja detectada — escalamiento obligatorio"},
    }


def _herramienta_gestionar_cita(
    mensaje: str,
    clasificacion: dict[str, Any],
    historial: list[HistorialTurno],
) -> dict[str, Any]:
    """
    Extrae parámetros de la cita con Qwen y ejecuta nueva/reagendar/cancelar
    contra la base SQLite, o escala a revisión humana si hay ambigüedad.
    """
    extraccion = _extraer_datos_cita(mensaje, historial)
    operacion = extraccion.get("operacion")
    servicio_solicitado = extraccion.get("servicio")
    fecha_hora = extraccion.get("fecha_hora")
    cita_referencia_id = extraccion.get("cita_referencia_id")
    cliente_nombre = extraccion.get("cliente_nombre")
    cliente_telefono = extraccion.get("cliente_telefono")
    ambiguo = extraccion.get("ambiguo", False)
    motivo_ambiguedad = extraccion.get("motivo_ambiguedad", "")

    servicio_id = (
        _resolver_servicio_id(servicio_solicitado, historial)
        if servicio_solicitado
        else None
    )

    if servicio_solicitado and servicio_id is None:
        return _escalar_gestion_cita(
            mensaje,
            clasificacion,
            extraccion,
            motivo=(
                f"El cliente preguntó por un servicio que no está en nuestro catálogo: "
                f"{servicio_solicitado}"
            ),
        )

    if ambiguo or operacion not in ("nueva", "reagendar", "cancelar"):
        return _escalar_gestion_cita(
            mensaje,
            clasificacion,
            extraccion,
            motivo=motivo_ambiguedad or "No se pudo determinar la operación de cita",
        )

    if operacion == "nueva":
        if not servicio_id or not fecha_hora:
            return _escalar_gestion_cita(
                mensaje,
                clasificacion,
                extraccion,
                motivo="Faltan servicio o fecha/hora para agendar",
            )
        if rh.hay_conflicto_horario(fecha_hora):
            return _escalar_gestion_cita(
                mensaje,
                clasificacion,
                extraccion,
                motivo=f"Conflicto de horario: {fecha_hora} no disponible",
            )
        cita = rh.crear_cita(
            cliente_nombre=cliente_nombre,
            cliente_telefono=cliente_telefono,
            servicio_id=servicio_id,
            fecha_hora=fecha_hora,
        )
        respuesta = (
            f"¡Listo! Tu cita de {SERVICIOS[servicio_id]['nombre']} quedó agendada "
            f"para el {fecha_hora}. Te esperamos en el salón."
        )
        return _respuesta_exitosa(
            mensaje, clasificacion, "gestionar_cita", respuesta,
            {"operacion": "nueva", "cita": cita},
        )

    if operacion == "reagendar":
        cita = _resolver_cita_existente(cita_referencia_id, cliente_nombre, cliente_telefono)
        if cita is None:
            return _escalar_gestion_cita(
                mensaje,
                clasificacion,
                extraccion,
                motivo="No se encontró la cita a reagendar",
            )
        if not fecha_hora:
            return _escalar_gestion_cita(
                mensaje,
                clasificacion,
                extraccion,
                motivo="Falta la nueva fecha/hora para reagendar",
            )
        if rh.hay_conflicto_horario(fecha_hora, excluir_cita_id=cita["id"]):
            return _escalar_gestion_cita(
                mensaje,
                clasificacion,
                extraccion,
                motivo=f"Conflicto de horario: {fecha_hora} no disponible",
            )
        cita_actualizada = rh.reagendar_cita(cita["id"], fecha_hora)
        respuesta = (
            f"Tu cita #{cita['id']} fue reagendada para el {fecha_hora}. "
            "¡Te esperamos!"
        )
        return _respuesta_exitosa(
            mensaje, clasificacion, "gestionar_cita", respuesta,
            {"operacion": "reagendar", "cita": cita_actualizada},
        )

    if operacion == "cancelar":
        cita = _resolver_cita_existente(cita_referencia_id, cliente_nombre, cliente_telefono)
        if cita is None:
            return _escalar_gestion_cita(
                mensaje,
                clasificacion,
                extraccion,
                motivo="No se encontró la cita a cancelar",
            )
        cita_cancelada = rh.cancelar_cita(cita["id"])
        respuesta = (
            f"Tu cita #{cita['id']} del {cita['fecha_hora']} fue cancelada. "
            "Si deseas reagendar, escríbenos cuando quieras."
        )
        return _respuesta_exitosa(
            mensaje, clasificacion, "gestionar_cita", respuesta,
            {"operacion": "cancelar", "cita": cita_cancelada},
        )

    return _escalar_gestion_cita(mensaje, clasificacion, extraccion, motivo="Operación no soportada")


def _extraer_datos_cita(
    mensaje: str,
    historial: list[HistorialTurno] | None = None,
) -> dict[str, Any]:
    """Qwen extrae operación, servicio, fecha/hora y referencia de cita."""
    citas_activas = rh.listar_citas_activas()
    citas_contexto = [
        {
            "id": c["id"],
            "cliente": c["cliente_nombre"],
            "telefono": c["cliente_telefono"],
            "servicio": c["servicio_id"],
            "fecha_hora": c["fecha_hora"],
        }
        for c in citas_activas
    ]

    system_prompt = f"""Eres un asistente de un salón de belleza. Extrae datos de gestión de citas.
Considera el historial de la conversación para interpretar referencias implícitas.
Horario del salón: {HORARIO_APERTURA} a {HORARIO_CIERRE}, lunes a sábado.
Formato de fecha_hora preferido: YYYY-MM-DD HH:MM (24h). Si el cliente dice "mañana" o "el viernes", infiere la fecha más probable.

Citas activas actuales:
{citas_contexto}

Responde SOLO JSON:
{{
  "operacion": "nueva" | "reagendar" | "cancelar" | null,
  "servicio": "texto del servicio mencionado o null",
  "fecha_hora": "YYYY-MM-DD HH:MM o null",
  "cita_referencia_id": número o null,
  "cliente_nombre": "nombre si lo menciona o null",
  "cliente_telefono": "teléfono si lo menciona o null",
  "ambiguo": true/false,
  "motivo_ambiguedad": "string o vacío"
}}

Marca ambiguo=true si falta información crítica, hay múltiples interpretaciones,
o el cliente pide algo fuera de lo estándar (ej. domingo, horario fuera de rango)."""

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        *_historial_a_mensajes_qwen(historial or []),
        {"role": "user", "content": f'Mensaje actual: "{mensaje}"'},
    ]

    raw = chat_completion(messages, response_format_json=True)
    return parse_json_response(raw)


def _herramienta_cotizar_servicios(
    mensaje: str,
    clasificacion: dict[str, Any],
    historial: list[HistorialTurno],
) -> dict[str, Any]:
    """Calcula cotización de uno o varios servicios mencionados."""
    servicios_mencionados = _extraer_servicios_cotizacion(mensaje, historial)

    if not servicios_mencionados:
        return _escalar_revision(
            mensaje=mensaje,
            intencion="cotizacion",
            motivo="No se identificaron servicios para cotizar",
            origen="reactivo_cotizacion_sin_servicios",
            herramienta="cotizar_servicios",
            clasificacion=clasificacion,
        )

    desglose: list[dict[str, Any]] = []
    total = 0
    desconocidos: list[str] = []

    for nombre in servicios_mencionados:
        servicio_id = _resolver_servicio_id(nombre, historial)
        if servicio_id is None:
            desconocidos.append(nombre)
            continue
        info = SERVICIOS[servicio_id]
        desglose.append(
            {
                "servicio_id": servicio_id,
                "nombre": info["nombre"],
                "precio": info["precio"],
            }
        )
        total += info["precio"]

    if desconocidos:
        motivo = (
            "El cliente preguntó por un servicio que no está en nuestro catálogo: "
            + ", ".join(desconocidos)
        )
        return _escalar_revision(
            mensaje=mensaje,
            intencion="cotizacion",
            motivo=motivo,
            origen="reactivo_cotizacion_servicio_desconocido",
            herramienta="cotizar_servicios",
            clasificacion=clasificacion,
            metadata={"servicios_desconocidos": desconocidos},
        )

    lineas = [f"• {item['nombre']}: ${item['precio']:,} COP" for item in desglose]
    respuesta = (
        "Estos son nuestros precios:\n"
        + "\n".join(lineas)
        + f"\n\nTotal: ${total:,} COP\n\n¿Te gustaría agendar alguno de estos servicios?"
    )

    return _respuesta_exitosa(
        mensaje,
        clasificacion,
        "cotizar_servicios",
        respuesta,
        {"desglose": desglose, "total": total},
    )


def _extraer_servicios_cotizacion(
    mensaje: str,
    historial: list[HistorialTurno] | None = None,
) -> list[str]:
    """Qwen identifica los servicios mencionados para cotización."""
    catalogo = [
        {"id": sid, "nombre": info["nombre"], "aliases": info["aliases"]}
        for sid, info in SERVICIOS.items()
    ]

    system_prompt = f"""Identifica qué servicios menciona el cliente para cotización.
Usa el historial de la conversación para resolver referencias como "¿y qué otro hay?" o "el otro manicure".
Catálogo disponible (solo estos servicios existen): {catalogo}

Responde SOLO JSON:
{{"servicios": ["texto exacto del servicio que el cliente pregunta", ...]}}

Incluye el nombre o descripción tal como el cliente lo pidió, aunque no esté en el catálogo.
Si no hay servicios claros, devuelve lista vacía."""

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        *_historial_a_mensajes_qwen(historial or []),
        {"role": "user", "content": f'Mensaje actual: "{mensaje}"'},
    ]

    raw = chat_completion(messages, response_format_json=True)
    result = parse_json_response(raw)
    return result.get("servicios", [])


def _catalogo_para_matching() -> list[dict[str, Any]]:
    return [
        {"servicio_id": sid, "nombre": info["nombre"], "aliases": info["aliases"]}
        for sid, info in SERVICIOS.items()
    ]


def _resolver_servicio_id(
    texto: str | None,
    historial: list[HistorialTurno] | None = None,
) -> str | None:
    """Usa Qwen para mapear el texto del cliente a un servicio_id exacto del catálogo."""
    if not texto:
        return None

    catalogo = _catalogo_para_matching()
    system_prompt = f"""Eres un matcher estricto de servicios para un salón de belleza.
Catálogo REAL (solo estos servicios existen):
{catalogo}

Responde SOLO JSON:
{{
  "servicio_id": "id_exacto_del_catalogo" | null,
  "razon": "breve explicación"
}}

Reglas ESTRICTAS:
- Devuelve servicio_id SOLO si el servicio pedido corresponde CLARAMENTE a uno del catálogo.
- Devuelve null si el servicio mencionado NO existe (ej. "manicure semipermanente" cuando solo hay "Manicure tradicional").
- NO hagas matching parcial por palabras compartidas: compartir "manicure" NO basta si el tipo es distinto.
- Devuelve null si hay ambigüedad entre varios servicios.
- Usa el historial solo para resolver referencias explícitas al contexto, no para inventar servicios."""

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        *_historial_a_mensajes_qwen(historial or []),
        {"role": "user", "content": f'Servicio mencionado por el cliente: "{texto}"'},
    ]

    raw = chat_completion(messages, response_format_json=True)
    result = parse_json_response(raw)
    servicio_id = result.get("servicio_id")

    if servicio_id is None:
        return None
    if servicio_id not in SERVICIOS:
        logger.warning("Qwen devolvió servicio_id inválido: %s", servicio_id)
        return None
    return str(servicio_id)


def _resolver_cita_existente(
    cita_id: int | None,
    nombre: str | None,
    telefono: str | None,
) -> dict[str, Any] | None:
    if cita_id:
        return rh.obtener_cita(int(cita_id))
    citas = rh.buscar_citas_por_cliente(telefono, nombre)
    if len(citas) == 1:
        return citas[0]
    return None


def _escalar_gestion_cita(
    mensaje: str,
    clasificacion: dict[str, Any],
    extraccion: dict[str, Any],
    motivo: str,
) -> dict[str, Any]:
    return _escalar_revision(
        mensaje=mensaje,
        intencion="gestion_cita",
        motivo=motivo,
        origen="reactivo_gestion_cita",
        herramienta="gestionar_cita",
        clasificacion=clasificacion,
        metadata={"clasificacion": clasificacion, "extraccion": extraccion},
    )


def _escalar_revision(
    *,
    mensaje: str,
    intencion: str,
    motivo: str,
    origen: str,
    herramienta: str | None = None,
    clasificacion: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Escala a revisión humana en lugar de improvisar respuesta."""
    meta = metadata or {}
    if clasificacion:
        meta.setdefault("clasificacion", clasificacion)
    meta["motivo"] = motivo

    revision = rh.crear_revision_humana(
        origen=origen,
        titulo=f"Revisión humana — {intencion}",
        descripcion=motivo,
        mensaje_cliente=mensaje,
        mensaje_respuesta=MENSAJE_ESCALAMIENTO,
        prioridad="normal",
        metadata=meta,
    )

    return {
        "intencion": intencion,
        "confianza": meta.get("clasificacion", {}).get("confianza"),
        "herramienta": herramienta or "escalamiento",
        "respuesta": MENSAJE_ESCALAMIENTO,
        "escalado_revision_humana": True,
        "revision_humana_id": revision["id"],
        "detalle": {"motivo": motivo},
    }


def _respuesta_exitosa(
    mensaje: str,
    clasificacion: dict[str, Any],
    herramienta: str,
    respuesta: str,
    detalle: dict[str, Any],
) -> dict[str, Any]:
    return {
        "intencion": clasificacion.get("intencion"),
        "confianza": clasificacion.get("confianza"),
        "herramienta": herramienta,
        "respuesta": respuesta,
        "escalado_revision_humana": False,
        "revision_humana_id": None,
        "detalle": detalle,
    }
