import { useState, useEffect, useMemo } from 'react'
import { rolesService } from '@/services/roles.service'
import { permissionsService } from '@/services/permissions.service'
import { Search, Plus, Edit, Trash2, X, Check } from 'lucide-react'

export default function RolesPage() {
  const [roles, setRoles] = useState<any[]>([])
  const [allPermissions, setAllPermissions] = useState<any[]>([])
  
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<any>(null)
  
  const [isPermDrawerOpen, setIsPermDrawerOpen] = useState(false)
  const [selectedRole, setSelectedRole] = useState<any>(null)
  const [rolePermissions, setRolePermissions] = useState<Set<number>>(new Set())
  const [permSearch, setPermSearch] = useState('')

  useEffect(() => {
    loadRoles()
    loadPermissions()
  }, [])

  const loadRoles = async () => {
    try {
      const data = await rolesService.list()
      setRoles(data)
    } catch (e) { console.error(e) }
  }

  const loadPermissions = async () => {
    try {
      const data = await permissionsService.list()
      setAllPermissions(data)
    } catch (e) { console.error(e) }
  }

  const filteredRoles = useMemo(() => {
    // Скрываем роль admin из UI
    let result = roles.filter(r => r.name !== 'admin')
    if (search) {
      result = result.filter(r => r.name.toLowerCase().includes(search.toLowerCase()))
    }
    return result
  }, [roles, search])

  const filteredPerms = useMemo(() => {
    if (!permSearch) return allPermissions
    return allPermissions.filter(p => p.name.toLowerCase().includes(permSearch.toLowerCase()))
  }, [allPermissions, permSearch])

  const handleSaveRole = async (e: any) => {
    e.preventDefault()
    const name = e.target.roleName.value
    try {
      if (editingRole) {
        await rolesService.update(editingRole.id, { name })
      } else {
        await rolesService.create({ name })
      }
      setIsModalOpen(false)
      loadRoles()
    } catch (e) { console.error(e) }
  }

  const handleDelete = async (id: number) => {
    if (confirm("Rolni o'chirishni tasdiqlaysizmi?")) {
      try {
        await rolesService.delete(id)
        loadRoles()
      } catch (e) { console.error(e) }
    }
  }

  const openPermDrawer = (role: any) => {
    setSelectedRole(role)
    setRolePermissions(new Set(role.permissions.map((p: any) => p.id)))
    setIsPermDrawerOpen(true)
  }

  const togglePermission = (id: number) => {
    setRolePermissions(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const savePermissions = async () => {
    if (!selectedRole) return
    try {
      await rolesService.assignPermissions(selectedRole.id, Array.from(rolePermissions))
      setIsPermDrawerOpen(false)
      loadRoles()
    } catch (e) { console.error(e) }
  }

  return (
    <div className="p-6 relative">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Rollar</h1>
        <button 
          onClick={() => { setEditingRole(null); setIsModalOpen(true) }}
          className="bg-indigo-600 text-white px-4 py-2 rounded flex items-center hover:bg-indigo-700"
        >
          <Plus className="h-5 w-5 mr-2" /> Rol qo'shish
        </button>
      </div>

      <div className="mb-6 relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none sm:text-sm dark:bg-gray-800 dark:border-gray-700 dark:text-white"
          placeholder="Rol izlash..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden dark:bg-gray-800">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nomi</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Huquqlar soni</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700">
            {filteredRoles.map((role) => (
              <tr key={role.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer" onClick={() => openPermDrawer(role)}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{role.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{role.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{role.permissions?.length || 0}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button 
                    onClick={(e) => { e.stopPropagation(); setEditingRole(role); setIsModalOpen(true) }}
                    className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 mr-4"
                  >
                    <Edit className="h-5 w-5" />
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); handleDelete(role.id) }}
                    className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Role Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96">
            <h2 className="text-xl font-bold mb-4 dark:text-white">{editingRole ? 'Rolni tahrirlash' : 'Yangi rol'}</h2>
            <form onSubmit={handleSaveRole}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nomi</label>
                <input 
                  name="roleName"
                  defaultValue={editingRole?.name}
                  required
                  className="w-full border p-2 rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white" 
                />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 border rounded text-gray-600 dark:text-gray-300">Bekor qilish</button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">Saqlash</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Permissions Drawer */}
      {isPermDrawerOpen && selectedRole && (
        <div className="fixed inset-0 z-40 flex justify-end">
          <div className="absolute inset-0 bg-black/50" onClick={() => setIsPermDrawerOpen(false)} />
          <div className="relative w-96 bg-white dark:bg-gray-800 h-full shadow-xl flex flex-col z-50">
            <div className="p-4 border-b dark:border-gray-700 flex justify-between items-center">
              <h2 className="text-lg font-bold dark:text-white">"{selectedRole.name}" rolining huquqlari</h2>
              <button onClick={() => setIsPermDrawerOpen(false)}><X className="dark:text-white" /></button>
            </div>
            
            <div className="p-4 border-b dark:border-gray-700">
              <div className="relative">
                <Search className="absolute left-2 top-2 h-5 w-5 text-gray-400" />
                <input 
                  type="text" 
                  placeholder="Huquqlarni izlash..."
                  className="w-full pl-9 pr-3 py-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  value={permSearch}
                  onChange={e => setPermSearch(e.target.value)}
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-2">
                {filteredPerms.map(p => (
                  <label key={p.id} className="flex items-center gap-3 p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-600 h-4 w-4"
                      checked={rolePermissions.has(p.id)}
                      onChange={() => togglePermission(p.id)}
                    />
                    <span className="text-sm dark:text-gray-200">{p.name}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="p-4 border-t dark:border-gray-700">
              <button 
                onClick={savePermissions}
                className="w-full bg-indigo-600 text-white py-2 rounded flex items-center justify-center hover:bg-indigo-700"
              >
                <Check className="h-5 w-5 mr-2" /> Huquqlarni saqlash
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
