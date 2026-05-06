import useAuth from '../../hooks/useAuth';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <div className={styles.page}>
      <h1>Welcome, {user?.full_name}</h1>
      <p>Role: {user?.role}</p>
      <button onClick={logout} className={styles.logoutBtn}>Logout</button>
    </div>
  );
}