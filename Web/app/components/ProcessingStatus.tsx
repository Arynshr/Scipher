'use client';

import { useState, useEffect } from 'react';
import { apiClient, type DocumentResponse, type ProcessedContent } from "../lib/api";

interface ProcessingStatusProps {
  document: DocumentResponse;
  status: string;
  onStatusUpdate: (status: string) => void;
  onProcessingComplete: (content: ProcessedContent) => void;
}

export function ProcessingStatus({ 
  document, 
  status, 
  onStatusUpdate, 
  onProcessingComplete 
}: ProcessingStatusProps) {
  const [currentStatus, setCurrentStatus] = useState(status);
  const [error, setError] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (isMounted && (currentStatus === 'uploaded' || currentStatus === 'processing')) {
      const interval = setInterval(async () => {
        try {
          const statusData = await apiClient.getProcessingStatus(document.id);
          const newStatus = statusData.status.toLowerCase();

          setCurrentStatus(newStatus);
          onStatusUpdate(newStatus);

          if (newStatus === 'completed') {
            try {
              const content = await apiClient.getDocumentContent(document.id);
              onProcessingComplete(content);
            } catch (contentErr) {
              setError(`Failed to fetch document content: ${contentErr instanceof Error ? contentErr.message : 'Unknown error'}`);
            }
          } else if (newStatus === 'failed') {
            setError(statusData.error_message || 'Processing failed');
          }
        } catch (err) {
          if (err instanceof TypeError && err.message.includes('fetch')) {
            setError('Network error: Unable to connect to server');
          } else {
            setError(err instanceof Error ? err.message : 'Failed to check status');
          }
        }
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [isMounted, currentStatus, document.id, onStatusUpdate, onProcessingComplete]);

  const getStatusIcon = () => {
    switch (currentStatus) {
      case 'uploaded':
        return (
          <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'processing':
        return (
          <svg className="w-8 h-8 text-yellow-500 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case 'completed':
        return (
          <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getStatusMessage = () => {
    switch (currentStatus) {
      case 'uploaded':
        return 'Document uploaded successfully. Processing will begin shortly...';
      case 'processing':
        return 'Processing your document. This may take a few minutes...';
      case 'completed':
        return 'Document processing completed successfully!';
      case 'failed':
        return 'Document processing failed.';
      default:
        return 'Unknown status';
    }
  };

  const getStatusColor = () => {
    switch (currentStatus) {
      case 'uploaded':
        return 'text-blue-600 dark:text-blue-400';
      case 'processing':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'completed':
        return 'text-green-600 dark:text-green-400';
      case 'failed':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (!isMounted) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <svg className="w-8 h-8 text-gray-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
            Loading Processing Status
          </h2>
          <p className="text-gray-500 dark:text-gray-400">
            Please wait while we initialize the status monitoring...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
      <div className="text-center">
        <div className="flex justify-center mb-4">
          {getStatusIcon()}
        </div>
        
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
          Processing Status
        </h2>
        
        <p className={`text-lg font-medium mb-4 ${getStatusColor()}`}>
          {getStatusMessage()}
        </p>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-2">Document Details</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            <strong>Filename:</strong> {document.original_filename || document.filename}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            <strong>File Size:</strong> {document.file_size ? `${(document.file_size / 1024 / 1024).toFixed(2)} MB` : 'Unknown'}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            <strong>Document ID:</strong> {document.id}
          </p>
        </div>

        {currentStatus === 'processing' && (
          <div className="mb-4">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              Extracting text and images from your document...
            </p>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
