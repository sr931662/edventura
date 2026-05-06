import { useParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import api from '../../api/axiosInstance';
import { useState } from 'react';
import styles from './VerifyInstitute.module.css';

export default function VerifyInstitute() {
  const { type } = useParams(); // verification type like 'GOVT_ID'
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [textData, setTextData] = useState('');

  const { mutate, isLoading } = useMutation({
    mutationFn: async () => {
      const instituteId = JSON.parse(localStorage.getItem('user'))?.institution_id; // better: useAuth
      if (type === 'DOCUMENT' && file) {
        return api.uploadDocument(instituteId, type, file);
      } else {
        return api.submitVerification(instituteId, type, { id_number: textData });
      }
    },
    onSuccess: () => navigate('/institute/status'),
    onError: (err) => alert('Submission failed'),
  });

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h2>Verify – {type}</h2>
        {type === 'DOCUMENT' ? (
          <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        ) : (
          <input value={textData} onChange={(e) => setTextData(e.target.value)} placeholder="Enter ID / Number" />
        )}
        <button onClick={mutate} disabled={isLoading} className={styles.gradientBtn}>Submit</button>
      </div>
    </div>
  );
}