"use client"

import { useCallback, useEffect, useState } from "react"
import {
  Check,
  X,
  MessageCircle,
  Megaphone,
  ShieldCheck,
  Sparkles,
  Inbox,
  Loader2,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { IntentBadge, PriorityBadge, ProfileBadge } from "@/components/meta-badges"
import { cn } from "@/lib/utils"
import {
  listarRevisionPendiente,
  aprobarRevision,
  descartarRevision,
  ApiError,
} from "@/lib/api"
import type { ReviewTask, TaskOrigin } from "@/lib/agent-data"

const ORIGIN_META: Record<
  TaskOrigin,
  { label: string; icon: typeof MessageCircle; className: string }
> = {
  conversacion: {
    label: "Conversación en vivo",
    icon: MessageCircle,
    className: "border-chart-4/40 bg-chart-4/10 text-chart-4",
  },
  proactivo: {
    label: "Borrador proactivo",
    icon: Megaphone,
    className: "border-primary/40 bg-primary/10 text-primary",
  },
}

export default function RevisionPage() {
  const [tasks, setTasks] = useState<ReviewTask[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const fetchTasks = useCallback(async () => {
    setError(null)
    try {
      const items = await listarRevisionPendiente()
      setTasks(items)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Ocurrió un error inesperado al cargar la bandeja.",
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const handleAction = async (id: string, action: "aprobar" | "descartar") => {
    setActionLoading(id)
    setError(null)
    try {
      if (action === "aprobar") {
        await aprobarRevision(id)
      } else {
        await descartarRevision(id)
      }
      await fetchTasks()
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : `No se pudo ${action === "aprobar" ? "aprobar" : "descartar"} el item.`,
      )
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <section className="mb-8">
        <span className="inline-flex items-center rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          Revisión humana
        </span>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-2xl">
            <h1 className="text-pretty text-3xl font-semibold tracking-tight sm:text-4xl">
              Bandeja de{" "}
              <span className="font-serif italic text-primary">aprobación</span>
            </h1>
            <p className="mt-3 text-pretty leading-relaxed text-muted-foreground">
              Casos y mensajes que el agente derivó a una persona: quejas prioritarias, citas
              ambiguas y borradores proactivos que esperan tu visto bueno antes de enviarse.
            </p>
          </div>
          <div className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3">
            <span className="flex size-10 items-center justify-center rounded-lg bg-primary/15 text-primary">
              {loading ? (
                <Loader2 className="size-5 animate-spin" aria-hidden="true" />
              ) : (
                <Inbox className="size-5" aria-hidden="true" />
              )}
            </span>
            <div className="leading-none">
              <p className="text-2xl font-semibold tabular-nums">
                {loading ? "—" : tasks.length}
              </p>
              <p className="text-xs text-muted-foreground">pendientes</p>
            </div>
          </div>
        </div>
      </section>

      {error && (
        <div className="mb-4 flex items-start gap-2 rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex flex-col gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-64 animate-pulse rounded-2xl border border-border bg-card/60"
            />
          ))}
        </div>
      ) : tasks.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border bg-card/40 py-16 text-center">
          <ShieldCheck className="mx-auto size-8 text-success" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium">¡Bandeja al día!</p>
          <p className="text-sm text-muted-foreground">
            No quedan tareas pendientes de revisión.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {tasks.map((task) => (
            <ReviewCard
              key={task.id}
              task={task}
              actionLoading={actionLoading === task.id}
              onAprobar={() => handleAction(task.id, "aprobar")}
              onDescartar={() => handleAction(task.id, "descartar")}
            />
          ))}
        </div>
      )}
    </main>
  )
}

function ReviewCard({
  task,
  actionLoading,
  onAprobar,
  onDescartar,
}: {
  task: ReviewTask
  actionLoading: boolean
  onAprobar: () => void
  onDescartar: () => void
}) {
  const origin = ORIGIN_META[task.origin]
  const OriginIcon = origin.icon
  const isHighPriority = task.priority === "alta"

  return (
    <article
      className={cn(
        "rounded-2xl border bg-card p-5",
        isHighPriority ? "border-destructive/40 ring-1 ring-destructive/20" : "border-border",
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <PriorityBadge priority={task.priority} />
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
            origin.className,
          )}
        >
          <OriginIcon className="size-3.5" aria-hidden="true" />
          {origin.label}
        </span>
        <IntentBadge intent={task.intent} />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <h2 className="text-base font-semibold">{task.title}</h2>
        <span className="text-xs text-muted-foreground">· {task.time}</span>
      </div>

      <div className="mt-1 flex items-center gap-2">
        <span className="text-sm text-muted-foreground">{task.client}</span>
        <ProfileBadge profile={task.profile} />
      </div>

      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{task.detail}</p>

      <div className="mt-3 rounded-xl border border-border bg-secondary/40 p-3">
        <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-primary">
          <Sparkles className="size-3.5" aria-hidden="true" />
          Acción propuesta por la IA
        </p>
        <p className="text-sm leading-relaxed text-foreground">{task.proposed}</p>
      </div>

      <div className="mt-4 flex gap-2">
        <Button
          onClick={onAprobar}
          disabled={actionLoading}
          className="flex-1 gap-2"
        >
          {actionLoading ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <Check className="size-4" aria-hidden="true" />
          )}
          Aprobar
        </Button>
        <Button
          onClick={onDescartar}
          disabled={actionLoading}
          variant="outline"
          className="flex-1 gap-2"
        >
          {actionLoading ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <X className="size-4" aria-hidden="true" />
          )}
          Descartar
        </Button>
      </div>
    </article>
  )
}
