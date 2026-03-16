import React from 'react';
import { NavLink } from 'react-router-dom';
import { Camera, Users, LayoutDashboard, Settings } from 'lucide-react';

const Sidebar = () => {
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
      <div style={{ marginTop: 'auto' }}>
        <div className="nav-link">
          <Settings size={20} />
          <span>Settings</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
