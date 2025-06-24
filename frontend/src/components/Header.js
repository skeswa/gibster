import React from 'react';
import { Link } from 'react-router-dom';

const Header = ({ user, onLogout }) => {
  return (
    <header className="header">
      <h1>Gibster</h1>
      
      <nav>
        {user ? (
          <>
            <span className="user-info">Welcome, {user.email}</span>
            <Link to="/dashboard" className="btn btn-secondary">Dashboard</Link>
            <Link to="/credentials" className="btn btn-secondary">Settings</Link>
            <button onClick={onLogout} className="btn btn-danger">Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className="btn btn-primary">Login</Link>
            <Link to="/register" className="btn btn-secondary">Register</Link>
          </>
        )}
      </nav>
    </header>
  );
};

export default Header; 