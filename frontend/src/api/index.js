import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const cameraApi = {
  list: (params) => api.get('/cameras/list', { params: params || {} }),
  get: (id) => api.get(`/cameras/${id}`),
  create: (data) => api.post('/cameras/', data),
  delete: (id) => api.delete(`/cameras/${id}`),
  connect: (id) => api.post(`/cameras/${id}/connect`),
  disconnect: (id) => api.post(`/cameras/${id}/disconnect`),
  restart: (id) => api.post(`/cameras/${id}/restart`),
};

export const userApi = {
  list: (params) => api.get('/users/list', { params: params || {} }),
  get: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users/', data),
  delete: (id) => api.delete(`/users/${id}`),
};

export const userEventApi = {
  list: (params) => api.post('/user-events/list', params || {}),
  get: (id) => api.get(`/user-events/${id}`),
};

export default api;
