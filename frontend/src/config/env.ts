/**
 * Environment configuration with validation.
 * Centralizes all environment variable access.
 */

const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = import.meta.env[key] || defaultValue;
  if (!value && !defaultValue) {
    throw new Error(`Missing environment variable: ${key}`);
  }
  return value || defaultValue || "";
};

export const env = {
  apiBaseUrl: getEnvVar("VITE_API_BASE_URL", "http://localhost:8000"),
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const;

