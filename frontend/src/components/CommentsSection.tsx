"use client";

import { useState } from 'react';
import { useLanguage } from './LanguageProvider';

export interface CommentData {
  _id?: string;
  text: string;
  date: string;
}

export default function CommentsSection({ 
  slug, 
  initialComments 
}: { 
  slug: string, 
  initialComments: CommentData[] 
}) {
  const { language } = useLanguage();
  const [comments, setComments] = useState<CommentData[]>(initialComments);
  const [newComment, setNewComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const t = {
    title: language === 'es' ? 'Comentarios' : 'Comments',
    placeholder: language === 'es' ? 'Escribe un comentario anónimo...' : 'Write an anonymous comment...',
    button: language === 'es' ? 'Publicar' : 'Post',
    posting: language === 'es' ? 'Publicando...' : 'Posting...',
    noComments: language === 'es' ? 'Aún no hay comentarios. ¡Sé el primero!' : 'No comments yet. Be the first!',
    anonymous: language === 'es' ? 'Anónimo' : 'Anonymous'
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    
    setIsSubmitting(true);
    
    try {
      const res = await fetch(`/api/articles/${slug}/comment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: newComment }),
      });
      
      if (res.ok) {
        const data = await res.json();
        // Añadir el nuevo comentario al inicio de la lista
        setComments([data.comment, ...comments]);
        setNewComment("");
      }
    } catch (error) {
      console.error("Error posting comment:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
      <h3 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', fontWeight: 'bold' }}>
        {t.title} ({comments.length})
      </h3>
      
      <form onSubmit={handleSubmit} style={{ marginBottom: '2rem' }}>
        <textarea 
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder={t.placeholder}
          rows={3}
          style={{
            width: '100%',
            padding: '1rem',
            borderRadius: '8px',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'white',
            marginBottom: '1rem',
            resize: 'vertical',
            fontFamily: 'inherit'
          }}
        />
        <button 
          type="submit" 
          disabled={isSubmitting || !newComment.trim()}
          style={{
            padding: '0.5rem 1.5rem',
            borderRadius: '6px',
            background: isSubmitting || !newComment.trim() ? 'rgba(255,255,255,0.1)' : 'linear-gradient(to right, #6d28d9, #9333ea)',
            color: 'white',
            border: 'none',
            cursor: isSubmitting || !newComment.trim() ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            transition: 'opacity 0.2s'
          }}
        >
          {isSubmitting ? t.posting : t.button}
        </button>
      </form>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {comments.length === 0 ? (
          <p style={{ color: '#94a3b8', fontStyle: 'italic' }}>{t.noComments}</p>
        ) : (
          comments.map((c, i) => (
            <div key={c._id || i} style={{ 
              padding: '1rem', 
              borderRadius: '8px', 
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.05)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <strong style={{ color: '#c084fc' }}>{t.anonymous}</strong>
                <span style={{ color: '#64748b', fontSize: '0.875rem' }}>
                  {new Date(c.date).toLocaleDateString(
                    language === 'es' ? 'es-ES' : 'en-US',
                    { day: 'numeric', month: 'long', year: 'numeric' }
                  )}
                </span>
              </div>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                {c.text}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
