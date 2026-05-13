import { useMemo, useState } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { Employee } from '@/types/employee'

type Props = {
  employees: Employee[]
  value: number[]
  onChange: (next: number[]) => void
}

export function EmployeeMultiSelect({ employees, value, onChange }: Props) {
  const [q, setQ] = useState('')

  const filtered = useMemo(() => {
    const lower = q.trim().toLowerCase()
    if (!lower) return employees
    return employees.filter(
      (e) =>
        e.full_name.toLowerCase().includes(lower) ||
        e.jshir.includes(lower),
    )
  }, [employees, q])

  const toggle = (id: number) =>
    onChange(
      value.includes(id) ? value.filter((v) => v !== id) : [...value, id],
    )

  const allFilteredSelected =
    filtered.length > 0 && filtered.every((e) => value.includes(e.id))

  const toggleAllFiltered = () => {
    if (allFilteredSelected) {
      const ids = new Set(filtered.map((e) => e.id))
      onChange(value.filter((id) => !ids.has(id)))
    } else {
      const merged = new Set(value)
      filtered.forEach((e) => merged.add(e.id))
      onChange(Array.from(merged))
    }
  }

  return (
    <div className="space-y-2">
      <Input
        placeholder="Qidirish..."
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <div className="max-h-56 space-y-1 overflow-y-auto rounded-md border p-2">
        {filtered.length === 0 ? (
          <p className="py-2 text-center text-sm text-muted-foreground">
            Xodim topilmadi
          </p>
        ) : (
          <>
            <Label
              htmlFor="ems-select-all"
              className="flex cursor-pointer items-center gap-2 border-b pb-2 text-sm font-medium"
            >
              <Checkbox
                id="ems-select-all"
                checked={allFilteredSelected}
                onCheckedChange={toggleAllFiltered}
              />
              <span>Hammasini tanlash</span>
            </Label>
            {filtered.map((emp) => (
              <Label
                key={emp.id}
                htmlFor={`ems-emp-${emp.id}`}
                className="flex cursor-pointer items-center gap-2 py-1"
              >
                <Checkbox
                  id={`ems-emp-${emp.id}`}
                  checked={value.includes(emp.id)}
                  onCheckedChange={() => toggle(emp.id)}
                />
                <span>{emp.full_name}</span>
              </Label>
            ))}
          </>
        )}
      </div>
      <p className="text-xs text-muted-foreground">{value.length} tanlandi</p>
    </div>
  )
}
