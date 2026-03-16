import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { userApi, userEventApi } from '../api';
import { ArrowLeft, User, Calendar, Clock, MapPin, ChevronRight } from 'lucide-react';

const UserDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [userRes, eventsRes] = await Promise.all([
          userApi.get(id),
          userEventApi.list({ user_id: parseInt(id), limit: 100 })
        ]);
        setUser(userRes.data);
        setEvents(eventsRes.data.events);
      } catch (err) {
        console.error('Failed to fetch user details', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  // Group events by date
  const groupedEvents = events.reduce((acc, event) => {
    const date = new Date(event.enter_time).toLocaleDateString();
    if (!acc[date]) acc[date] = [];
    acc[date].push(event);
    return acc;
  }, {});

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>;
  if (!user) return <div style={{ padding: '2rem', textAlign: 'center' }}>User not found</div>;

  return (
    <div className="fade-in">
      <button className="btn btn-ghost" onClick={() => navigate('/users')} style={{ marginBottom: '2rem' }}>
        <ArrowLeft size={18} />
        Back to Users
      </button>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
        {/* Profile Card */}
        <div className="glass-card" style={{ height: 'fit-content' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{ width: 120, height: 120, borderRadius: '50%', background: 'var(--glass)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
              <User size={60} color="var(--primary)" />
            </div>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{user.username}</h2>
            <span className={`badge ${user.is_active ? 'badge-success' : 'badge-danger'}`}>
              {user.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="glass-card" style={{ padding: '1rem', background: 'rgba(15, 23, 42, 0.3)' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>User ID</div>
              <div style={{ fontWeight: 600 }}>{user.id}</div>
            </div>
            <div className="glass-card" style={{ padding: '1rem', background: 'rgba(15, 23, 42, 0.3)' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Employment Status</div>
              <div style={{ fontWeight: 600 }}>{user.in_work ? 'In Work' : 'Out of Office'}</div>
            </div>
          </div>
        </div>

        {/* Timeline/Calendar View */}
        <div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Calendar size={22} color="var(--primary)" />
            Activity History
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {Object.keys(groupedEvents).length === 0 ? (
              <div className="glass-card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                No activity recorded for this user.
              </div>
            ) : (
              Object.entries(groupedEvents).sort((a, b) => new Date(b[0]) - new Date(a[0])).map(([date, dayEvents]) => (
                <div key={date}>
                  <div style={{ 
                    display: 'inline-block', 
                    padding: '0.5rem 1rem', 
                    background: 'var(--glass)', 
                    borderRadius: '2rem', 
                    fontSize: '0.875rem', 
                    fontWeight: 600,
                    marginBottom: '1rem',
                    border: '1px solid var(--border)'
                  }}>
                    {date}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {dayEvents.sort((a, b) => new Date(b.enter_time) - new Date(a.enter_time)).map(event => (
                      <div key={event.id} className="glass-card" style={{ 
                        padding: '1rem', 
                        display: 'grid', 
                        gridTemplateColumns: '1fr 1fr 1fr', 
                        alignItems: 'center',
                        transition: 'transform 0.2s ease',
                        cursor: 'default'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <Clock size={16} color="var(--primary)" />
                          <div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Enter</div>
                            <div style={{ fontSize: '0.9375rem', fontWeight: 500 }}>
                              {new Date(event.enter_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <Clock size={16} color="var(--danger)" />
                          <div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Exit</div>
                            <div style={{ fontSize: '0.9375rem', fontWeight: 500 }}>
                              {event.exit_time 
                                ? new Date(event.exit_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
                                : '--:--'}
                            </div>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'flex-end' }}>
                          <MapPin size={16} color="var(--text-muted)" />
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Camera ID</div>
                            <div style={{ fontSize: '0.9375rem', fontWeight: 500 }}>#{event.camera_id}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserDetail;
