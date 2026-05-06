import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../../api/axiosInstance';
import useAuth from '../../hooks/useAuth';
import styles from './InstituteStatus.module.css';

export default function InstituteStatus() {
  const { user } = useAuth();
  const instituteId = user?.institution_id;

  const { data, isLoading, error } = useQuery({
    queryKey: ['instituteStatus', instituteId],
    queryFn: () => api.get(`/institutes/${instituteId}/status`).then(res => res.data),
    enabled: !!instituteId,
  });

  if (isLoading) return <div className={styles.page}>Loading...</div>;
  if (error) return <div className={styles.page}>Error loading status</div>;

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h2 className={styles.gradientText}>Trust Score: {data.trust_score} / 100</h2>
        <p>Status: <strong>{data.verification_status}</strong></p>
        <p>Feature Level: {data.feature_level}</p>
        {data.can_onboard_students && <p>✅ You can onboard students</p>}
        {data.can_use_communication && <p>✅ Communication features available</p>}
        {data.can_full_access && <p>✅ Full platform access</p>}

        <div className={styles.missingSteps}>
          <h3>Complete Verification</h3>
          {data.missing_steps.map(step => (
            <div key={step.verification_type} className={styles.step}>
              <span>{step.description}</span>
              <Link to={`/institute/verify/${step.verification_type}`} className={styles.verifyBtn}>Verify</Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}