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

// Add response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token is invalid or expired
      localStorage.removeItem('token');
      // Redirect to login if not already there
      if (window.location.pathname !== '/admin/login') {
        window.location.href = '/admin/login';
      }
    }
    return Promise.reject(error);
  }
);

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
  age?: number;
  gender?: string;
  date_reported: string;
  contact_info: string;
  description?: string;
  last_seen_location?: string;
  photos: File[];
}) => {
  const formData = new FormData();
  formData.append('name', data.name);
  if (data.age !== undefined) formData.append('age', data.age.toString());
  if (data.gender) formData.append('gender', data.gender);
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

// Token validation
export const validateToken = async () => {
  try {
    const response = await api.get('/auth/validate');
    return response.data;
  } catch (error) {
    return null;
  }
};


// Text search
export const textSearch = async (params: {
  q?: string;
  age_min?: number;
  age_max?: number;
  gender?: string;
  location?: string;
  status?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}) => {
  const response = await api.get('/search/text', { params });
  return response.data;
};

// Dashboard stats
export const getDashboardStats = async () => {
  const response = await api.get('/admin/missing-persons/dashboard/stats');
  return response.data;
};

// Update person status
export const updatePersonStatus = async (personId: string, data: {
  status: string;
  traced_date?: string;
  traced_notes?: string;
}) => {
  const response = await api.patch(`/admin/missing-persons/${personId}/status`, data);
  return response.data;
};

// Update person details
export const updatePersonDetails = async (personId: string, data: {
  name?: string;
  age?: number;
  gender?: string;
  description?: string;
  last_seen_location?: string;
  contact_info?: string;
}) => {
  const response = await api.put(`/admin/missing-persons/${personId}`, data);
  return response.data;
};

// Export data
export const exportData = async (format: 'csv' | 'excel', status?: string) => {
  const params: any = { format };
  if (status) params.status_filter = status;
  
  const response = await api.get('/admin/missing-persons/export', {
    params,
    responseType: 'blob'
  });
  
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `missing_persons_export.${format === 'csv' ? 'csv' : 'xlsx'}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  
  return response.data;
};

export default api;
export const getAuditLogs = async (params: {
  page?: number;
  page_size?: number;
  admin_id?: string;
  action?: string;
  start_date?: string;
  end_date?: string;
}) => {
  const response = await api.get('/admin/missing-persons/audit-logs', { params });
  return response.data;
};
