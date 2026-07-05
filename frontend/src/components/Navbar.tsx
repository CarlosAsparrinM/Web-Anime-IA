"use client";

import Link from 'next/link';
import { useLanguage } from './LanguageProvider';
import { Languages } from 'lucide-react';

export default function Navbar() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <nav className="navbar">
      <Link href="/" className="nav-brand">
        <span className="text-gradient">Kenko</span>
        <span style={{ color: '#fff' }}>Anime</span>
      </Link>

      <div className="nav-links">
        <Link href="/?cat=novedades" className="nav-link">
          {t('Novedades', 'News')}
        </Link>
        <Link href="/?cat=analisis" className="nav-link">
          {t('Análisis', 'Analysis')}
        </Link>
        <Link href="/?cat=curiosidades" className="nav-link">
          {t('Curiosidades', 'Trivia')}
        </Link>
        
        <button 
          onClick={() => setLanguage(language === 'es' ? 'en' : 'es')}
          className="btn-lang"
        >
          <Languages size={16} />
          {language === 'es' ? '🇪🇸 ES' : '🇬🇧 EN'}
        </button>
      </div>
    </nav>
  );
}
