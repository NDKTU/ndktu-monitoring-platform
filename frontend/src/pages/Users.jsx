import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { userApi } from '../api';
import { Plus, Trash2, User, UserCheck, UserX, Search } from 'lucide-react';
import Modal from '../components/Modal';

const UsersList = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState('all');
  const [filterInWork, setFilterInWork] = useState('all');
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    is_active: true
  });

  const fetchUsers = async (search = '', isActive = 'all', inWork = 'all') => {
    try {
      setLoading(true);
      const params = { search, limit: 100 };
      if (isActive !== 'all') params.is_active = isActive === 'true';
      if (inWork !== 'all') params.in_work = inWork === 'true';
      
      const res = await userApi.list(params);
      setUsers(res.data.users);
    } catch (err) {
      console.error('Failed to fetch users', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchUsers(searchTerm, filterActive, filterInWork);
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, filterActive, filterInWork]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await userApi.create(formData);
      setIsModalOpen(false);
      setFormData({ username: '', password: '', is_active: true });
      fetchUsers();
    } catch (err) {
      alert('Error creating user');
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (window.confirm('Delete this user?')) {
      try {
        await userApi.delete(id);
        fetchUsers();
      } catch (err) {
        alert('Error deleting user');
      }
    }
  };

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 700 }}>Users</h1>
          <p style={{ color: 'var(--text-muted)' }}>Manage system users and access</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search 
              size={18} 
              style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} 
            />
            <input 
              type="text" 
              className="form-input" 
              placeholder="Search username..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '40px', width: '240px', marginBottom: 0 }}
            />
          </div>
          
          <select 
            className="form-input" 
            style={{ width: '150px', marginBottom: 0 }}
            value={filterActive}
            onChange={(e) => setFilterActive(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>

          <select 
            className="form-input" 
            style={{ width: '150px', marginBottom: 0 }}
            value={filterInWork}
            onChange={(e) => setFilterInWork(e.target.value)}
          >
            <option value="all">All Work</option>
            <option value="true">In Work</option>
            <option value="false">Off Work</option>
          </select>
          <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
            <Plus size={20} />
            Add User
          </button>
        </div>
      </div>

      <div className="glass-card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Username</th>
                <th>Status</th>
                <th>In Work</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="clickable" onClick={() => navigate(`/users/${user.id}`)}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{ padding: '0.5rem', background: 'var(--glass)', borderRadius: '0.5rem' }}>
                        <User size={18} />
                      </div>
                      {user.username}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${user.is_active ? 'badge-success' : 'badge-danger'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {user.in_work ? <UserCheck size={16} color="var(--success)" /> : <UserX size={16} color="var(--danger)" />}
                      {user.in_work ? 'Working' : 'Off'}
                    </div>
                  </td>
                  <td onClick={e => e.stopPropagation()}>
                    <button className="btn btn-danger" onClick={(e) => handleDelete(user.id, e)}>
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && !loading && (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No users found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create New User">
        <form onSubmit={handleCreate}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input 
              className="form-input" 
              required 
              value={formData.username} 
              onChange={e => setFormData({...formData, username: e.target.value})}
              placeholder="johndoe"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input 
              className="form-input" 
              type="password" 
              value={formData.password} 
              onChange={e => setFormData({...formData, password: e.target.value})}
              placeholder="Optional"
            />
          </div>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
            <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setIsModalOpen(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Create User</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default UsersList;
