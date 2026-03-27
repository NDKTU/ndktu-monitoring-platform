import React from 'react';
import { NavLink } from 'react-router-dom';
import { Camera, Users, LayoutDashboard, Settings, Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const Sidebar = () => {
  const { isDarkMode, toggleTheme } = useTheme();
  const links = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/cameras', icon: Camera, label: 'Cameras' },
    { to: '/users', icon: Users, label: 'Users' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Camera size={32} />
        <span>NDKTU Monitor</span>
      </div>
      <nav>
        <ul className="nav-links">
          {links.map((link) => (
            <li key={link.to}>
              <NavLink
                to={link.to}
                className={({ isActive }) => 
                  `nav-link ${isActive ? 'active' : ''}`
                }
              >
                <link.icon size={20} />
                <span>{link.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <button 
          className="nav-link" 
          onClick={toggleTheme} 
          style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}
        >
          {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
          <span>{isDarkMode ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
        <div className="nav-link">
          <Settings size={20} />
          <span>Settings</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
