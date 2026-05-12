import {
  CalendarCheck,
  Camera,
  Clock,
  ContactRound,
  LayoutDashboard,
  ShieldCheck,
  UserCog,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { to: '/', label: 'Boshqaruv', icon: LayoutDashboard, end: true },
  { to: '/cameras', label: 'Kameralar', icon: Camera, end: false },
  { to: '/employees', label: 'Xodimlar', icon: ContactRound, end: false },
  {
    to: '/daily-attendance',
    label: 'Davomat',
    icon: CalendarCheck,
    end: false,
  },
  {
    to: '/work-schedules',
    label: 'Ish jadvallari',
    icon: Clock,
    end: false,
  },
  { to: '/users', label: 'Foydalanuvchilar', icon: UserCog, end: false },
]

type SidebarProps = {
  onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
  return (
    <div className="flex h-full flex-col gap-6 bg-sidebar text-sidebar-foreground">
      <div className="flex items-center gap-2 px-5 pt-6">
        <div className="grid size-8 place-items-center rounded-md bg-primary text-primary-foreground">
          <ShieldCheck className="size-4" aria-hidden />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold">NDKTU</div>
          <div className="text-xs text-muted-foreground">Monitoring</div>
        </div>
      </div>

      <nav aria-label="Asosiy navigatsiya" className="flex-1 px-3">
        <ul className="flex flex-col gap-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                      : 'text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground',
                  )
                }
              >
                <Icon className="size-4" aria-hidden />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="px-5 pb-6">
        <div className="rounded-md border border-sidebar-border bg-background/40 p-3 text-xs text-muted-foreground">
          Kirish nazorati va videokuzatuv tizimi.
        </div>
      </div>
    </div>
  )
}
