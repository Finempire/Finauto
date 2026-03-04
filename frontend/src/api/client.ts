import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(err);
    }
);

// Auth
export const login = (email: string, password: string) =>
    api.post('/auth/login', { email, password }).then((r) => r.data);

export const getMe = () => api.get('/auth/me').then((r) => r.data);

// Upload
export const parseFile = (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return api.post('/upload/parse', fd).then((r) => r.data);
};

export const validateFile = (file: File, mapping: Record<string, string>, voucherType: string) => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('mapping', JSON.stringify(mapping));
    fd.append('voucher_type', voucherType);
    return api.post('/upload/validate', fd).then((r) => r.data);
};

// Tally
export const pingTally = (host: string, port: number) =>
    api.post('/tally/ping', { host, port }).then((r) => r.data);

export const getTallyCompanies = (host: string, port: number) =>
    api.get('/tally/companies', { params: { host, port } }).then((r) => r.data);

export const getTallyConfigs = () => api.get('/tally/configs').then((r) => r.data);
export const createTallyConfig = (data: any) => api.post('/tally/configs', data).then((r) => r.data);
export const updateTallyConfig = (id: string, data: any) => api.patch(`/tally/configs/${id}`, data).then((r) => r.data);
export const deleteTallyConfig = (id: string) => api.delete(`/tally/configs/${id}`);

// Templates
export const getTemplates = (voucherType?: string) =>
    api.get('/templates', { params: voucherType ? { voucher_type: voucherType } : {} }).then((r) => r.data);

export const createTemplate = (data: any) => api.post('/templates', data).then((r) => r.data);
export const deleteTemplate = (id: string) => api.delete(`/templates/${id}`);

// Admin
export const getUsers = () => api.get('/admin/users').then((r) => r.data);
export const createUser = (data: any) => api.post('/admin/users', data).then((r) => r.data);
export const updateUser = (id: string, data: any) => api.patch(`/admin/users/${id}`, data).then((r) => r.data);
export const deleteUser = (id: string) => api.delete(`/admin/users/${id}`);

export default api;
