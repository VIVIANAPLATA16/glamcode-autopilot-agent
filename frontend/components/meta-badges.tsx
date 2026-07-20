import {
  CalendarClock,
  Tag,
  AlertTriangle,
  MessageCircle,
  type LucideIcon,
} from "lucide-react"
import { cn } from "@/lib/utils"
import {
  INTENT_LABELS,
  PROFILE_LABELS,
  PRIORITY_LABELS,
  type Intent,
  type ClientProfile,
  type Priority,
} from "@/lib/agent-data"

const INTENT_ICONS: Record<Intent, LucideIcon> = {
  cita: CalendarClock,
  cotizacion: Tag,
  queja: AlertTriangle,
  otro: MessageCircle,
}

export function IntentBadge({ intent }: { intent: Intent }) {
  const Icon = INTENT_ICONS[intent]
  const isComplaint = intent === "queja"
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        isComplaint
          ? "border-destructive/40 bg-destructive/10 text-destructive"
          : "border-border bg-secondary text-secondary-foreground",
      )}
    >
      <Icon className="size-3.5" aria-hidden="true" />
      {INTENT_LABELS[intent]}
    </span>
  )
}

const PROFILE_STYLES: Record<ClientProfile, string> = {
  vip: "border-primary/50 bg-primary/15 text-primary",
  frecuente: "border-success/40 bg-success/10 text-success",
  ocasional: "border-border bg-secondary text-secondary-foreground",
  inactivo: "border-muted-foreground/30 bg-muted text-muted-foreground",
  nuevo: "border-chart-4/40 bg-chart-4/10 text-chart-4",
}

export function ProfileBadge({ profile }: { profile: ClientProfile }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium capitalize",
        PROFILE_STYLES[profile],
      )}
    >
      {PROFILE_LABELS[profile]}
    </span>
  )
}

const PRIORITY_STYLES: Record<Priority, string> = {
  alta: "border-destructive/40 bg-destructive/10 text-destructive",
  media: "border-warning/40 bg-warning/10 text-warning",
  baja: "border-border bg-secondary text-secondary-foreground",
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        PRIORITY_STYLES[priority],
      )}
    >
      <span
        className={cn(
          "size-1.5 rounded-full",
          priority === "alta" && "bg-destructive",
          priority === "media" && "bg-warning",
          priority === "baja" && "bg-muted-foreground",
        )}
        aria-hidden="true"
      />
      {PRIORITY_LABELS[priority]}
    </span>
  )
}
