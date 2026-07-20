"use client"

import { useState } from "react"
import { Megaphone, Loader2, Gift, Clock, RotateCcw, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ProfileBadge } from "@/components/meta-badges"
import { ejecutarSeguimientoProactivo, ApiError } from "@/lib/api"
import type { ProactiveResult } from "@/lib/agent-data"

type Status = "idle" | "running" | "done" | "error"

export default function ProactivoPage() {
  const [status, setStatus] = useState<Status>("idle")
  const [results, setResults] = useState<ProactiveResult[]>([])
  const [error, setError] = useState<string | null>(null)

  const runCampaign = async () => {
    setStatus("running")
    setResults([])
    setError(null)

    try {
      const borradores = await ejecutarSeguimientoProactivo()
      setResults(borradores)
      setStatus("done")
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Ocurrió un error inesperado al ejecutar la campaña.",
      )
      setStatus("error")
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <section className="mb-8 max-w-2xl">
        <span className="inline-flex items-center rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          Campañas proactivas
        </span>
        <h1 className="mt-4 text-pretty text-3xl font-semibold tracking-tight sm:text-4xl">
          Reactiva clientes con{" "}
          <span className="font-serif italic text-primary">mensajes personalizados</span>
        </h1>
        <p className="mt-3 text-pretty leading-relaxed text-muted-foreground">
          El agente analiza tu base de clientes, detecta a quienes llevan tiempo sin volver y genera
          un mensaje de seguimiento con una promoción a la medida de cada perfil.
        </p>
      </section>

      <div className="mb-8 flex flex-wrap items-center gap-4 rounded-2xl border border-border bg-card p-5">
        <span className="flex size-11 items-center justify-center rounded-xl bg-primary/15 text-primary">
          <Megaphone className="size-5" aria-hidden="true" />
        </span>
        <div className="flex-1">
          <p className="text-sm font-medium">Campaña de reactivación</p>
          <p className="text-xs text-muted-foreground">
            Analiza clientes inactivos y genera promociones personalizadas.
          </p>
        </div>
        <Button onClick={runCampaign} disabled={status === "running"} className="gap-2">
          {status === "running" ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              Analizando…
            </>
          ) : status === "done" || status === "error" ? (
            <>
              <RotateCcw className="size-4" aria-hidden="true" />
              Volver a ejecutar
            </>
          ) : (
            <>
              <Megaphone className="size-4" aria-hidden="true" />
              Disparar campaña
            </>
          )}
        </Button>
      </div>

      {error && (
        <div className="mb-4 flex items-start gap-2 rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {status === "done" && (
        <p className="mb-4 text-sm text-muted-foreground">
          Se generaron{" "}
          <span className="font-semibold text-foreground">{results.length} mensajes</span>{" "}
          personalizados. Revísalos y apruébalos en la bandeja de revisión antes de enviar.
        </p>
      )}

      {status === "idle" && (
        <div className="rounded-2xl border border-dashed border-border bg-card/40 py-16 text-center">
          <Megaphone className="mx-auto size-8 text-muted-foreground" aria-hidden="true" />
          <p className="mt-3 text-sm text-muted-foreground">
            Dispara la campaña para ver los mensajes generados por la IA.
          </p>
        </div>
      )}

      {status === "running" && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-52 animate-pulse rounded-2xl border border-border bg-card/60"
            />
          ))}
        </div>
      )}

      {status === "done" && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((r) => (
            <article
              key={r.id}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-5"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium">{r.name}</p>
                  <p className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="size-3" aria-hidden="true" />
                    {r.lastVisit}
                  </p>
                </div>
                <ProfileBadge profile={r.profile} />
              </div>

              <p className="rounded-xl border border-border bg-secondary/40 p-3 text-sm leading-relaxed text-foreground">
                {r.message}
              </p>

              <div className="mt-auto flex items-center gap-2 text-xs font-medium text-primary">
                <Gift className="size-3.5" aria-hidden="true" />
                {r.offer}
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  )
}
