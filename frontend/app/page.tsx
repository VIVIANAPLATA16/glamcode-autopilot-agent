import { CalendarClock, Tag, AlertTriangle, UserCog } from "lucide-react"
import { ChatSimulator } from "@/components/chat-simulator"

const CAPABILITIES = [
  {
    icon: CalendarClock,
    title: "Gestión de citas",
    desc: "Agenda, reagenda y confirma citas entendiendo el lenguaje natural del cliente.",
  },
  {
    icon: Tag,
    title: "Cotizaciones",
    desc: "Responde precios y servicios al instante desde el catálogo del salón.",
  },
  {
    icon: AlertTriangle,
    title: "Manejo de quejas",
    desc: "Detecta molestia, responde con empatía y prioriza el caso.",
  },
  {
    icon: UserCog,
    title: "Escalamiento humano",
    desc: "Cuando duda o el caso es delicado, lo deriva a una persona.",
  },
]

export default function Page() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <section className="mb-8 max-w-2xl">
        <span className="inline-flex items-center rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          Simulador de conversación
        </span>
        <h1 className="mt-4 text-pretty text-3xl font-semibold tracking-tight sm:text-4xl">
          Atiende clientes por WhatsApp con{" "}
          <span className="font-serif italic text-primary">inteligencia artificial</span>
        </h1>
        <p className="mt-3 text-pretty leading-relaxed text-muted-foreground">
          Escribe como si fueras un cliente del salón y observa cómo el agente responde. Junto a
          cada respuesta verás la intención detectada, la herramienta usada, el nivel de confianza y
          si el caso se escaló a revisión humana.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <ChatSimulator />

        <aside className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-muted-foreground">
            Qué resuelve el agente
          </h2>
          {CAPABILITIES.map((c) => {
            const Icon = c.icon
            return (
              <div
                key={c.title}
                className="flex gap-3 rounded-xl border border-border bg-card p-4"
              >
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
                  <Icon className="size-[18px]" aria-hidden="true" />
                </span>
                <div>
                  <p className="text-sm font-medium">{c.title}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{c.desc}</p>
                </div>
              </div>
            )
          })}
        </aside>
      </div>
    </main>
  )
}
