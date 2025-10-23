import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

function ProfileSettings({ language, user, onUpdate }) {
  const [formData, setFormData] = useState({
    name: '',
    job_title: ''
  });
  const [saving, setSaving] = useState(false);

  const translations = {
    en: {
      title: 'Profile Settings',
      name: 'Name',
      jobTitle: 'Job Title / Position',
      jobTitlePlaceholder: 'e.g., Safety Inspector, Site Manager, Auditor',
      save: 'Save Changes',
      saved: 'Profile updated successfully!',
      error: 'Error updating profile'
    },
    es: {
      title: 'Configuración de Perfil',
      name: 'Nombre',
      jobTitle: 'Título / Posición de Trabajo',
      jobTitlePlaceholder: 'ej., Inspector de Seguridad, Gerente de Sitio, Auditor',
      save: 'Guardar Cambios',
      saved: '¡Perfil actualizado exitosamente!',
      error: 'Error actualizando perfil'
    }
  };

  const t = translations[language] || translations.en;

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || '',
        job_title: user.job_title || ''
      });
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      const response = await axios.put(`${API}/auth/profile`, formData);
      alert(t.saved);
      
      // Update user context if onUpdate function is provided
      if (onUpdate && typeof onUpdate === 'function') {
        try {
          onUpdate(response.data);
        } catch (updateError) {
          console.error('Error updating user context:', updateError);
          // Reload page to refresh user data
          window.location.reload();
        }
      } else {
        // If no onUpdate function, reload to refresh user data
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      alert(t.error + ': ' + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">{t.title}</h2>
      
      <form onSubmit={handleSubmit} className="max-w-md">
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">{t.name}</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full border rounded px-3 py-2"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">{t.jobTitle}</label>
          <input
            type="text"
            value={formData.job_title}
            onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
            className="w-full border rounded px-3 py-2"
            placeholder={t.jobTitlePlaceholder}
          />
          <p className="text-xs text-gray-500 mt-1">
            {language === 'en' 
              ? 'This will be displayed on audit reports and your profile'
              : 'Esto se mostrará en los reportes de auditoría y tu perfil'}
          </p>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {saving ? (language === 'en' ? 'Saving...' : 'Guardando...') : t.save}
        </button>
      </form>
    </div>
  );
}

export default ProfileSettings;