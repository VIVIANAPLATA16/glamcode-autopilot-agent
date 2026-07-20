import type {
  AgentMeta,
  ClientProfile,
  Intent,
  Priority,
  ProactiveResult,
  ReviewTask,
  TaskOrigin,
} from "@/lib/agent-data"

// Empty string = same-origin (used in production behind Next.js rewrites).
// Locally defaults to Flask on :5000 unless NEXT_PUBLIC_API_URL is set.
const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "production" ? "" : "http://localhost:5000")

function getApiUrl(path: string): string {
  const base = API_URL.replace(/\/$/, "")
  return `${base}${path}`
}

export class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "ApiError"
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(getApiUrl(path), {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    })
  } catch {
    throw new ApiError(
      API_URL
        ? `No se pudo conectar con el servidor. Verifica que el backend esté corriendo en ${API_URL}`
        : "No se pudo conectar con el servidor API. Intenta de nuevo en unos segundos.",
    )
  }

  let data: { ok?: boolean; error?: string }
  try {
    data = await res.json()
  } catch {
    throw new ApiError(`Respuesta inválida del servidor (${res.status}).`)
  }

  if (!res.ok || data.ok === false) {
    throw new ApiError(data.error ?? `Error del servidor (${res.status}).`)
  }

  return data as T
}

// ---------------------------------------------------------------------------
// Simulador de chat
// ---------------------------------------------------------------------------

interface SimularMensajeResponse {
  ok: true
  resultado: {
    intencion: string
    herramienta: string
    confianza: number
    escalado_revision_humana: boolean
    respuesta: string
    revision_humana_id: number | null
    detalle?: Record<string, unknown>
    conversacion_id?: number
  }
}

const VALID_INTENTS: Intent[] = ["cita", "cotizacion", "queja", "consulta_belleza", "otro"]

function mapIntent(intencion: string): Intent {
  if (intencion === "gestion_cita") return "cita"
  if (VALID_INTENTS.includes(intencion as Intent)) return intencion as Intent
  return "otro"
}

function mapConfidence(confianza: number): number {
  const value = confianza <= 1 ? confianza * 100 : confianza
  return Math.round(value)
}

export interface SimularMensajeResult {
  agentReply: string
  meta: AgentMeta
  conversacionId: number | null
}

export function mapSimularMensajeResultado(
  resultado: SimularMensajeResponse["resultado"],
): SimularMensajeResult {
  return {
    agentReply: resultado.respuesta,
    meta: {
      intent: mapIntent(resultado.intencion),
      tool: resultado.herramienta,
      confidence: mapConfidence(resultado.confianza),
      escalated: resultado.escalado_revision_humana,
    },
    conversacionId: resultado.conversacion_id ?? null,
  }
}

export async function simularMensaje(
  mensaje: string,
  conversacionId?: number | null,
) {
  const body: { mensaje: string; conversacion_id?: number } = { mensaje }
  if (conversacionId != null) {
    body.conversacion_id = conversacionId
  }
  const data = await apiFetch<SimularMensajeResponse>("/api/simular-mensaje", {
    method: "POST",
    body: JSON.stringify(body),
  })
  return mapSimularMensajeResultado(data.resultado)
}

// ---------------------------------------------------------------------------
// Campañas proactivas
// ---------------------------------------------------------------------------

interface BorradorProactivo {
  id: number
  titulo: string
  descripcion: string
  mensaje_respuesta: string
  origen: string
  metadata: {
    cliente_nombre?: string
    perfil?: string
    dias_inactivo?: number
  }
}

interface EjecutarSeguimientoResponse {
  ok: true
  resultado: {
    seguimiento: { borradores: BorradorProactivo[] }
    promociones?: { borradores: BorradorProactivo[] }
    total_borradores: number
  }
}

const VALID_PROFILES: ClientProfile[] = [
  "frecuente",
  "vip",
  "ocasional",
  "inactivo",
  "nuevo",
]

function mapProfile(perfil: string | undefined): ClientProfile {
  if (perfil && VALID_PROFILES.includes(perfil as ClientProfile)) {
    return perfil as ClientProfile
  }
  return "ocasional"
}

function mapBorradorToProactiveResult(borrador: BorradorProactivo): ProactiveResult {
  const { metadata } = borrador
  const dias = metadata.dias_inactivo

  let offer: string
  if (borrador.origen.includes("promocion")) {
    offer = `Promoción ${mapProfile(metadata.perfil)}`
  } else if (dias != null) {
    offer = `Seguimiento tras ${dias} días`
  } else {
    offer = borrador.titulo
  }

  let lastVisit: string
  if (dias != null) {
    lastVisit = `Hace ${dias} días`
  } else {
    lastVisit = borrador.descripcion
  }

  return {
    id: String(borrador.id),
    name: metadata.cliente_nombre ?? borrador.titulo,
    profile: mapProfile(metadata.perfil),
    lastVisit,
    message: borrador.mensaje_respuesta,
    offer,
  }
}

export async function ejecutarSeguimientoProactivo(): Promise<ProactiveResult[]> {
  const data = await apiFetch<EjecutarSeguimientoResponse>(
    "/api/ejecutar-seguimiento-proactivo",
    {
      method: "POST",
      body: JSON.stringify({ dias_umbral: 30, incluir_promociones: true }),
    },
  )

  const seguimiento = data.resultado.seguimiento?.borradores ?? []
  const promociones = data.resultado.promociones?.borradores ?? []
  return [...seguimiento, ...promociones].map(mapBorradorToProactiveResult)
}

// ---------------------------------------------------------------------------
// Bandeja de revisión humana
// ---------------------------------------------------------------------------

interface RevisionHumanaItem {
  id: number
  tipo: string
  origen: string
  titulo: string
  descripcion: string
  mensaje_cliente: string | null
  mensaje_respuesta: string
  prioridad: string
  metadata: {
    cliente_nombre?: string
    perfil?: string
    clasificacion?: { intencion?: string }
    intencion?: string
  }
  created_at: string
}

interface ListarRevisionResponse {
  ok: true
  total: number
  items: RevisionHumanaItem[]
}

function mapPriority(prioridad: string): Priority {
  if (prioridad === "alta") return "alta"
  if (prioridad === "baja") return "baja"
  return "media"
}

function mapOrigin(item: RevisionHumanaItem): TaskOrigin {
  if (item.tipo === "borrador_proactivo" || item.origen.startsWith("proactivo")) {
    return "proactivo"
  }
  return "conversacion"
}

function mapReviewIntent(item: RevisionHumanaItem): Intent {
  const raw =
    item.metadata.clasificacion?.intencion ??
    item.metadata.intencion ??
    (item.origen.includes("queja") ? "queja" : "otro")
  return mapIntent(raw)
}

function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate)
  const diffMs = Date.now() - date.getTime()
  const diffMin = Math.floor(diffMs / 60_000)

  if (diffMin < 1) return "Hace un momento"
  if (diffMin < 60) return `Hace ${diffMin} min`
  const diffHours = Math.floor(diffMin / 60)
  if (diffHours < 24) return `Hace ${diffHours} h`
  const diffDays = Math.floor(diffHours / 24)
  return `Hace ${diffDays} d`
}

function mapRevisionItemToTask(item: RevisionHumanaItem): ReviewTask {
  return {
    id: String(item.id),
    title: item.titulo,
    client: item.metadata.cliente_nombre ?? "Cliente",
    profile: mapProfile(item.metadata.perfil),
    priority: mapPriority(item.prioridad),
    origin: mapOrigin(item),
    intent: mapReviewIntent(item),
    detail: item.descripcion,
    proposed: item.mensaje_respuesta,
    time: formatRelativeTime(item.created_at),
  }
}

export async function listarRevisionPendiente(): Promise<ReviewTask[]> {
  const data = await apiFetch<ListarRevisionResponse>(
    "/api/revision-humana?estado=pendiente",
  )
  return data.items.map(mapRevisionItemToTask)
}

export async function aprobarRevision(id: string): Promise<void> {
  await apiFetch(`/api/revision-humana/${id}/aprobar`, { method: "POST" })
}

export async function descartarRevision(id: string): Promise<void> {
  await apiFetch(`/api/revision-humana/${id}/descartar`, { method: "POST" })
}
