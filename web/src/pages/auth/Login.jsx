import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import useAuth from '../../hooks/useAuth';
import styles from './Login.module.css';

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

export default function LoginPage() {
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data) => {
    setIsLoading(true);
    try {
      // DEMO ADMIN BYPASS (remove in production)
      if (data.email === 'admin@demo.com' && data.password === '123456') {
        localStorage.setItem('access_token', 'demo-token');
        navigate('/dashboard');
        return;
      }
      await login(data.email, data.password);
      navigate('/dashboard');
    } catch (err) {
      alert('Login failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={`${styles.orb} ${styles.orbTop}`} />
      <div className={`${styles.orb} ${styles.orbBottom}`} />
      <div className={styles.container}>
        <div className={styles.card}>
          <div className={styles.logoWrap}>
            <img src="/logo.svg" alt="EdVentura" className={styles.logo} />
          </div>
          <h1 className={styles.title}>Welcome Back</h1>

          <form onSubmit={handleSubmit(onSubmit)}>
            <div className={styles.inputGroup}>
              <input
                {...register('email')}
                type="text"
                placeholder="User ID / Email"
                className={styles.input}
              />
              {errors.email && <span className={styles.error}>{errors.email.message}</span>}
            </div>
            <div className={`${styles.inputGroup} ${styles.passwordWrapper}`}>
              <input
                type={showPassword ? 'text' : 'password'}
                {...register('password')}
                placeholder="Password"
                className={styles.input}
              />
              <span className={styles.eyeIcon} onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </span>
              {errors.password && <span className={styles.error}>{errors.password.message}</span>}
            </div>

            <div className={styles.checkboxRow}>
              <label className={styles.checkbox}>
                <input type="checkbox" /> Keep me logged in
              </label>
              <Link to="/forgot-password" className={styles.link}>Forgot Password?</Link>
            </div>

            <button type="submit" className={styles.gradientBtn} disabled={isLoading}>
              {isLoading ? 'Logging in…' : 'LOGIN'}
            </button>
          </form>

          <div className={styles.security}>
            <p className={styles.securityText}>Higher Security</p>
            <div className={styles.securityButtons}>
              <button className={styles.securityBtn}><span>👤</span> Face ID</button>
              <button className={styles.securityBtn}><span>🖐️</span> Biometric</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}