import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const searchFace = async (imageFile: File, threshold?: number, maxResults?: number) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  if (threshold !== undefined) formData.append('threshold', threshold.toString());
  if (maxResults !== undefined) formData.append('max_results', maxResults.toString());
  
  const response = await api.post('/search', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const login = async (username: string, password: string) => {
  const response = await api.post('/auth/login', { username, password });
  return response.data;
};

export const uploadMissingPerson = async (data: {
  name: string;
  date_reported: string;
  contact_info: string;
  description?: string;
  last_seen_location?: string;
  photos: File[];
}) => {
  const formData = new FormData();
  formData.append('name', data.name);
  formData.append('date_reported', data.date_reported);
  formData.append('contact_info', data.contact_info);
  if (data.description) formData.append('description', data.description);
  if (data.last_seen_location) formData.append('last_seen_location', data.last_seen_location);
  
  data.photos.forEach(photo => {
    formData.append('photos', photo);
  });
  
  const response = await api.post('/admin/missing-persons', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const listMissingPersons = async () => {
  const response = await api.get('/admin/missing-persons');
  return response.data;
};

export const deleteMissingPerson = async (personId: string) => {
  const response = await api.delete(`/admin/missing-persons/${personId}`);
  return response.data;
};

export default api;
