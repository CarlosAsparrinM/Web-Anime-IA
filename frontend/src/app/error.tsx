"use client";

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '50vh',
      gap: '1.5rem',
      textAlign: 'center'
    }}>
      <h2 style={{ fontSize: '2rem', color: 'var(--neon-pink)' }}>¡Ups! Algo salió mal.</h2>
      <p style={{ color: '#94a3b8', maxWidth: '400px' }}>
        No pudimos cargar la información en este momento. Nuestros agentes IA ya están revisando el problema.
      </p>
      <button
        onClick={() => reset()}
        style={{
          background: 'var(--neon-purple)',
          color: 'white',
          border: 'none',
          padding: '0.75rem 1.5rem',
          borderRadius: '20px',
          fontWeight: 600,
          cursor: 'pointer',
          marginTop: '1rem',
          transition: 'background 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.background = '#7c3aed'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'var(--neon-purple)'}
      >
        Intentar de nuevo
      </button>
    </div>
  );
}
