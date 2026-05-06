import api from '../axiosInstance';

export const getInstituteStatus = (id) => api.get(`/institutes/${id}/status`);
export const submitVerification = (id, type, data) => api.post(`/institutes/${id}/verify`, { verification_type: type, data });
export const uploadDocument = (id, type, file) => {
  const form = new FormData();
  form.append('document_type', type);
  form.append('file', file);
  return api.post(`/institutes/${id}/documents`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};