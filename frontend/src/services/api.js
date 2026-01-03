import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
});

// Use an interceptor to automatically add the auth token to every request header
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// --- Admin DB Viewer Functions ---

export const getJobStateDbTables = async () => {
  const response = await apiClient.get('/api/admin/db/job_state/tables');
  return response.data;
};

export const getJobStateTableData = async (tableName) => {
  const response = await apiClient.get(`/api/admin/db/job_state/table/${tableName}`);
  return response.data;
};


export default apiClient;
