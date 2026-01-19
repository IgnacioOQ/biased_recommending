
/**
 * Application configuration
 * 
 * VITE_API_URL is set in Vercel environment variables for production.
 * If not set (local development), it defaults to http://localhost:8000.
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
