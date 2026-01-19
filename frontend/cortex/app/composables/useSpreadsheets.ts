import { ref } from 'vue';
import type { SheetMetadata, SpreadsheetSourceConfig } from '~/types';

export function useSpreadsheets() {
  const { apiUrl } = useApi();
  const loading = ref(false);
  const error = ref<string | null>(null);

  /**
   * Upload CSV files to temporary storage
   */
  async function uploadFiles(files: File[], environmentId: string, overwrite: boolean = false) {
    loading.value = true;
    error.value = null;

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });
      console.log("Overwrite:", overwrite);
      const response = await $fetch<{
        file_ids: string[];
        files: Array<{ id: string; name: string; extension: string; size: number; mime_type: string }>;
        message: string;
      }>(apiUrl('/api/v1/data/sources/upload'), {
        method: 'POST',
        body: formData,
        query: {
          environment_id: environmentId,
          overwrite: overwrite.toString()
        }
      });

      return response;
    } catch (err: any) {
      console.error('Failed to upload files:', err);
      
      // Check if it's a duplicate file error
      let errorDetail = err.data?.detail || err.data;
      
      // Parse if it's a string
      if (typeof errorDetail === 'string') {
        try {
          // Try JSON parse first
          errorDetail = JSON.parse(errorDetail);
        } catch (parseErr) {
          // If JSON parsing fails, try to extract values from Python dict string using regex
          try {
            // Use regex to extract values from Python dict format
            // This handles both 'key': 'value' and "key": "value" formats
            const errorMatch = errorDetail.match(/'error':\s*'([^']*)'/) || errorDetail.match(/"error":\s*"([^"]*)"/);
            const filenameMatch = errorDetail.match(/'filename':\s*'([^']*)'/) || errorDetail.match(/"filename":\s*"([^"]*)"/);
            const fileIdMatch = errorDetail.match(/'file_id':\s*'([^']*)'/) || errorDetail.match(/"file_id":\s*"([^"]*)"/);
            const messageMatch = errorDetail.match(/'message':\s*"([^"]*)"/) || errorDetail.match(/"message":\s*"([^"]*)"/);
            
            if (errorMatch && filenameMatch) {
              errorDetail = {
                error: errorMatch[1],
                filename: filenameMatch[1],
                file_id: fileIdMatch?.[1],
                message: messageMatch?.[1]
              };
            }
          } catch (pythonParseErr) {
            // If regex parsing fails, keep as string
            console.error('Failed to parse error detail:', parseErr, pythonParseErr);
          }
        }
      }
      
      if (err.status === 409 && errorDetail?.error === 'StorageFileAlreadyExists') {
        throw {
          type: 'StorageFileAlreadyExists',
          filename: errorDetail.filename,
          fileId: errorDetail.file_id,
          message: errorDetail.message
        };
      }
      
      error.value = err.message || 'Failed to upload files';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * List all uploaded files
   */
  async function listUploadedFiles(environmentId: string, limit?: number) {
    loading.value = true;
    error.value = null;

    try {
      const query: Record<string, any> = {
        environment_id: environmentId
      };
      if (limit) {
        query.limit = limit;
      }

      const response = await $fetch<{
        files: Array<{
          id: string;
          name: string;
          extension: string;
          size: number;
          mime_type: string;
          hash: string;
          created_at: string;
          updated_at: string;
        }>;
      }>(apiUrl('/api/v1/data/sources/files'), {
        method: 'GET',
        query
      });

      return response.files;
    } catch (err: any) {
      console.error('Failed to list files:', err);
      error.value = err.message || 'Failed to list files';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Discover available sheets/tables from a data source
   */
  async function discoverSheets(config: {
    provider_type: 'csv' | 'gsheets';
    session_id?: string;
    spreadsheet_id?: string;
    service_account_json?: Record<string, any>;
    access_token?: string;
  }) {
    loading.value = true;
    error.value = null;

    try {
      const response = await $fetch<{
        tables: SheetMetadata[];
      }>(apiUrl('/api/v1/data/sources/discover'), {
        method: 'POST',
        body: config,
      });

      return response.tables;
    } catch (err: any) {
      console.error('Failed to discover sheets:', err);
      error.value = err.message || 'Failed to discover sheets';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Preview data from a specific sheet
   */
  async function previewSheet(config: {
    provider_type: 'csv' | 'gsheets';
    session_id?: string;
    spreadsheet_id?: string;
    service_account_json?: Record<string, any>;
    table_name: string;
    limit?: number;
  }) {
    loading.value = true;
    error.value = null;

    try {
      const response = await $fetch<{
        columns: string[];
        rows: Array<Array<string | null>>;
        total_rows: number;
      }>(apiUrl('/api/v1/data/sources/preview'), {
        method: 'POST',
        body: config,
      });

      return response;
    } catch (err: any) {
      console.error('Failed to preview sheet:', err);
      error.value = err.message || 'Failed to preview sheet';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Refresh a spreadsheet data source
   */
  async function refreshDataSource(dataSourceId: string) {
    loading.value = true;
    error.value = null;

    try {
      const response = await $fetch<{
        refreshed_tables: string[];
        unchanged_tables: string[];
        last_synced: string;
      }>(apiUrl(`/api/v1/data/sources/${dataSourceId}/refresh`), {
        method: 'POST',
      });

      return response;
    } catch (err: any) {
      console.error('Failed to refresh data source:', err);
      error.value = err.message || 'Failed to refresh data source';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Get status of a spreadsheet data source
   */
  async function getDataSourceStatus(dataSourceId: string) {
    loading.value = true;
    error.value = null;

    try {
      const response = await $fetch<{
        source_id: string;
        source_type: string;
        provider_type: string;
        selected_sheets: string[];
        table_mappings: Record<string, string>;
        last_synced: string;
        sqlite_path: string;
      }>(apiUrl(`/api/v1/data/sources/${dataSourceId}/status`), {
        method: 'GET',
      });

      return response;
    } catch (err: any) {
      console.error('Failed to get data source status:', err);
      error.value = err.message || 'Failed to get data source status';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return {
    loading,
    error,
    uploadFiles,
    listUploadedFiles,
    discoverSheets,
    previewSheet,
    refreshDataSource,
    getDataSourceStatus,
  };
}
