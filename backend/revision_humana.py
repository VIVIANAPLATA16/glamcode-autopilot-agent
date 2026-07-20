"""SQLite persistence for human review tasks and proactive message drafts."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Literal

from mock_data import CITAS_INICIALES

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "glamcode_agent.db"

EstadoItem = Literal["pendiente", "aprobado", "descartado", "enviado"]
TipoItem = Literal["revision_humana", "borrador_proactivo"]
Prioridad = Literal["alta", "normal", "baja"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and seed initial appointment data if empty."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS revision_humana (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                origen TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                prioridad TEXT NOT NULL DEFAULT 'normal',
                titulo TEXT NOT NULL,
                descripcion TEXT,
                mensaje_cliente TEXT,
                mensaje_respuesta TEXT,
                metadata_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mensaje_cliente TEXT NOT NULL,
                intencion TEXT,
                herramienta TEXT,
                respuesta_agente TEXT,
                escalado_revision INTEGER NOT NULL DEFAULT 0,
                revision_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (revision_id) REFERENCES revision_humana(id)
            );

            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_nombre TEXT,
                cliente_telefono TEXT,
                servicio_id TEXT NOT NULL,
                fecha_hora TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'activa',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS turnos_conversacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversacion_id INTEGER NOT NULL,
                rol TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversacion_id) REFERENCES conversaciones(id)
            );

            CREATE INDEX IF NOT EXISTS idx_turnos_conversacion_id
                ON turnos_conversacion(conversacion_id, id);
            """
        )

        count = conn.execute("SELECT COUNT(*) FROM citas").fetchone()[0]
        if count == 0:
            now = _utc_now()
            for cita in CITAS_INICIALES:
                conn.execute(
                    """
                    INSERT INTO citas (id, cliente_nombre, cliente_telefono, servicio_id,
                                         fecha_hora, estado, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cita["id"],
                        cita["cliente_nombre"],
                        cita["cliente_telefono"],
                        cita["servicio_id"],
                        cita["fecha_hora"],
                        cita["estado"],
                        now,
                        now,
                    ),
                )
            logger.info("Seeded %d citas iniciales", len(CITAS_INICIALES))


def crear_revision_humana(
    *,
    origen: str,
    titulo: str,
    descripcion: str,
    mensaje_cliente: str | None = None,
    mensaje_respuesta: str | None = None,
    prioridad: Prioridad = "normal",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crea una tarea de revisión humana (flujo reactivo)."""
    now = _utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO revision_humana
                (tipo, origen, estado, prioridad, titulo, descripcion,
                 mensaje_cliente, mensaje_respuesta, metadata_json, created_at, updated_at)
            VALUES (?, ?, 'pendiente', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "revision_humana",
                origen,
                prioridad,
                titulo,
                descripcion,
                mensaje_cliente,
                mensaje_respuesta,
                json.dumps(metadata or {}, ensure_ascii=False),
                now,
                now,
            ),
        )
        item_id = cursor.lastrowid
    logger.info("Tarea de revisión humana creada id=%s prioridad=%s", item_id, prioridad)
    return obtener_item(int(item_id))


def crear_borrador_proactivo(
    *,
    origen: str,
    titulo: str,
    descripcion: str,
    mensaje_borrador: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crea un borrador proactivo pendiente de aprobación humana."""
    now = _utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO revision_humana
                (tipo, origen, estado, prioridad, titulo, descripcion,
                 mensaje_cliente, mensaje_respuesta, metadata_json, created_at, updated_at)
            VALUES (?, ?, 'pendiente', 'normal', ?, ?, NULL, ?, ?, ?, ?)
            """,
            (
                "borrador_proactivo",
                origen,
                titulo,
                descripcion,
                mensaje_borrador,
                json.dumps(metadata or {}, ensure_ascii=False),
                now,
                now,
            ),
        )
        item_id = cursor.lastrowid
    logger.info("Borrador proactivo creado id=%s origen=%s", item_id, origen)
    return obtener_item(int(item_id))


def listar_pendientes(estado: str | None = "pendiente") -> list[dict[str, Any]]:
    """Lista tareas y borradores, filtrados por estado."""
    query = "SELECT * FROM revision_humana"
    params: tuple[Any, ...] = ()
    if estado:
        query += " WHERE estado = ?"
        params = (estado,)
    query += " ORDER BY CASE prioridad WHEN 'alta' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def listar_todos(estado: str | None = None) -> list[dict[str, Any]]:
    """Lista todos los items de revisión humana / borradores."""
    if estado:
        return listar_pendientes(estado=estado)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM revision_humana ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def obtener_item(item_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM revision_humana WHERE id = ?", (item_id,)
        ).fetchone()
    if row is None:
        raise KeyError(f"Item de revisión humana no encontrado: id={item_id}")
    return _row_to_dict(row)


def aprobar_item(item_id: int) -> dict[str, Any]:
    """Aprueba un item: simula envío/resolución y marca como enviado."""
    item = obtener_item(item_id)
    if item["estado"] != "pendiente":
        raise ValueError(f"El item {item_id} no está pendiente (estado={item['estado']}).")

    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE revision_humana
            SET estado = 'enviado', updated_at = ?
            WHERE id = ?
            """,
            (now, item_id),
        )

    updated = obtener_item(item_id)
    # Simular envío: log en consola
    if updated["tipo"] == "borrador_proactivo":
        logger.info(
            "[SIMULACIÓN ENVÍO] Borrador proactivo #%s enviado: %s",
            item_id,
            updated.get("mensaje_respuesta", "")[:80],
        )
    else:
        logger.info(
            "[SIMULACIÓN] Revisión humana #%s aprobada/resuelta",
            item_id,
        )
    return updated


def descartar_item(item_id: int) -> dict[str, Any]:
    """Descarta un item pendiente."""
    item = obtener_item(item_id)
    if item["estado"] != "pendiente":
        raise ValueError(f"El item {item_id} no está pendiente (estado={item['estado']}).")

    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE revision_humana
            SET estado = 'descartado', updated_at = ?
            WHERE id = ?
            """,
            (now, item_id),
        )
    logger.info("Item #%s descartado", item_id)
    return obtener_item(item_id)


def crear_sesion_conversacion() -> int:
    """Crea una sesión de conversación multi-turno y devuelve su id."""
    now = _utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO conversaciones
                (mensaje_cliente, intencion, herramienta, respuesta_agente,
                 escalado_revision, revision_id, created_at)
            VALUES ('', NULL, NULL, '', 0, NULL, ?)
            """,
            (now,),
        )
        return int(cursor.lastrowid)


def conversacion_existe(conversacion_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM conversaciones WHERE id = ?",
            (conversacion_id,),
        ).fetchone()
    return row is not None


def guardar_turno(conversacion_id: int, rol: str, mensaje: str) -> None:
    """Persiste un turno (cliente o agente) en la sesión de conversación."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO turnos_conversacion (conversacion_id, rol, mensaje, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (conversacion_id, rol, mensaje, _utc_now()),
        )


def obtener_historial(conversacion_id: int, limite: int = 6) -> list[dict[str, Any]]:
    """Devuelve los últimos turnos de la conversación (más antiguos primero)."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT rol, mensaje, timestamp
            FROM turnos_conversacion
            WHERE conversacion_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (conversacion_id, limite),
        ).fetchall()
    return [
        {"rol": row["rol"], "mensaje": row["mensaje"], "timestamp": row["timestamp"]}
        for row in reversed(rows)
    ]


def actualizar_conversacion_sesion(
    conversacion_id: int,
    *,
    mensaje_cliente: str,
    intencion: str | None,
    herramienta: str | None,
    respuesta_agente: str,
    escalado_revision: bool,
    revision_id: int | None = None,
) -> None:
    """Actualiza el resumen de la sesión con el último intercambio."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE conversaciones
            SET mensaje_cliente = ?,
                intencion = ?,
                herramienta = ?,
                respuesta_agente = ?,
                escalado_revision = ?,
                revision_id = ?
            WHERE id = ?
            """,
            (
                mensaje_cliente,
                intencion,
                herramienta,
                respuesta_agente,
                1 if escalado_revision else 0,
                revision_id,
                conversacion_id,
            ),
        )


def guardar_conversacion(
    *,
    mensaje_cliente: str,
    intencion: str | None,
    herramienta: str | None,
    respuesta_agente: str,
    escalado_revision: bool,
    revision_id: int | None = None,
) -> int:
    """Compatibilidad: crea sesión, guarda turnos y actualiza resumen."""
    conversacion_id = crear_sesion_conversacion()
    guardar_turno(conversacion_id, "cliente", mensaje_cliente)
    guardar_turno(conversacion_id, "agente", respuesta_agente)
    actualizar_conversacion_sesion(
        conversacion_id,
        mensaje_cliente=mensaje_cliente,
        intencion=intencion,
        herramienta=herramienta,
        respuesta_agente=respuesta_agente,
        escalado_revision=escalado_revision,
        revision_id=revision_id,
    )
    return conversacion_id


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    metadata = row["metadata_json"]
    return {
        "id": row["id"],
        "tipo": row["tipo"],
        "origen": row["origen"],
        "estado": row["estado"],
        "prioridad": row["prioridad"],
        "titulo": row["titulo"],
        "descripcion": row["descripcion"],
        "mensaje_cliente": row["mensaje_cliente"],
        "mensaje_respuesta": row["mensaje_respuesta"],
        "metadata": json.loads(metadata) if metadata else {},
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# --- Operaciones de citas (usadas por agente_reservas) ---


def listar_citas_activas() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM citas WHERE estado = 'activa' ORDER BY fecha_hora"
        ).fetchall()
    return [dict(row) for row in rows]


def obtener_cita(cita_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM citas WHERE id = ?", (cita_id,)).fetchone()
    return dict(row) if row else None


def buscar_citas_por_cliente(telefono: str | None, nombre: str | None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if telefono:
            rows = conn.execute(
                "SELECT * FROM citas WHERE estado = 'activa' AND cliente_telefono = ?",
                (telefono,),
            ).fetchall()
        elif nombre:
            rows = conn.execute(
                "SELECT * FROM citas WHERE estado = 'activa' AND cliente_nombre LIKE ?",
                (f"%{nombre}%",),
            ).fetchall()
        else:
            return []
    return [dict(row) for row in rows]


def hay_conflicto_horario(fecha_hora: str, excluir_cita_id: int | None = None) -> bool:
    with get_connection() as conn:
        if excluir_cita_id:
            row = conn.execute(
                """
                SELECT COUNT(*) FROM citas
                WHERE estado = 'activa' AND fecha_hora = ? AND id != ?
                """,
                (fecha_hora, excluir_cita_id),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT COUNT(*) FROM citas
                WHERE estado = 'activa' AND fecha_hora = ?
                """,
                (fecha_hora,),
            ).fetchone()
    return row[0] > 0


def crear_cita(
    *,
    cliente_nombre: str | None,
    cliente_telefono: str | None,
    servicio_id: str,
    fecha_hora: str,
) -> dict[str, Any]:
    now = _utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO citas (cliente_nombre, cliente_telefono, servicio_id,
                                fecha_hora, estado, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'activa', ?, ?)
            """,
            (cliente_nombre, cliente_telefono, servicio_id, fecha_hora, now, now),
        )
        cita_id = cursor.lastrowid
    return obtener_cita(int(cita_id))  # type: ignore[return-value]


def reagendar_cita(cita_id: int, nueva_fecha_hora: str) -> dict[str, Any]:
    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            "UPDATE citas SET fecha_hora = ?, updated_at = ? WHERE id = ?",
            (nueva_fecha_hora, now, cita_id),
        )
    cita = obtener_cita(cita_id)
    if cita is None:
        raise KeyError(f"Cita no encontrada: {cita_id}")
    return cita


def cancelar_cita(cita_id: int) -> dict[str, Any]:
    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            "UPDATE citas SET estado = 'cancelada', updated_at = ? WHERE id = ?",
            (now, cita_id),
        )
    cita = obtener_cita(cita_id)
    if cita is None:
        raise KeyError(f"Cita no encontrada: {cita_id}")
    return cita
