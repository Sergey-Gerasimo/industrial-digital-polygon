// src/App.jsx
import React, { useState } from 'react';
import { useAuth } from './hooks/useAuth';
import Login from './components/Auth/Login';
import UserList from './components/UserManagement/UserList';
import UserForm from './components/UserManagement/UserForm';
import './App.css';

function App() {
  const { user, loading, login, logout, isAuthenticated, isAdmin } = useAuth();
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUserCreated = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Login onLogin={login} />;
  }

  if (!isAdmin) {
    return (
      <div className="container">
        <header>
          <h1>Access Denied</h1>
          <p>You need admin privileges to access this panel.</p>
          <button onClick={logout} className="btn btn-secondary">Logout</button>
        </header>
      </div>
    );
  }

  return (
    <div className="container">
      <header>
        <h1>User Management Panel</h1>
        <div className="user-info">
          Welcome, {user.username} ({user.role})
          <button onClick={logout} className="btn btn-secondary">Logout</button>
        </div>
      </header>

      <main>
        <div className="panel-layout">
          <aside className="sidebar">
            <UserForm onUserCreated={handleUserCreated} />
          </aside>
          
          <section className="main-content">
            <UserList key={refreshTrigger} />
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;