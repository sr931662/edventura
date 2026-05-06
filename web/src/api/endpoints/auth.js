import api from '../axiosInstance';

export const login = (email, password) => {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);
  return api.post('/auth/login', params);
};

export const getMe = () => api.get('/auth/me');
export const registerInstitute = (data) => api.post('/public/register-institute', data); // will add