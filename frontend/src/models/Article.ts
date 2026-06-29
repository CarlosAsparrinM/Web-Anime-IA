import mongoose from 'mongoose';

const ArticleSchema = new mongoose.Schema(
  {
    title: {
      es: { type: String, required: true },
      en: { type: String, required: true },
    },
    slug: { type: String, required: true, unique: true },
    content: {
      es: { type: String, required: true },
      en: { type: String, required: true },
    },
    excerpt: {
      es: { type: String, required: true },
      en: { type: String, required: true },
    },
    category: {
      type: String,
      enum: ['novedades', 'curiosidades', 'analisis'],
      required: true,
    },
    imageUrl: { type: String, required: true },
    imageAlt: { type: String, required: true },
    animeName: { type: String, required: true },
    tags: [{ type: String }],
    published: { type: Boolean, default: true },
  },
  { timestamps: true }
);

export default mongoose.models.Article || mongoose.model('Article', ArticleSchema);
