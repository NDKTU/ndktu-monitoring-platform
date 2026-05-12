import {
  Activity,
  AlarmClock,
  Camera,
  Clock4,
  ContactRound,
  LogOut,
  ShieldAlert,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/shared/PageHeader'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { todayIso } from '@/lib/time'
import { camerasService } from '@/services/cameras'
import { dailyAttendanceService } from '@/services/dailyAttendance'
import { employeesService } from '@/services/employees'

type CountStats = {
  cameras: number
  activeCameras: number
  employees: number
  employeesInWork: number
}

type DailyStats = {
  late: number
  earlyLeave: number
  totalHours: number
}

type StatCard = {
  label: string
  value: string | number
  icon: typeof Camera
}

export default function DashboardPage() {
  const [counts, setCounts] = useState<CountStats | null>(null)
  const [countsLoading, setCountsLoading] = useState(true)

  const [daily, setDaily] = useState<DailyStats | null>(null)
  const [dailyLoading, setDailyLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const fetchCounts = async () => {
      try {
        setCountsLoading(true)
        const [cams, allEmployees, workingEmployees] = await Promise.all([
          camerasService.list({ page: 1, limit: 100 }),
          employeesService.list({ page: 1, limit: 1 }),
          employeesService.list({ page: 1, limit: 1, in_work: true }),
        ])
        if (cancelled) return
        setCounts({
          cameras: cams.total,
          activeCameras: cams.cameras.filter((c) => c.is_active).length,
          employees: allEmployees.total,
          employeesInWork: workingEmployees.total,
        })
      } catch (err) {
        console.error('Failed to fetch counts', err)
      } finally {
        if (!cancelled) setCountsLoading(false)
      }
    }
    fetchCounts()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const fetchDaily = async () => {
      try {
        setDailyLoading(true)
        const today = todayIso()
        const res = await dailyAttendanceService.list({
          date_from: today,
          date_to: today,
          limit: 200,
        })
        if (cancelled) return
        const late = res.items.filter((i) => i.status === 'LATE_ARRIVAL').length
        const earlyLeave = res.items.filter(
          (i) =>
            i.status === 'EARLY_LEAVE' || i.status === 'LATE_AND_EARLY',
        ).length
        const totalHours = res.items.reduce(
          (sum, i) => sum + (i.total_working_hours ?? 0),
          0,
        )
        setDaily({ late, earlyLeave, totalHours })
      } catch (err) {
        console.error('Failed to fetch daily KPI', err)
      } finally {
        if (!cancelled) setDailyLoading(false)
      }
    }
    fetchDaily()
    return () => {
      cancelled = true
    }
  }, [])

  const countCards: StatCard[] = [
    { label: 'Jami kameralar', value: counts?.cameras ?? 0, icon: Camera },
    {
      label: 'Faol kameralar',
      value: counts?.activeCameras ?? 0,
      icon: Activity,
    },
    {
      label: 'Jami xodimlar',
      value: counts?.employees ?? 0,
      icon: ContactRound,
    },
    {
      label: 'Hozir ishda',
      value: counts?.employeesInWork ?? 0,
      icon: ShieldAlert,
    },
  ]

  const dailyCards: StatCard[] = [
    {
      label: 'Bugun kech kelganlar',
      value: daily?.late ?? 0,
      icon: AlarmClock,
    },
    {
      label: 'Erta ketganlar',
      value: daily?.earlyLeave ?? 0,
      icon: LogOut,
    },
    {
      label: 'Bugungi soat',
      value: daily ? daily.totalHours.toFixed(1) : '0.0',
      icon: Clock4,
    },
  ]

  return (
    <>
      <PageHeader
        title="Boshqaruv paneli"
        description="Tizim holati va xavfsizlik ko‘rsatkichlari"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {countCards.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="flex items-center gap-4">
              <div className="grid size-10 place-items-center rounded-md bg-muted text-foreground">
                <Icon className="size-5" aria-hidden />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {label}
                </div>
                {countsLoading ? (
                  <Skeleton className="mt-1 h-6 w-12" />
                ) : (
                  <div className="text-2xl font-semibold tabular-nums">
                    {value}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {dailyCards.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="flex items-center gap-4">
              <div className="grid size-10 place-items-center rounded-md bg-muted text-foreground">
                <Icon className="size-5" aria-hidden />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {label}
                </div>
                {dailyLoading ? (
                  <Skeleton className="mt-1 h-6 w-12" />
                ) : (
                  <div className="text-2xl font-semibold tabular-nums">
                    {value}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardContent className="flex h-72 flex-col items-center justify-center gap-3 border-dashed text-center text-muted-foreground">
          <Activity className="size-8 opacity-60" aria-hidden />
          <p className="text-sm">
            Real vaqt voqealar tasmasi bu yerda paydo bo‘ladi
          </p>
        </CardContent>
      </Card>
    </>
  )
}
