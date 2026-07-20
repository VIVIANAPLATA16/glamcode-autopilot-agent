// ---------------------------------------------------------------------------
// Tipos compartidos del agente GlamCode Autopilot
// ---------------------------------------------------------------------------

export type Intent = "cita" | "cotizacion" | "queja" | "otro"

export type ClientProfile = "frecuente" | "vip" | "ocasional" | "inactivo" | "nuevo"

export type Priority = "alta" | "media" | "baja"

export type TaskOrigin = "conversacion" | "proactivo"

export interface AgentMeta {
  intent: Intent
  /** Herramienta interna usada para resolver el caso */
  tool: string
  /** 0 - 100 */
  confidence: number
  /** Si el caso se derivó a un humano */
  escalated: boolean
}

export interface ChatScenario {
  /** Texto del botón de ejemplo */
  label: string
  /** Mensaje que "escribe" el cliente */
  userMessage: string
  /** Respuesta del agente */
  agentReply: string
  meta: AgentMeta
}

// ---------------------------------------------------------------------------
// Metadatos de intención (para etiquetas visuales)
// ---------------------------------------------------------------------------

export const INTENT_LABELS: Record<Intent, string> = {
  cita: "Gestión de cita",
  cotizacion: "Cotización",
  queja: "Queja",
  otro: "Otro",
}

export const PROFILE_LABELS: Record<ClientProfile, string> = {
  frecuente: "Frecuente",
  vip: "VIP",
  ocasional: "Ocasional",
  inactivo: "Inactivo",
  nuevo: "Nuevo",
}

export const PRIORITY_LABELS: Record<Priority, string> = {
  alta: "Prioridad alta",
  media: "Prioridad media",
  baja: "Prioridad baja",
}

// ---------------------------------------------------------------------------
// Simulador de chat — escenarios precargados
// ---------------------------------------------------------------------------

export const CHAT_SCENARIOS: ChatScenario[] = [
  {
    label: "Cotización simple",
    userMessage: "Hola, ¿cuánto cuesta un manicure semipermanente?",
    agentReply:
      "¡Hola! 💅 El manicure semipermanente tiene un valor de $45.000 COP e incluye limado, cutícula y esmaltado que dura hasta 3 semanas. Si quieres te agendo una cita, tengo disponibilidad mañana a las 10:00 a.m. o 3:00 p.m. ¿Te sirve alguna?",
    meta: {
      intent: "cotizacion",
      tool: "catalogo_precios",
      confidence: 97,
      escalated: false,
    },
  },
  {
    label: "Cita ambigua",
    userMessage: "Quiero algo para el cabello el finde, no sé bien qué",
    agentReply:
      "¡Claro que sí! Para recomendarte mejor, ¿buscas corte, color, tratamiento o peinado? Y cuando dices el finde, ¿prefieres sábado o domingo? Con eso reviso la agenda y te propongo un horario ideal.",
    meta: {
      intent: "cita",
      tool: "clarificacion_agenda",
      confidence: 58,
      escalated: true,
    },
  },
  {
    label: "Queja de cliente",
    userMessage:
      "Estoy súper molesta, me dejaron el tinte manchado y me cobraron completo 😡",
    agentReply:
      "Lamento muchísimo lo que pasó, entiendo tu molestia y quiero ayudarte a resolverlo. He registrado tu caso como prioritario y una de nuestras coordinadoras te contactará hoy mismo para ofrecerte una corrección sin costo. Gracias por darnos la oportunidad de arreglarlo.",
    meta: {
      intent: "queja",
      tool: "gestion_incidencias",
      confidence: 91,
      escalated: true,
    },
  },
  {
    label: "Reagendar cita",
    userMessage: "Necesito mover mi cita del jueves para la otra semana",
    agentReply:
      "¡Con gusto! Veo tu cita de corte y cepillado para el jueves a las 2:00 p.m. Tengo disponible el martes a las 11:00 a.m. o el miércoles a las 4:00 p.m. de la próxima semana. ¿Cuál prefieres para confirmar el cambio?",
    meta: {
      intent: "cita",
      tool: "reagendamiento_citas",
      confidence: 94,
      escalated: false,
    },
  },
]

/** Respuesta genérica cuando el mensaje no coincide con un escenario */
export function inferAgentResponse(message: string): { agentReply: string; meta: AgentMeta } {
  const text = message.toLowerCase()

  const has = (words: string[]) => words.some((w) => text.includes(w))

  if (has(["precio", "cuánto", "cuanto", "vale", "cuesta", "cotiza", "cotización"])) {
    return {
      agentReply:
        "¡Con gusto te cotizo! Nuestros servicios van desde $25.000 COP. Cuéntame qué servicio te interesa (uñas, cabello, cejas o maquillaje) y te doy el precio exacto y la disponibilidad.",
      meta: { intent: "cotizacion", tool: "catalogo_precios", confidence: 82, escalated: false },
    }
  }

  if (has(["queja", "molesta", "molesto", "mal", "reclamo", "pésimo", "terrible", "cobraron"])) {
    return {
      agentReply:
        "Lamento mucho lo sucedido. He marcado tu caso como prioritario y lo derivé a una coordinadora humana para que te contacte y lo resuelva lo antes posible.",
      meta: { intent: "queja", tool: "gestion_incidencias", confidence: 88, escalated: true },
    }
  }

  if (has(["cita", "agendar", "reservar", "cupo", "reagendar", "cancelar", "horario"])) {
    return {
      agentReply:
        "¡Claro! Cuéntame qué servicio quieres y el día que prefieres, y reviso la agenda para proponerte el mejor horario disponible.",
      meta: { intent: "cita", tool: "clarificacion_agenda", confidence: 71, escalated: false },
    }
  }

  return {
    agentReply:
      "¡Gracias por escribir a nuestro salón! 💛 Cuéntame un poco más sobre lo que necesitas (una cita, un precio o alguna inquietud) y con gusto te ayudo.",
    meta: { intent: "otro", tool: "conversacion_general", confidence: 63, escalated: false },
  }
}

// ---------------------------------------------------------------------------
// Campañas proactivas — clientes + mensajes generados
// ---------------------------------------------------------------------------

export interface ProactiveResult {
  id: string
  name: string
  profile: ClientProfile
  lastVisit: string
  message: string
  offer: string
}

export const PROACTIVE_RESULTS: ProactiveResult[] = [
  {
    id: "p1",
    name: "Valentina Ospina",
    profile: "vip",
    lastVisit: "Hace 2 meses",
    offer: "20% en tratamiento capilar",
    message:
      "Hola Valentina 💛 Te extrañamos en el salón. Como clienta VIP tienes un 20% en nuestro tratamiento de keratina esta semana. ¿Te reservo tu cupo del sábado?",
  },
  {
    id: "p2",
    name: "Camila Restrepo",
    profile: "frecuente",
    lastVisit: "Hace 6 semanas",
    offer: "Manicure + pedicure combo",
    message:
      "¡Hola Camila! Ya casi es hora de tu manicure mensual 💅 Esta quincena tenemos el combo manos + pies con precio especial. ¿Agendamos como siempre los viernes?",
  },
  {
    id: "p3",
    name: "Daniela Gómez",
    profile: "inactivo",
    lastVisit: "Hace 7 meses",
    offer: "Corte + cepillado de regreso",
    message:
      "Hola Daniela, ¡hace rato no te vemos! Queremos consentirte con un corte + cepillado de bienvenida a mitad de precio. Tu cabello merece un cambio ✨ ¿Te gustaría venir esta semana?",
  },
  {
    id: "p4",
    name: "Andrea Marín",
    profile: "ocasional",
    lastVisit: "Hace 3 meses",
    offer: "Diseño de cejas gratis",
    message:
      "¡Hola Andrea! Gracias por confiar en nosotras. Este mes, al reservar cualquier servicio, el diseño de cejas va por nuestra cuenta. ¿Aprovechamos el fin de semana?",
  },
  {
    id: "p5",
    name: "Sofía Cardona",
    profile: "nuevo",
    lastVisit: "Primera visita hace 3 semanas",
    offer: "Bono de bienvenida",
    message:
      "¡Hola Sofía! Fue un placer atenderte en tu primera visita 💛 Te dejamos un bono de $15.000 para tu próxima cita. ¿Te ayudo a agendarla?",
  },
  {
    id: "p6",
    name: "Laura Betancur",
    profile: "frecuente",
    lastVisit: "Hace 5 semanas",
    offer: "Color + brillo profesional",
    message:
      "¡Hola Laura! Notamos que tu color ya pide un retoque 😉 Esta semana el servicio de color incluye tratamiento de brillo sin costo. ¿Te reservo el horario de siempre?",
  },
]

// ---------------------------------------------------------------------------
// Bandeja de revisión humana
// ---------------------------------------------------------------------------

export interface ReviewTask {
  id: string
  title: string
  client: string
  profile: ClientProfile
  priority: Priority
  origin: TaskOrigin
  intent: Intent
  detail: string
  /** Mensaje/acción propuesta por la IA que espera aprobación */
  proposed: string
  time: string
}

export const REVIEW_TASKS: ReviewTask[] = [
  {
    id: "r1",
    title: "Queja por servicio de tinte",
    client: "Mariana López",
    profile: "frecuente",
    priority: "alta",
    origin: "conversacion",
    intent: "queja",
    detail:
      "La clienta reporta un tinte manchado y cobro completo. El agente escaló el caso por sensibilidad emocional alta.",
    proposed:
      "Ofrecer corrección sin costo + 30% de descuento en próximo servicio y llamada de una coordinadora hoy.",
    time: "Hace 8 min",
  },
  {
    id: "r2",
    title: "Cita ambigua sin confirmar",
    client: "Juliana Vélez",
    profile: "ocasional",
    priority: "media",
    origin: "conversacion",
    intent: "cita",
    detail:
      "El cliente pidió 'algo para el cabello el finde' sin especificar servicio ni día. Confianza del agente: 58%.",
    proposed:
      "Confirmar manualmente: proponer corte + tratamiento el sábado a las 10:00 a.m.",
    time: "Hace 21 min",
  },
  {
    id: "r3",
    title: "Promoción VIP pendiente de envío",
    client: "Valentina Ospina",
    profile: "vip",
    priority: "media",
    origin: "proactivo",
    intent: "otro",
    detail:
      "Mensaje generado por la campaña proactiva de reactivación de clientas VIP inactivas.",
    proposed:
      "Enviar: '20% en tratamiento de keratina esta semana, ¿te reservo el sábado?'",
    time: "Hace 35 min",
  },
  {
    id: "r4",
    title: "Seguimiento a clienta inactiva",
    client: "Daniela Gómez",
    profile: "inactivo",
    priority: "baja",
    origin: "proactivo",
    intent: "otro",
    detail:
      "Borrador de reactivación tras 7 meses sin visitas. Incluye descuento de bienvenida.",
    proposed:
      "Enviar: 'Corte + cepillado de bienvenida a mitad de precio, ¿vienes esta semana?'",
    time: "Hace 1 h",
  },
  {
    id: "r5",
    title: "Reclamo por demora en la atención",
    client: "Paola Henao",
    profile: "frecuente",
    priority: "alta",
    origin: "conversacion",
    intent: "queja",
    detail:
      "La clienta esperó 40 minutos más de lo agendado. El agente detectó insatisfacción y escaló.",
    proposed:
      "Ofrecer disculpas + servicio express gratis y priorizar su próxima cita.",
    time: "Hace 1 h",
  },
]
