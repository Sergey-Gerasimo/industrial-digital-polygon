// src/components/UserManagement/UserActions.jsx
import React, { useState } from 'react';
import { apiService } from '../../services/api';

const UserActions = ({ user, onUserUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState(user.role);

  const handleActivate = async () => {
    setLoading(true);
    try {
      await apiService.activateUser(user.id);
      onUserUpdate();
    } catch (error) {
      alert('Failed to activate user');
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivate = async () => {
    setLoading(true);
    try {
      await apiService.deactivateUser(user.id);
      onUserUpdate();
    } catch (error) {
      alert('Failed to deactivate user');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete user ${user.username}?`)) {
      return;
    }
    
    setLoading(true);
    try {
      await apiService.deleteUser(user.id);
      onUserUpdate();
    } catch (error) {
      alert('Failed to delete user');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async () => {
    if (!newPassword || newPassword.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }

    setLoading(true);
    try {
      await apiService.updateUserPassword(user.id, newPassword);
      setShowPasswordModal(false);
      setNewPassword('');
      alert('Password updated successfully');
    } catch (error) {
      alert('Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async () => {
    setLoading(true);
    try {
      await apiService.updateUserRole(user.id, newRole);
      setShowRoleModal(false);
      onUserUpdate();
      alert('Role updated successfully');
    } catch (error) {
      alert('Failed to update role');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="user-actions">
      {user.is_active ? (
        <button 
          onClick={handleDeactivate} 
          disabled={loading}
          className="btn btn-warning"
        >
          Deactivate
        </button>
      ) : (
        <button 
          onClick={handleActivate} 
          disabled={loading}
          className="btn btn-success"
        >
          Activate
        </button>
      )}
      
      <button 
        onClick={() => setShowPasswordModal(true)}
        disabled={loading}
        className="btn btn-secondary"
      >
        Change Password
      </button>
      
      <button 
        onClick={() => setShowRoleModal(true)}
        disabled={loading}
        className="btn btn-info"
      >
        Change Role
      </button>
      
      <button 
        onClick={handleDelete}
        disabled={loading}
        className="btn btn-danger"
      >
        Delete
      </button>

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Change Password for {user.username}</h3>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter new password"
              className="input-field"
            />
            <div className="modal-actions">
              <button onClick={handlePasswordChange} disabled={loading}>
                Update Password
              </button>
              <button onClick={() => setShowPasswordModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Role Change Modal */}
      {showRoleModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Change Role for {user.username}</h3>
            <select 
              value={newRole} 
              onChange={(e) => setNewRole(e.target.value)}
              className="input-field"
            >
              <option value="USER">User</option>
              <option value="ADMIN">Admin</option>
            </select>
            <div className="modal-actions">
              <button onClick={handleRoleChange} disabled={loading}>
                Update Role
              </button>
              <button onClick={() => setShowRoleModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserActions;