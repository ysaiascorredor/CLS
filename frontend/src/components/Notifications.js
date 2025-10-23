import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function Notifications({ language }) {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const translations = {
    en: {
      title: 'Notifications',
      markAllRead: 'Mark All as Read',
      noNotifications: 'No notifications yet',
      newFinding: 'New Finding Assigned',
      unread: 'unread'
    },
    es: {
      title: 'Notificaciones',
      markAllRead: 'Marcar Todas como Leídas',
      noNotifications: 'No hay notificaciones aún',
      newFinding: 'Nuevo Finding Asignado',
      unread: 'sin leer'
    }
  };

  const t = translations[language] || translations.en;

  useEffect(() => {
    loadNotifications();
    // Poll for new notifications every 30 seconds
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`);
      setNotifications(response.data.notifications);
      setUnreadCount(response.data.unread);
      setLoading(false);
    } catch (error) {
      console.error('Error loading notifications:', error);
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.put(`${API}/notifications/${notificationId}/read`);
      loadNotifications();
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await axios.put(`${API}/notifications/mark-all-read`);
      loadNotifications();
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  if (loading) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">{t.title}</h2>
          {unreadCount > 0 && (
            <span className="text-sm text-gray-500">
              {unreadCount} {t.unread}
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={markAllAsRead}
            className="text-sm text-blue-500 hover:text-blue-700"
          >
            {t.markAllRead}
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          {t.noNotifications}
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map(notification => (
            <div
              key={notification.id}
              onClick={() => !notification.is_read && markAsRead(notification.id)}
              className={`border rounded-lg p-4 cursor-pointer transition ${
                !notification.is_read 
                  ? 'bg-blue-50 border-blue-200 hover:bg-blue-100' 
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  {!notification.is_read && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  )}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold mb-1">{notification.title}</h4>
                  <p className="text-sm text-gray-600">{notification.message}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    {new Date(notification.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Notifications;
