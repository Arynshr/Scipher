'use client';

import { useState } from 'react';

interface DocumentViewerProps {
  document: any;
  onNewUpload: () => void;
}

export function DocumentViewer({ document, onNewUpload }: DocumentViewerProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'sections' | 'text'>('overview');

  const renderImages = (content: string) => {
    if (!content || typeof content !== 'string') {
      return [];
    }
    
    // Simple regex to find image references in the content
    const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
    const images = [];
    let match;
    
    while ((match = imageRegex.exec(content)) !== null) {
      // Sanitize image data
      const alt = match[1] ? match[1].substring(0, 100) : 'Image'; // Limit alt text length
      const src = match[2] ? match[2].substring(0, 500) : ''; // Limit src length
      
      if (src) {
        images.push({
          alt,
          src
        });
      }
    }
    
    return images;
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Document Overview
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Filename</p>
                  <p className="text-gray-900 dark:text-white">{document?.filename || 'Unknown'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">File Size</p>
                  <p className="text-gray-900 dark:text-white">
                    {document.metadata?.file_size ? `${(document.metadata.file_size / 1024 / 1024).toFixed(2)} MB` : 'Unknown'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Upload Date</p>
                  <p className="text-gray-900 dark:text-white">
                    {document.metadata?.upload_date ? new Date(document.metadata.upload_date).toLocaleDateString() : 'Unknown'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Sections</p>
                  <p className="text-gray-900 dark:text-white">{document.sections?.length || 0}</p>
                </div>
              </div>
            </div>

            {document.sections && document.sections.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Document Sections
                </h3>
                <div className="space-y-3">
                  {document.sections.map((section: any, index: number) => (
                    <div key={section.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white capitalize">
                          {section.section_type.replace('_', ' ')}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {section.content?.length > 100 
                            ? `${section.content.substring(0, 100)}...` 
                            : section.content}
                        </p>
                      </div>
                      <span className="text-xs text-gray-400 dark:text-gray-500">
                        #{section.order + 1}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'sections':
        return (
          <div className="space-y-6">
            {document.sections && document.sections.length > 0 ? (
              document.sections.map((section: any, index: number) => (
                <div key={section.id} className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white capitalize">
                      {section.section_type.replace('_', ' ')}
                    </h3>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      Section {section.order + 1}
                    </span>
                  </div>
                  
                  <div className="prose dark:prose-invert max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
                      {section.content}
                    </div>
                  </div>

                  {/* Render images if any */}
                  {renderImages(section.content).length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Images</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {renderImages(section.content).map((image: any, imgIndex: number) => (
                          <div key={imgIndex} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{image.alt}</p>
                            <div className="bg-gray-100 dark:bg-gray-700 rounded p-4 text-center">
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                Image: {image.src}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400">No sections found in this document.</p>
              </div>
            )}
          </div>
        );

      case 'text':
        return (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Full Document Text
            </h3>
            <div className="prose dark:prose-invert max-w-none">
              <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300 max-h-96 overflow-y-auto">
                {document.text || 'No text content available.'}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Document Analysis Complete
          </h2>
          <p className="text-gray-600 dark:text-gray-300">
            {document.filename}
          </p>
        </div>
        <button
          onClick={onNewUpload}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Upload New Document
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'sections', label: 'Sections' },
            { id: 'text', label: 'Full Text' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {renderContent()}
    </div>
  );
}
