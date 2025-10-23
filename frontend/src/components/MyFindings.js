import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

function MyFindings({ language }) {
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFinding, setSelectedFinding] = useState(null);

  const translations = {
    en: {
      title: 'My Assigned Findings',
      total: 'Total Assigned',
      site: 'Site',
      auditor: 'Auditor',
      question: 'Question',
      priority: 'Priority',
      status: 'Status',
      dueDate: 'Due Date',
      comment: 'Comment',
      actionTaken: 'Action Taken',
      updateStatus: 'Update Status',
      markInProgress: 'Mark In Progress',
      markClosed: 'Mark as Closed',
      save: 'Save',
      cancel: 'Cancel',
      noFindings: 'No findings assigned to you yet',
      updated: 'Finding updated successfully!',
      error: 'Error',
      open: 'Open',
      inProgress: 'In Progress',
      closed: 'Closed',
      low: 'Low',
      medium: 'Medium',
      high: 'High',
      critical: 'Critical'
    },
    es: {
      title: 'Mis Findings Asignados',
      total: 'Total Asignados',
      site: 'Sitio',
      auditor: 'Auditor',
      question: 'Pregunta',
      priority: 'Prioridad',
      status: 'Estado',
      dueDate: 'Fecha Límite',
      comment: 'Comentario',
      actionTaken: 'Acción Tomada',
      updateStatus: 'Actualizar Estado',
      markInProgress: 'Marcar En Progreso',
      markClosed: 'Marcar como Cerrado',
      save: 'Guardar',
      cancel: 'Cancelar',
      noFindings: 'No tienes findings asignados aún',
      updated: '¡Finding actualizado exitosamente!',
      error: 'Error',
      open: 'Abierto',
      inProgress: 'En Progreso',
      closed: 'Cerrado',
      low: 'Baja',
      medium: 'Media',
      high: 'Alta',
      critical: 'Crítica'
    }
  };

  const t = translations[language] || translations.en;

  useEffect(() => {
    loadFindings();
  }, []);

  const loadFindings = async () => {
    try {
      const response = await axios.get(`${API}/findings/my-assignments`);
      setFindings(response.data.assigned_findings);
      setLoading(false);
    } catch (error) {
      console.error('Error loading findings:', error);
      setLoading(false);
    }
  };

  const updateFinding = async (auditId, findingId, updateData) => {
    try {
      await axios.put(`${API}/audits/${auditId}/findings/${findingId}`, updateData);
      alert(t.updated);
      setSelectedFinding(null);
      loadFindings();
    } catch (error) {
      console.error('Error updating finding:', error);
      alert(t.error + ': ' + (error.response?.data?.detail || error.message));
    }
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return colors[priority] || colors.medium;
  };

  const getStatusColor = (status) => {
    const colors = {
      open: 'bg-red-100 text-red-800',
      in_progress: 'bg-blue-100 text-blue-800',
      closed: 'bg-green-100 text-green-800'
    };
    return colors[status] || colors.open;
  };

  if (loading) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">{t.title}</h2>
        <p className="text-gray-500">
          {t.total}: {findings.length}
        </p>
      </div>

      {findings.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          {t.noFindings}
        </div>
      ) : (
        <div className="space-y-4">
          {findings.map(finding => (
            <div key={finding.id} className="border rounded-lg p-4 shadow hover:shadow-lg transition">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold text-lg">{finding.question}</h3>
                  <div className="flex gap-2 mt-2">
                    <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(finding.priority)}`}>
                      {t[finding.priority] || finding.priority}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(finding.status)}`}>
                      {t[finding.status.replace('_', '')] || finding.status}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedFinding(finding)}
                  className="text-blue-500 hover:text-blue-700 text-sm"
                >
                  {t.updateStatus}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 mt-3">
                <div>
                  <span className="font-medium">{t.site}:</span> {finding.site_name}
                </div>
                <div>
                  <span className="font-medium">{t.auditor}:</span> {finding.auditor_name}
                </div>
              </div>

              {finding.comment && (
                <div className="mt-3 text-sm">
                  <span className="font-medium">{t.comment}:</span> {finding.comment}
                </div>
              )}

              {finding.action_taken && (
                <div className="mt-2 text-sm bg-green-50 p-2 rounded">
                  <span className="font-medium">{t.actionTaken}:</span> {finding.action_taken}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedFinding && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold mb-4">{t.updateStatus}</h3>
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">{selectedFinding.question}</p>
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => updateFinding(selectedFinding.audit_id, selectedFinding.id, { status: 'in_progress' })}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  {t.markInProgress}
                </button>
                <button
                  onClick={() => updateFinding(selectedFinding.audit_id, selectedFinding.id, { status: 'closed' })}
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  {t.markClosed}
                </button>
              </div>
              <button
                onClick={() => setSelectedFinding(null)}
                className="w-full px-4 py-2 border rounded hover:bg-gray-100"
              >
                {t.cancel}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MyFindings;