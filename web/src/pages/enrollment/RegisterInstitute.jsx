import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axiosInstance';
import useAuth from '../../hooks/useAuth';
import styles from './RegisterInstitute.module.css';

const schema = z.object({
  fullName: z.string().min(1, 'Required'),
  email: z.string().email(),
  password: z.string().min(6),
  instituteName: z.string().min(3),
  address: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  affiliationType: z.enum(['CBSE', 'ICSE', 'STATE', 'OTHER']),
  affiliationId: z.string().optional(),
});

export default function RegisterInstitute() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(schema) });

  const onSubmit = async (data) => {
    try {
      // Call public registration endpoint
      const res = await api.post('/public/register-institute', {
        user: {
          email: data.email,
          password: data.password,
          full_name: data.fullName,
        },
        institute: {
          name: data.instituteName,
          address: data.address,
          city: data.city,
          state: data.state,
          affiliation_type: data.affiliationType,
          affiliation_id: data.affiliationId,
        },
      });
      localStorage.setItem('access_token', res.data.access_token);
      // Refresh user
      const userRes = await api.get('/auth/me');
      navigate('/institute/status');
    } catch (err) {
      alert('Registration failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h2 className={styles.heading}>Register Your Institution</h2>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* fields - simple input styling */}
          <input {...register('fullName')} placeholder="Full Name *" className={styles.input} />
          <input {...register('email')} placeholder="Email *" className={styles.input} />
          <input type="password" {...register('password')} placeholder="Password *" className={styles.input} />
          <input {...register('instituteName')} placeholder="Institute Name *" className={styles.input} />
          {/* ... other fields */}
          <select {...register('affiliationType')} className={styles.select}>
            <option value="">Select Board</option>
            <option value="CBSE">CBSE</option>
            <option value="ICSE">ICSE</option>
            <option value="STATE">State Board</option>
            <option value="OTHER">Other</option>
          </select>
          <input {...register('affiliationId')} placeholder="Affiliation ID (optional)" className={styles.input} />
          <button type="submit" className={styles.gradientBtn}>Create Institute</button>
        </form>
      </div>
    </div>
  );
}