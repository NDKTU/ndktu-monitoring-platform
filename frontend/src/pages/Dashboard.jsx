import React, { useState, useEffect } from 'react';
import { cameraApi, userApi } from '../api';
import { Camera, Users, ShieldAlert, Activity } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState({
    cameras: 0,
    users: 0,
    activeCameras: 0,
    usersInWork: 0
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [camRes, userRes] = await Promise.all([
          cameraApi.list({ limit: 100 }),
          userApi.list({ limit: 100 })
        ]);

        setStats({
          cameras: camRes.data.total,
          activeCameras: camRes.data.cameras.filter(c => c.is_active).length,
          users: userRes.data.total,
          usersInWork: userRes.data.users.filter(u => u.in_work).length
        });
      } catch (err) {
        console.error('Failed to fetch stats', err);
      }
    };
    fetchStats();
  }, []);

  const cards = [
    { label: 'Total Cameras', value: stats.cameras, icon: Camera, color: '#6366f1' },
    { label: 'Active Cameras', value: stats.activeCameras, icon: Activity, color: '#10b981' },
    { label: 'Total Users', value: stats.users, icon: Users, color: '#818cf8' },
    { label: 'Users in Work', value: stats.usersInWork, icon: ShieldAlert, color: '#f59e0b' },
  ];

  return (
    <div className="fade-in">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 700 }}>Dashboard</h1>
        <p style={{ color: 'var(--text-muted)' }}>System overview and security metrics</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
        {cards.map((card, i) => (
          <div key={i} className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{ 
              padding: '1rem', 
              borderRadius: '1rem', 
              background: `${card.color}15`, 
              color: card.color 
            }}>
              <card.icon size={28} />
            </div>
            <div>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{card.label}</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{card.value}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="glass-card" style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderStyle: 'dashed' }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <Activity size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
          <p>Real-time activity feed coming soon...</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
