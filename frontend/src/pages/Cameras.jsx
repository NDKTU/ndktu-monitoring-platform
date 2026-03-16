import React, { useState, useEffect } from 'react';
import { cameraApi, userEventApi } from '../api';
import { Plus, Trash2, Camera, ExternalLink, RefreshCw, Power, PowerOff, Activity } from 'lucide-react';
import Modal from '../components/Modal';

const Cameras = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [cameraEvents, setCameraEvents] = useState([]);
  const [eventsLoading, setEventsLoading] = useState(false);

  const fetchCameraEvents = async (cameraId) => {
    try {
      setEventsLoading(true);
      const res = await userEventApi.list({ camera_id: cameraId, limit: 5 });
      setCameraEvents(res.data.events);
    } catch (err) {
      console.error('Failed to fetch camera events', err);
    } finally {
      setEventsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCamera) {
      fetchCameraEvents(selectedCamera.id);
    } else {
      setCameraEvents([]);
    }
  }, [selectedCamera]);
  const [formData, setFormData] = useState({
    device_ip: '',
    username: '',
    password: '',
    direction: 'enter',
    is_active: true
  });

  const fetchCameras = async () => {
    try {
      setLoading(true);
      const res = await cameraApi.list({ limit: 100 });
      setCameras(res.data.cameras);
    } catch (err) {
      console.error('Failed to fetch cameras', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await cameraApi.create(formData);
      setIsModalOpen(false);
      setFormData({ device_ip: '', username: '', password: '', direction: 'enter', is_active: true });
      fetchCameras();
    } catch (err) {
      alert('Error creating camera');
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (window.confirm('Delete this camera?')) {
      try {
        await cameraApi.delete(id);
        fetchCameras();
      } catch (err) {
        alert('Error deleting camera');
      }
    }
  };

  const handleToggleConnect = async (camera, e) => {
    e.stopPropagation();
    try {
      if (camera.is_active) {
        await cameraApi.disconnect(camera.id);
      } else {
        await cameraApi.connect(camera.id);
      }
      fetchCameras();
    } catch (err) {
      alert('Connection error');
    }
  };

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 700 }}>Cameras</h1>
          <p style={{ color: 'var(--text-muted)' }}>Manage your surveillance network</p>
        </div>
        <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
          <Plus size={20} />
          Add Camera
        </button>
      </div>

      <div className="glass-card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>IP Address</th>
                <th>Username</th>
                <th>Direction</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {cameras.map((camera) => (
                <tr key={camera.id} className="clickable" onClick={() => setSelectedCamera(camera)}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{ padding: '0.5rem', background: 'var(--glass)', borderRadius: '0.5rem' }}>
                        <Camera size={18} />
                      </div>
                      {camera.device_ip}
                    </div>
                  </td>
                  <td>{camera.username}</td>
                  <td>
                    <span className={`badge ${camera.direction === 'enter' ? 'badge-success' : 'badge-danger'}`} style={{ textTransform: 'capitalize' }}>
                      {camera.direction}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${camera.is_active ? 'badge-success' : 'badge-danger'}`}>
                      {camera.is_active ? 'Connected' : 'Disconnected'}
                    </span>
                  </td>
                  <td onClick={e => e.stopPropagation()}>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn btn-ghost" onClick={(e) => handleToggleConnect(camera, e)} title={camera.is_active ? 'Disconnect' : 'Connect'}>
                        {camera.is_active ? <PowerOff size={18} /> : <Power size={18} />}
                      </button>
                      <button className="btn btn-danger" onClick={(e) => handleDelete(camera.id, e)}>
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {cameras.length === 0 && !loading && (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No cameras found. Add one to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add New Camera">
        <form onSubmit={handleCreate}>
          <div className="form-group">
            <label className="form-label">IP Address</label>
            <input 
              className="form-input" 
              required 
              value={formData.device_ip} 
              onChange={e => setFormData({...formData, device_ip: e.target.value})}
              placeholder="192.168.1.10"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input 
              className="form-input" 
              required 
              value={formData.username} 
              onChange={e => setFormData({...formData, username: e.target.value})}
              placeholder="admin"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input 
              className="form-input" 
              type="password" 
              required 
              value={formData.password} 
              onChange={e => setFormData({...formData, password: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Direction</label>
            <select 
              className="form-input" 
              value={formData.direction} 
              onChange={e => setFormData({...formData, direction: e.target.value})}
            >
              <option value="enter">Enter</option>
              <option value="exit">Exit</option>
            </select>
          </div>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
            <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setIsModalOpen(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Create Camera</button>
          </div>
        </form>
      </Modal>

      {/* Details Modal */}
      <Modal isOpen={!!selectedCamera} onClose={() => setSelectedCamera(null)} title="Camera Details">
        {selectedCamera && (
          <div>
            <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'var(--glass)', borderRadius: '0.75rem' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>ID</div>
              <div style={{ fontWeight: 600 }}>{selectedCamera.id}</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>IP Address</div>
                <div style={{ fontWeight: 600 }}>{selectedCamera.device_ip}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Direction</div>
                <div className={`badge ${selectedCamera.direction === 'enter' ? 'badge-success' : 'badge-danger'}`} style={{ marginTop: '0.25rem' }}>
                  {selectedCamera.direction}
                </div>
              </div>
            </div>
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Username</div>
              <div style={{ fontWeight: 600 }}>{selectedCamera.username}</div>
            </div>

            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ fontSize: '1.125rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={18} />
                Recent Events
              </h3>
              <div className="table-container" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                <table style={{ fontSize: '0.8125rem' }}>
                  <thead>
                    <tr>
                      <th>User</th>
                      <th>Enter Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cameraEvents.map(event => (
                      <tr key={event.id}>
                        <td>User #{event.user_id}</td>
                        <td>{new Date(event.enter_time).toLocaleString()}</td>
                      </tr>
                    ))}
                    {cameraEvents.length === 0 && (
                      <tr>
                        <td colSpan="2" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No recent events</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ marginTop: '2rem' }}>
              <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => setSelectedCamera(null)}>
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Cameras;
