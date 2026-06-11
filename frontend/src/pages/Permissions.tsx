import { useState, useEffect, useMemo } from 'react'
import { permissionsService } from '@/services/permissions.service'
import { Search, ChevronDown, ChevronRight } from 'lucide-react'

export default function PermissionsPage() {
  const [permissions, setPermissions] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [expandedModules, setExpandedModules] = useState<Record<string, boolean>>({})

  useEffect(() => {
    loadPermissions()
  }, [])

  const loadPermissions = async () => {
    try {
      const data = await permissionsService.list()
      setPermissions(data)
    } catch (error) {
      console.error(error)
    }
  }

  // filter by search
  const filtered = useMemo(() => {
    if (!search) return permissions
    return permissions.filter(p => p.name.toLowerCase().includes(search.toLowerCase()))
  }, [permissions, search])

  // group by module (e.g. "users:create" -> "users")
  const grouped = useMemo(() => {
    const map: Record<string, any[]> = {}
    filtered.forEach(p => {
      const [mod] = p.name.split(':')
      if (!map[mod]) map[mod] = []
      map[mod].push(p)
    })
    return map
  }, [filtered])

  const toggleModule = (mod: string) => {
    setExpandedModules(prev => ({ ...prev, [mod]: !prev[mod] }))
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Kirish huquqlari</h1>
      
      <div className="mb-6 relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-800 dark:border-gray-700 dark:text-white"
          placeholder="Huquqlarni izlash..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="bg-white shadow rounded-lg dark:bg-gray-800 overflow-hidden">
        <ul className="divide-y divide-gray-200 dark:divide-gray-700">
          {Object.entries(grouped).map(([mod, perms]) => (
            <li key={mod}>
              <div 
                className="px-4 py-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
                onClick={() => toggleModule(mod)}
              >
                <div className="flex items-center">
                  {expandedModules[mod] ? (
                    <ChevronDown className="h-5 w-5 text-gray-400 mr-2" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-gray-400 mr-2" />
                  )}
                  <span className="text-sm font-medium text-gray-900 dark:text-white uppercase">
                    {mod}
                  </span>
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {perms.length} huquq
                </span>
              </div>
              
              {expandedModules[mod] && (
                <div className="bg-gray-50 dark:bg-gray-900 px-8 py-3">
                  <ul className="space-y-2">
                    {perms.map(p => (
                      <li key={p.id} className="text-sm text-gray-700 dark:text-gray-300 flex justify-between">
                        <span>{p.name}</span>
                        <span className="text-xs text-gray-400">ID: {p.id}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </li>
          ))}
          {Object.keys(grouped).length === 0 && (
            <li className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
              Hech narsa topilmadi
            </li>
          )}
        </ul>
      </div>
    </div>
  )
}
