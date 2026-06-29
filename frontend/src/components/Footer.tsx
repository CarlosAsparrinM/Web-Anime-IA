export default function Footer() {
  return (
    <footer style={{
      borderTop: '1px solid var(--card-border)',
      padding: '2rem',
      textAlign: 'center',
      color: '#64748b',
      fontSize: '0.9rem'
    }}>
      <p>Powered by AI · KenkoAnime © {new Date().getFullYear()}</p>
    </footer>
  );
}
