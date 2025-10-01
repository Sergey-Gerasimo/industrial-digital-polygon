// src/components/UserManagement/UserList.jsx
import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import UserActions from './UserActions';

const UserList = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    is_active: '',
    role: '',
    limit: 50,
    offset: 0,
  });

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await apiService.getUsers(filters);
      setUsers(data.users);
    } catch (err) {
      setError('Failed to load users');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [filters]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, offset: 0 }));
  };

  const handleUserUpdate = () => {
    loadUsers();
  };

  if (loading) return <div className="loading">Loading users...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="user-management">
      <div className="filters">
        <select 
          value={filters.role} 
          onChange={(e) => handleFilterChange('role', e.target.value)}
        >
          <option value="">All Roles</option>
          <option value="ADMIN">Admin</option>
          <option value="USER">User</option>
        </select>
        
        <select 
          value={filters.is_active} 
          onChange={(e) => handleFilterChange('is_active', e.target.value)}
        >
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
        
        <button onClick={loadUsers}>Refresh</button>
      </div>

      <div className="users-grid">
        <table className="users-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Role</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id} className={user.is_active ? '' : 'inactive'}>
                <td>{user.username}</td>
                <td>
                  <span className={`role-badge ${user.role.toLowerCase()}`}>
                    {user.role}
                  </span>
                </td>
                <td>
                  <span className={`status ${user.is_active ? 'active' : 'inactive'}`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</td>
                <td>
                  <UserActions user={user} onUserUpdate={handleUserUpdate} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {users.length === 0 && (
          <div className="no-users">No users found</div>
        )}
      </div>
    </div>
  );
};

export default UserList;