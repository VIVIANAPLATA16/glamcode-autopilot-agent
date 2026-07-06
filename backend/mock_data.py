"""Mock data for the fictional beauty salon 'Salón Estrella Ficticia'."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

# Horario estándar del salón (lunes a sábado)
HORARIO_APERTURA = "09:00"
HORARIO_CIERRE = "19:00"
DURACION_CITA_MINUTOS = 60

# Catálogo de servicios con precios en COP (datos ficticios)
SERVICIOS: dict[str, dict[str, Any]] = {
    "corte_dama": {
        "nombre": "Corte de cabello dama",
        "precio": 45000,
        "duracion_minutos": 60,
        "aliases": ["corte", "corte dama", "corte de cabello"],
    },
    "corte_caballero": {
        "nombre": "Corte de cabello caballero",
        "precio": 35000,
        "duracion_minutos": 45,
        "aliases": ["corte caballero", "corte hombre", "corte masculino"],
    },
    "manicure": {
        "nombre": "Manicure tradicional",
        "precio": 28000,
        "duracion_minutos": 45,
        "aliases": ["manicure", "uñas", "manos"],
    },
    "pedicure": {
        "nombre": "Pedicure tradicional",
        "precio": 32000,
        "duracion_minutos": 50,
        "aliases": ["pedicure", "pies"],
    },
    "cejas": {
        "nombre": "Diseño de cejas",
        "precio": 18000,
        "duracion_minutos": 30,
        "aliases": ["cejas", "depilación cejas", "perfilado cejas"],
    },
    "tinte": {
        "nombre": "Tinte completo",
        "precio": 85000,
        "duracion_minutos": 120,
        "aliases": ["tinte", "color", "tintura"],
    },
    "balayage": {
        "nombre": "Balayage",
        "precio": 180000,
        "duracion_minutos": 180,
        "aliases": ["balayage", "mechas"],
    },
    "keratina": {
        "nombre": "Keratina",
        "precio": 220000,
        "duracion_minutos": 180,
        "aliases": ["keratina", "alisado"],
    },
}

# Citas ya agendadas (mock inicial)
def _cita_en_dias(dias: int, hora: str) -> str:
    fecha = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    fecha += timedelta(days=dias)
    return f"{fecha.strftime('%Y-%m-%d')} {hora}"


CITAS_INICIALES: list[dict[str, Any]] = [
    {
        "id": 1,
        "cliente_nombre": "Laura Méndez",
        "cliente_telefono": "300-111-0001",
        "servicio_id": "manicure",
        "fecha_hora": _cita_en_dias(2, "10:00"),
        "estado": "activa",
    },
    {
        "id": 2,
        "cliente_nombre": "Carolina Ruiz",
        "cliente_telefono": "300-222-0002",
        "servicio_id": "corte_dama",
        "fecha_hora": _cita_en_dias(3, "14:00"),
        "estado": "activa",
    },
    {
        "id": 3,
        "cliente_nombre": "Ana Sofía Torres",
        "cliente_telefono": "300-333-0003",
        "servicio_id": "balayage",
        "fecha_hora": _cita_en_dias(5, "09:00"),
        "estado": "activa",
    },
    {
        "id": 4,
        "cliente_nombre": "Valentina Gómez",
        "cliente_telefono": "300-444-0004",
        "servicio_id": "pedicure",
        "fecha_hora": _cita_en_dias(1, "16:00"),
        "estado": "activa",
    },
]

# Clientes ficticios con perfil y última visita
def _fecha_hace_dias(dias: int) -> str:
    return (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")


CLIENTES: list[dict[str, Any]] = [
    {
        "id": 1,
        "nombre": "María Fernández",
        "telefono": "300-555-0101",
        "perfil": "frecuente",
        "ultima_visita": _fecha_hace_dias(12),
        "servicios_favoritos": ["corte_dama", "cejas"],
    },
    {
        "id": 2,
        "nombre": "Diana López",
        "telefono": "300-555-0102",
        "perfil": "ocasional",
        "ultima_visita": _fecha_hace_dias(45),
        "servicios_favoritos": ["manicure", "pedicure"],
    },
    {
        "id": 3,
        "nombre": "Camila Restrepo",
        "telefono": "300-555-0103",
        "perfil": "vip",
        "ultima_visita": _fecha_hace_dias(8),
        "servicios_favoritos": ["balayage", "keratina"],
    },
    {
        "id": 4,
        "nombre": "Juliana Vargas",
        "telefono": "300-555-0104",
        "perfil": "inactivo",
        "ultima_visita": _fecha_hace_dias(90),
        "servicios_favoritos": ["corte_dama"],
    },
    {
        "id": 5,
        "nombre": "Sofía Herrera",
        "telefono": "300-555-0105",
        "perfil": "nuevo",
        "ultima_visita": _fecha_hace_dias(60),
        "servicios_favoritos": ["tinte"],
    },
    {
        "id": 6,
        "nombre": "Paula Castaño",
        "telefono": "300-555-0106",
        "perfil": "frecuente",
        "ultima_visita": _fecha_hace_dias(35),
        "servicios_favoritos": ["manicure", "cejas"],
    },
]

SALON_INFO = {
    "nombre": "Salón Estrella Ficticia",
    "ciudad": "Bogotá, Colombia",
    "telefono": "601-000-0000",
    "direccion": "Calle Ficticia 123, Local 4",
}
