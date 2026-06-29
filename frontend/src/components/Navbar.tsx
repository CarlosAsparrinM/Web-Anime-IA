"use client";

import Link from 'next/link';
import { useLanguage } from './LanguageProvider';
import { Languages } from 'lucide-react';

export default function Navbar() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <nav style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      background: 'rgba(15, 17, 26, 0.8)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--card-border)',
      padding: '1rem',
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '1rem'
    }}>
      <Link href="/" style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'Outfit' }}>
        <span className="text-gradient">Kenko</span>
        <span style={{ color: '#fff' }}>Anime</span>
      </Link>

      <div style={{ 
        display: 'flex', 
        gap: '1.5rem', 
        alignItems: 'center',
        flexWrap: 'wrap',
        justifyContent: 'center'
      }}>
        <Link href="/?cat=novedades" style={{ fontWeight: 500, fontSize: '0.9rem' }}>
          {t('Novedades', 'News')}
        </Link>
        <Link href="/?cat=analisis" style={{ fontWeight: 500, fontSize: '0.9rem' }}>
          {t('Análisis', 'Analysis')}
        </Link>
        <Link href="/?cat=curiosidades" style={{ fontWeight: 500, fontSize: '0.9rem' }}>
          {t('Curiosidades', 'Trivia')}
        </Link>
        
        <button 
          onClick={() => setLanguage(language === 'es' ? 'en' : 'es')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'var(--card-bg)',
            border: '1px solid var(--card-border)',
            padding: '0.5rem 1rem',
            borderRadius: '20px',
            color: '#fff',
            cursor: 'pointer',
            fontWeight: 600,
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'var(--card-bg)'}
        >
          <Languages size={16} />
          {language === 'es' ? '🇪🇸 ES' : '🇬🇧 EN'}
        </button>
      </div>
    </nav>
  );
}
