import { Link } from 'react-router-dom';
import styles from './Home.module.css';
// import Header from '../../components/layout/Header';
// import Footer from '../../components/layout/Footer';

export default function Home() {
  return (
    <>
      {/* <Header /> */}
      <main className={styles.hero}>
        <h1 className={styles.headline}>
          <span className={styles.gradientText}>EdVentura</span> – Smart School OS
        </h1>
        <p className={styles.subhead}>
          AI‑powered management for modern educational institutions.
        </p>
        <div className={styles.cta}>
          <Link to="/enroll" className={styles.gradientBtn}>Enroll Your Institution</Link>
          <Link to="/login" className={styles.outlineBtn}>Login</Link>
        </div>
      </main>
      <section className={styles.features}>
        <h2>Why EdVentura?</h2>
        <div className={styles.grid}>
          <div className={styles.card}>AI‑driven insights</div>
          <div className={styles.card}>Full RBAC</div>
          <div className={styles.card}>Gamified learning</div>
        </div>
      </section>
      {/* <Footer /> */}
    </>
  );
}