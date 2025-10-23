import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

function JobSites({ language }) {
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingSite, setEditingSite] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    description: ''
  });

  const translations = {
    en: {
      title: 'Job Sites',
      addSite: 'Add New Site',
      name: 'Site Name',
      location: 'Address/Location',
      description: 'Description',
      actions: 'Actions',
      edit: 'Edit',
      delete: 'Delete',
      save: 'Save',
      cancel: 'Cancel',
      noSites: 'No job sites yet. Add your first site!',
      siteAdded: 'Site added successfully!',
      siteUpdated: 'Site updated successfully!',
      siteDeleted: 'Site deleted successfully!',
      error: 'Error',
      confirmDelete: 'Are you sure you want to delete this site?'
    },
    es: {
      title: 'Sitios de Trabajo',
      addSite: 'Agregar Nuevo Sitio',
      name: 'Nombre del Sitio',
      location: 'Dirección/Ubicación',
      description: 'Descripción',
      actions: 'Acciones',
      edit: 'Editar',
      delete: 'Eliminar',
      save: 'Guardar',
      cancel: 'Cancelar',
      noSites: '¡No hay sitios aún. Agrega tu primer sitio!',
      siteAdded: '¡Sitio agregado exitosamente!',
      siteUpdated: '¡Sitio actualizado exitosamente!',
      siteDeleted: '¡Sitio eliminado exitosamente!',
      error: 'Error',
      confirmDelete: '¿Estás seguro de que quieres eliminar este sitio?'
    }
  };

  const t = translations[language] || translations.en;

  useEffect(() => {
    loadSites();
  }, []);

  const loadSites = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/job-sites`);
      setSites(response.data);
    } catch (error) {
      console.error('Error loading sites:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingSite) {
        await axios.put(`${API}/job-sites/${editingSite.id}`, formData);
        alert(t.siteUpdated);
      } else {
        await axios.post(`${API}/job-sites`, formData);
        alert(t.siteAdded);
      }
      setShowDialog(false);
      setFormData({ name: '', location: '', description: '' });
      setEditingSite(null);
      loadSites();
    } catch (error) {
      console.error('Error saving site:', error);
      alert(t.error + ': ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (site) => {
    setEditingSite(site);
    setFormData({
      name: site.name,
      location: site.location || '',
      description: site.description || ''
    });
    setShowDialog(true);
  };

  const handleDelete = async (siteId) => {
    if (!window.confirm(t.confirmDelete)) return;
    
    try {
      await axios.delete(`${API}/job-sites/${siteId}`);
      alert(t.siteDeleted);
      loadSites();
    } catch (error) {
      console.error('Error deleting site:', error);
      alert(t.error + ': ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">{t.title}</h2>
        <button
          onClick={() => {
            setEditingSite(null);
            setFormData({ name: '', location: '', description: '' });
            setShowDialog(true);
          }}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          + {t.addSite}
        </button>
      </div>

      {sites.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          {t.noSites}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sites.map(site => (
            <div key={site.id} className="border rounded-lg p-4 shadow hover:shadow-lg transition">
              <h3 className="font-bold text-lg mb-2">{site.name}</h3>
              {site.location && (
                <p className="text-sm text-gray-600 mb-2">
                  📍 {site.location}
                </p>
              )}
              {site.description && (
                <p className="text-sm text-gray-500 mb-3">{site.description}</p>
              )}
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(site)}
                  className="text-blue-500 hover:text-blue-700 text-sm"
                >
                  {t.edit}
                </button>
                <button
                  onClick={() => handleDelete(site.id)}
                  className="text-red-500 hover:text-red-700 text-sm"
                >
                  {t.delete}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Dialog */}
      {showDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold mb-4">
              {editingSite ? t.edit : t.addSite}
            </h3>
            <form onSubmit={handleSubmit}>
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
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">{t.location}</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  placeholder="123 Main St, City, State"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">{t.description}</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  rows="3"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowDialog(false);
                    setEditingSite(null);
                    setFormData({ name: '', location: '', description: '' });
                  }}
                  className="px-4 py-2 border rounded hover:bg-gray-100"
                >
                  {t.cancel}
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  {t.save}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default JobSites;