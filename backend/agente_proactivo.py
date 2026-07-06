"""Flujo PROACTIVO: seguimiento de inactivos y promociones segmentadas."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from mock_data import CLIENTES, SALON_INFO, SERVICIOS
from qwen_client import chat_completion
import revision_humana as rh

logger = logging.getLogger(__name__)


def _dias_inactividad_umbral() -> int:
    return int(os.getenv("DIAS_INACTIVIDAD", "30"))


def _dias_desde(fecha_iso: str) -> int:
    ultima = datetime.strptime(fecha_iso, "%Y-%m-%d")
    return (datetime.now() - ultima).days


def ejecutar_seguimiento_clientes_inactivos(
    dias_umbral: int | None = None,
) -> dict[str, Any]:
    """
    Job proactivo: identifica clientes inactivos y genera borradores de seguimiento.
    NINGÚN mensaje se envía directamente — todos quedan pendientes de aprobación.
    """
    umbral = dias_umbral if dias_umbral is not None else _dias_inactividad_umbral()
    inactivos = [
        c for c in CLIENTES if _dias_desde(c["ultima_visita"]) > umbral
    ]

    logger.info(
        "Seguimiento proactivo: %d clientes inactivos (> %d días)",
        len(inactivos),
        umbral,
    )

    borradores: list[dict[str, Any]] = []
    for cliente in inactivos:
        dias = _dias_desde(cliente["ultima_visita"])
        mensaje = _generar_mensaje_seguimiento(cliente, dias)
        borrador = rh.crear_borrador_proactivo(
            origen="proactivo_seguimiento",
            titulo=f"Seguimiento — {cliente['nombre']}",
            descripcion=(
                f"Cliente inactivo hace {dias} días. "
                f"Última visita: {cliente['ultima_visita']}."
            ),
            mensaje_borrador=mensaje,
            metadata={
                "cliente_id": cliente["id"],
                "cliente_nombre": cliente["nombre"],
                "cliente_telefono": cliente["telefono"],
                "dias_inactivo": dias,
                "perfil": cliente["perfil"],
            },
        )
        borradores.append(borrador)

    return {
        "job": "seguimiento_clientes_inactivos",
        "dias_umbral": umbral,
        "clientes_evaluados": len(CLIENTES),
        "clientes_inactivos": len(inactivos),
        "borradores_generados": len(borradores),
        "borradores": borradores,
        "nota": "Todos los borradores requieren aprobación humana antes del envío simulado.",
    }


def ejecutar_generar_promociones() -> dict[str, Any]:
    """
    Job proactivo: genera mensajes promocionales segmentados por perfil de cliente.
    Qwen genera el texto; checkpoint humano obligatorio.
    """
    borradores: list[dict[str, Any]] = []

    for cliente in CLIENTES:
        mensaje = _generar_mensaje_promocion(cliente)
        borrador = rh.crear_borrador_proactivo(
            origen="proactivo_promocion",
            titulo=f"Promoción — {cliente['nombre']} ({cliente['perfil']})",
            descripcion=(
                f"Mensaje promocional segmentado para perfil '{cliente['perfil']}'."
            ),
            mensaje_borrador=mensaje,
            metadata={
                "cliente_id": cliente["id"],
                "cliente_nombre": cliente["nombre"],
                "cliente_telefono": cliente["telefono"],
                "perfil": cliente["perfil"],
                "servicios_favoritos": cliente["servicios_favoritos"],
            },
        )
        borradores.append(borrador)

    logger.info("Promociones proactivas: %d borradores generados", len(borradores))

    return {
        "job": "generar_promociones",
        "clientes_evaluados": len(CLIENTES),
        "borradores_generados": len(borradores),
        "borradores": borradores,
        "nota": "Todos los borradores requieren aprobación humana antes del envío simulado.",
    }


def ejecutar_jobs_proactivos(
    dias_umbral: int | None = None,
    incluir_promociones: bool = True,
) -> dict[str, Any]:
    """Ejecuta todos los jobs proactivos y devuelve resumen consolidado."""
    seguimiento = ejecutar_seguimiento_clientes_inactivos(dias_umbral=dias_umbral)
    resultado: dict[str, Any] = {
        "seguimiento": seguimiento,
        "total_borradores": seguimiento["borradores_generados"],
    }

    if incluir_promociones:
        promociones = ejecutar_generar_promociones()
        resultado["promociones"] = promociones
        resultado["total_borradores"] += promociones["borradores_generados"]

    resultado["nota"] = (
        "Checkpoint humano obligatorio: revisa y aprueba/descarta cada borrador "
        "en GET /api/revision-humana antes de simular el envío."
    )
    return resultado


def _generar_mensaje_seguimiento(cliente: dict[str, Any], dias_inactivo: int) -> str:
    """Genera texto personalizado de seguimiento usando Qwen."""
    servicios_fav = ", ".join(
        SERVICIOS[s]["nombre"] for s in cliente["servicios_favoritos"] if s in SERVICIOS
    )

    system_prompt = f"""Eres el asistente de {SALON_INFO['nombre']}, un salón de belleza en {SALON_INFO['ciudad']}.
Redacta un mensaje de WhatsApp breve, cálido y personalizado para reactivar a un cliente inactivo.
Reglas:
- Máximo 3 oraciones
- Tono empático, sin presionar
- Menciona el nombre del cliente
- Invita a agendar sin prometer descuentos
- Español colombiano natural
- NO uses emojis excesivos (máximo 1)"""

    user_prompt = f"""Cliente: {cliente['nombre']}
Días sin visitar: {dias_inactivo}
Servicios favoritos: {servicios_fav or 'no registrados'}
Perfil: {cliente['perfil']}

Escribe solo el texto del mensaje, sin comillas ni explicaciones."""

    return chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )


def _generar_mensaje_promocion(cliente: dict[str, Any]) -> str:
    """Genera promoción segmentada según perfil del cliente usando Qwen."""
    servicios_fav = ", ".join(
        SERVICIOS[s]["nombre"] for s in cliente["servicios_favoritos"] if s in SERVICIOS
    )

    # Guía de segmentación por perfil (lógica de negocio)
    segmentacion = {
        "vip": "Cliente VIP de alto valor — tono exclusivo, beneficio premium simulado (ej. prioridad en agenda)",
        "frecuente": "Cliente frecuente — tono de agradecimiento y recomendación de servicio complementario",
        "ocasional": "Cliente ocasional — tono amigable invitando a volver con propuesta concreta",
        "inactivo": "Cliente muy inactivo — tono de reencuentro suave, sin presión",
        "nuevo": "Cliente relativamente nuevo — tono de bienvenida y descubrimiento de servicios",
    }
    guia = segmentacion.get(cliente["perfil"], segmentacion["ocasional"])

    system_prompt = f"""Eres el asistente de marketing de {SALON_INFO['nombre']}.
Redacta un mensaje promocional de WhatsApp segmentado según el perfil del cliente.
Reglas:
- Máximo 4 oraciones
- Personaliza según el perfil indicado
- Puedes mencionar un beneficio ficticio de demo (ej. 10% en servicio favorito) — es demo, no real
- Español colombiano
- Solo el texto del mensaje, sin comillas"""

    user_prompt = f"""Cliente: {cliente['nombre']}
Perfil: {cliente['perfil']}
Guía de segmentación: {guia}
Servicios favoritos: {servicios_fav or 'generales'}
Días desde última visita: {_dias_desde(cliente['ultima_visita'])}

Escribe el mensaje promocional."""

    return chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
    )
