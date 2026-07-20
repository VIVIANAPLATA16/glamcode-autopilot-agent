"use client"

import { useRef, useState } from "react"
import {
  Send,
  Bot,
  User,
  Wrench,
  Gauge,
  ShieldCheck,
  Sparkles,
  Loader2,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { IntentBadge } from "@/components/meta-badges"
import { cn } from "@/lib/utils"
import { simularMensaje, ApiError } from "@/lib/api"
import type { AgentMeta } from "@/lib/agent-data"

interface ChatMessage {
  id: string
  role: "user" | "agent"
  text: string
  meta?: AgentMeta
}

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "agent",
  text: "¡Hola! Soy la asesora virtual del salón 💛 Con 20 años de experiencia en belleza integral te ayudo con consejos, precios, citas y lo que necesites. Escríbeme como si fueras una clienta por WhatsApp.",
  meta: { intent: "consulta_belleza", tool: "saludo_inicial", confidence: 99, escalated: false },
}

const SCENARIO_PROMPTS = [
  {
    label: "Consejo de belleza",
    userMessage: "Hola, tengo el cabello reseco después del tinte, ¿qué me recomiendas?",
  },
  { label: "Cotización simple", userMessage: "Hola, ¿cuánto cuesta un manicure tradicional?" },
  {
    label: "Cita ambigua",
    userMessage: "Quiero algo para el cabello el finde, no sé bien qué",
  },
  {
    label: "Queja de cliente",
    userMessage: "Estoy súper molesta, me dejaron el tinte manchado y me cobraron completo 😡",
  },
]

let idCounter = 0
const nextId = () => `m${++idCounter}`

function confidenceTone(confidence: number) {
  if (confidence >= 85) return "text-success"
  if (confidence >= 65) return "text-warning"
  return "text-destructive"
}

export function ChatSimulator() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversacionId, setConversacionId] = useState<number | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
    })
  }

  const send = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const userId = nextId()
    setMessages((prev) => [...prev, { id: userId, role: "user", text: trimmed }])
    setInput("")
    setLoading(true)
    setError(null)
    scrollToBottom()

    try {
      const response = await simularMensaje(trimmed, conversacionId)
      if (response.conversacionId != null) {
        setConversacionId(response.conversacionId)
      }
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "agent", text: response.agentReply, meta: response.meta },
      ])
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Ocurrió un error inesperado al procesar el mensaje."
      setError(message)
    } finally {
      setLoading(false)
      scrollToBottom()
    }
  }

  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
      {/* Header estilo WhatsApp */}
      <div className="flex items-center gap-3 border-b border-border bg-secondary/50 px-4 py-3">
        <span className="flex size-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <Bot className="size-5" aria-hidden="true" />
        </span>
        <div className="leading-tight">
          <p className="text-sm font-semibold">Salón Glam · Autopilot</p>
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span
              className={cn(
                "size-1.5 rounded-full",
                loading ? "animate-pulse bg-warning" : "bg-success",
              )}
              aria-hidden="true"
            />
            {loading ? "procesando…" : "en línea · responde al instante"}
          </p>
        </div>
      </div>

      {/* Mensajes */}
      <div
        ref={scrollRef}
        className="flex h-[460px] flex-col gap-4 overflow-y-auto px-4 py-5"
      >
        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="flex justify-end">
              <div className="flex max-w-[78%] items-end gap-2">
                <div className="rounded-2xl rounded-br-sm bg-primary px-3.5 py-2.5 text-sm text-primary-foreground">
                  {m.text}
                </div>
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
                  <User className="size-3.5" aria-hidden="true" />
                </span>
              </div>
            </div>
          ) : (
            <div key={m.id} className="flex flex-col gap-2">
              <div className="flex max-w-[85%] items-start gap-2">
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                  <Bot className="size-3.5" aria-hidden="true" />
                </span>
                <div className="rounded-2xl rounded-tl-sm border border-border bg-secondary/40 px-3.5 py-2.5 text-sm text-foreground">
                  {m.text}
                </div>
              </div>
              {m.meta && <AgentMetaPanel meta={m.meta} />}
            </div>
          ),
        )}

        {loading && (
          <div className="flex items-start gap-2">
            <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
              <Bot className="size-3.5" aria-hidden="true" />
            </span>
            <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm border border-border bg-secondary/40 px-3.5 py-2.5 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              El agente está pensando…
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mx-4 mb-2 flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2.5 text-xs text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Botones de ejemplo */}
      <div className="border-t border-border px-4 pt-3">
        <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          <Sparkles className="size-3.5 text-primary" aria-hidden="true" />
          Prueba un escenario:
        </p>
        <div className="flex flex-wrap gap-2">
          {SCENARIO_PROMPTS.map((s) => (
            <button
              key={s.label}
              type="button"
              disabled={loading}
              onClick={() => send(s.userMessage)}
              className="rounded-full border border-border bg-secondary/50 px-3 py-1.5 text-xs font-medium text-secondary-foreground transition-colors hover:border-primary/50 hover:text-primary disabled:opacity-50"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
        className="flex items-center gap-2 p-4"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe un mensaje como cliente…"
          className="h-11 rounded-full bg-background"
          aria-label="Mensaje del cliente"
          disabled={loading}
        />
        <Button
          type="submit"
          size="icon"
          className="size-11 shrink-0 rounded-full"
          disabled={!input.trim() || loading}
          aria-label="Enviar mensaje"
        >
          {loading ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <Send className="size-4" aria-hidden="true" />
          )}
        </Button>
      </form>
    </div>
  )
}

function AgentMetaPanel({ meta }: { meta: AgentMeta }) {
  return (
    <div className="ml-9 flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <IntentBadge intent={meta.intent} />
        <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground">
          <Wrench className="size-3.5" aria-hidden="true" />
          {meta.tool}
        </span>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border border-border bg-secondary px-2.5 py-1 text-xs font-medium",
            confidenceTone(meta.confidence),
          )}
        >
          <Gauge className="size-3.5" aria-hidden="true" />
          {meta.confidence}% de confianza
        </span>
      </div>

      {meta.escalated && (
        <div
          className="hitl-checkpoint relative overflow-hidden rounded-xl border border-primary/35 bg-gradient-to-r from-primary/12 via-card to-primary/8 px-3 py-2.5"
          role="status"
        >
          <span className="hitl-checkpoint-shimmer pointer-events-none absolute inset-0" aria-hidden="true" />
          <div className="relative flex items-start gap-2.5">
            <span className="hitl-checkpoint-orb mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full border border-primary/40 bg-primary/15 text-primary">
              <ShieldCheck className="size-3.5" aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-xs font-semibold tracking-wide text-primary">
                  Checkpoint humano activo
                </p>
                <span className="hitl-checkpoint-pulse inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-primary">
                  <span className="size-1.5 rounded-full bg-primary" aria-hidden="true" />
                  En cola
                </span>
              </div>
              <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                El agente pausó el flujo automático. Una coordinadora revisará y confirmará antes de
                responder al cliente.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
