import styles from './CardWrapper.module.css';
export default function CardWrapper({ children, className }) {
  return <div className={`${styles.card} ${className || ''}`}>{children}</div>;
}