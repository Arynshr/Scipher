'use client';

import { useState, useRef } from 'react';
import { DocumentUploader } from './components/DocumentUploader';
import { DocumentViewer } from './components/DocumentViewer';
import { ProcessingStatus } from './components/ProcessingStatus';

export default function Home() {
  const [uploadedDocument, setUploadedDocument] = useState<any>(null);
  const [processingStatus, setProcessingStatus] = useState<string>('idle');
  const [documentContent, setDocumentContent] = useState<any>(null);

  const handleUploadSuccess = (document: any) => {
    setUploadedDocument(document);
    setProcessingStatus('uploaded');
  };

  const handleProcessingComplete = (content: any) => {
    setDocumentContent(content);
    setProcessingStatus('completed');
  };

  const handleStatusUpdate = (status: string) => {
    setProcessingStatus(status);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Scipher
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-2">
            Research Paper Simplification Tool
          </p>
          <p className="text-gray-500 dark:text-gray-400">
            Upload your PDF research papers and get AI-powered parsing with images
          </p>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {!uploadedDocument ? (
            <DocumentUploader onUploadSuccess={handleUploadSuccess} />
          ) : processingStatus === 'completed' && documentContent ? (
            <DocumentViewer 
              document={documentContent} 
              onNewUpload={() => {
                setUploadedDocument(null);
                setProcessingStatus('idle');
                setDocumentContent(null);
              }}
            />
          ) : (
            <ProcessingStatus 
              document={uploadedDocument}
              status={processingStatus}
              onStatusUpdate={handleStatusUpdate}
              onProcessingComplete={handleProcessingComplete}
            />
          )}
        </div>
      </div>
    </div>
  );
}
