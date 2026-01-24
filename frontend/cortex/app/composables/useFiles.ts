import { useApi } from '~/composables/useApi';
import type { FileDependenciesError } from '~/types';

export function useFiles() {
  const { apiUrl } = useApi();

  /**
   * Delete a file
   * @param fileId - File ID
   * @param environmentId - Environment ID for multi-tenancy validation
   * @param cascade - If true, delete all dependent data sources and metrics
   * @returns Promise that resolves when deleted or rejects with error details
   */
  async function deleteFile(
    fileId: string,
    environmentId: string,
    cascade: boolean = false
  ) {
    try {
      await $fetch(
        apiUrl(`/api/v1/data/sources/files/${fileId}?environment_id=${environmentId}${cascade ? '&cascade=true' : ''}`),
        { method: 'DELETE' }
      );
      return { success: true };
    } catch (err: any) {
      console.error('Failed to delete file:', err);

      // Extract and parse error detail
      let errorDetail = err.data?.detail || err.data;
      if (typeof errorDetail === 'string') {
        try {
          errorDetail = JSON.parse(errorDetail);
        } catch (parseErr) {
          console.error('Failed to parse error detail:', parseErr);
        }
      }

      // If 409 Conflict, throw structured dependencies error
      if (err.status === 409 && errorDetail?.error === 'FileHasDependencies') {
        throw {
          error: 'FileHasDependencies',
          message: errorDetail.message,
          file_id: errorDetail.file_id,
          dependencies: errorDetail.dependencies
        } as FileDependenciesError;
      }

      throw err;
    }
  }

  return { deleteFile };
}
