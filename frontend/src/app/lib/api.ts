const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export interface DocumentResponse {
  id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  status: string;
  upload_date: string;
}

export interface StatusResponse {
  id: string;
  status: string;
  message: string;
  error_message?: string;
}

export interface SectionSchema {
  id: string;
  document_id: string;
  section_type: string;
  content: string;
  order: number;
}

export interface ProcessedContent {
  id: string;
  filename: string;
  text: string;
  sections: SectionSchema[];
  metadata: {
    upload_date: string;
    file_size: number;
    [key: string]: any;
  };
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async uploadDocument(file: File): Promise<DocumentResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Upload failed');
    }

    return response.json();
  }

  async getProcessingStatus(docId: string): Promise<StatusResponse> {
    const response = await fetch(`${this.baseUrl}/api/status/${docId}`);

    if (!response.ok) {
      throw new Error('Failed to fetch status');
    }

    return response.json();
  }

  async getDocumentContent(docId: string): Promise<ProcessedContent> {
    const response = await fetch(`${this.baseUrl}/api/document/${docId}`);

    if (!response.ok) {
      throw new Error('Failed to fetch document content');
    }

    return response.json();
  }

  async getDocumentSections(docId: string, sectionType?: string): Promise<SectionSchema[]> {
    const url = sectionType 
      ? `${this.baseUrl}/api/document/${docId}/sections?section_type=${sectionType}`
      : `${this.baseUrl}/api/document/${docId}/sections`;

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error('Failed to fetch document sections');
    }

    return response.json();
  }

  async getDocumentText(docId: string): Promise<{ id: string; filename: string; text: string; status: string }> {
    const response = await fetch(`${this.baseUrl}/api/document/${docId}/text`);

    if (!response.ok) {
      throw new Error('Failed to fetch document text');
    }

    return response.json();
  }

  async deleteDocument(docId: string): Promise<{ message: string; id: string }> {
    const response = await fetch(`${this.baseUrl}/api/document/${docId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete document');
    }

    return response.json();
  }

  async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/api/health`);

    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();
