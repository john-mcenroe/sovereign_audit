// API configuration
// In production, set VITE_API_URL environment variable (no trailing slash)
const raw = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const API_URL = raw.replace(/\/+$/, '')
