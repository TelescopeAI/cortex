import { ref } from 'vue';
import type { Ref } from 'vue';

export function useApi() {
  const config = useRuntimeConfig();
  const apiBaseUrl = config.public.apiBaseUrl;

  function apiUrl(path: string): string {
    return `${apiBaseUrl}${path}`;
  }

  return {
    apiBaseUrl,
    apiUrl
  };
} 