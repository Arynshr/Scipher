'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { apiClient } from "../lib/api";
import type { DocumentSummaryResponse, ProcessedContent } from "../lib/api";

interface DocumentViewerProps {
  document: ProcessedContent;
  onNewUpload: () => void;
}

type SummaryKey = 'easy' | 'intermediate' | 'technical';

const SUMMARY_SECTIONS: Array<{ key: SummaryKey; label: string; description: string }> = [
  { key: 'easy', label: 'Easy', description: 'High-level overview with approachable language.' },
  { key: 'intermediate', label: 'Intermediate', description: 'Balanced summary with key findings and context.' },
  { key: 'technical', label: 'Technical', description: 'Detailed synthesis preserving terminology and nuance.' },
];

export function DocumentViewer({ document, onNewUpload }: DocumentViewerProps) {
  const [markdownContent, setMarkdownContent] = useState<string>('');
  const [markdownLoading, setMarkdownLoading] = useState<boolean>(true);
  const [markdownError, setMarkdownError] = useState<string | null>(null);

  const [summary, setSummary] = useState<DocumentSummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [summaryFetchKey, setSummaryFetchKey] = useState<number>(0);

  useEffect(() => {
    let isMounted = true;
    const fetchMarkdown = async () => {
      try {
        setMarkdownLoading(true);
        const content = await apiClient.getDocumentMarkdown(document.id);
        if (!isMounted) return;
        setMarkdownContent(content);
        setMarkdownError(null);
      } catch (err) {
        console.error('Failed to fetch markdown:', err);
        if (!isMounted) return;
        setMarkdownError('Failed to load document content');
        if (document.text) {
          setMarkdownContent(document.text);
        }
      } finally {
        if (isMounted) {
          setMarkdownLoading(false);
        }
      }
    };

    if (document.id) {
      fetchMarkdown();
    }

    return () => {
      isMounted = false;
    };
  }, [document.id, document.text]);

  useEffect(() => {
    let isMounted = true;
    const fetchSummary = async () => {
      try {
        setSummaryLoading(true);
        setSummaryError(null);
        setSummary(null);
        const response = await apiClient.getDocumentSummary(document.id);
        if (!isMounted) return;
        setSummary(response);
      } catch (err) {
        console.error('Failed to fetch summary:', err);
        if (!isMounted) return;
        setSummaryError('Failed to generate summaries');
      } finally {
        if (isMounted) {
          setSummaryLoading(false);
        }
      }
    };

    if (document.id) {
      fetchSummary();
    }

    return () => {
      isMounted = false;
    };
  }, [document.id, summaryFetchKey]);

  const handleRefreshSummaries = () => {
    setSummaryFetchKey((prev) => prev + 1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {document.original_filename || document.filename}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Document processed successfully
          </p>
        </div>
        <button
          onClick={onNewUpload}
          className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Upload New Document
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 h-[calc(100vh-12rem)]">
        {/* Document Viewer - 50% width, independent scroll */}
        <div className="flex flex-col h-full">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 h-full flex flex-col">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Processed Document</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              {markdownLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600 dark:text-gray-400">Loading document...</span>
                </div>
              ) : markdownError && !markdownContent ? (
                <div className="text-center py-8">
                  <p className="text-red-600 dark:text-red-400">{markdownError}</p>
                </div>
              ) : (
                <div className="prose prose-lg dark:prose-invert max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({node, ...props}) => <h1 className="text-3xl font-bold mt-8 mb-4 text-gray-900 dark:text-white" {...props} />,
                      h2: ({node, ...props}) => <h2 className="text-2xl font-semibold mt-6 mb-3 text-gray-900 dark:text-white" {...props} />,
                      h3: ({node, ...props}) => <h3 className="text-xl font-semibold mt-4 mb-2 text-gray-900 dark:text-white" {...props} />,
                      p: ({node, ...props}) => <p className="mb-4 text-gray-700 dark:text-gray-300 leading-relaxed" {...props} />,
                      ul: ({node, ...props}) => <ul className="list-disc list-inside mb-4 space-y-2 text-gray-700 dark:text-gray-300" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-4 space-y-2 text-gray-700 dark:text-gray-300" {...props} />,
                      li: ({node, ...props}) => <li className="ml-4" {...props} />,
                      code: ({node, inline, ...props}: any) => 
                        inline ? (
                          <code className="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800 dark:text-gray-200" {...props} />
                        ) : (
                          <code className="block bg-gray-100 dark:bg-gray-700 p-4 rounded-lg text-sm font-mono text-gray-800 dark:text-gray-200 overflow-x-auto mb-4" {...props} />
                        ),
                      pre: ({node, ...props}) => <pre className="mb-4" {...props} />,
                      blockquote: ({node, ...props}) => (
                        <blockquote className="border-l-4 border-blue-500 pl-4 italic my-4 text-gray-600 dark:text-gray-400" {...props} />
                      ),
                      a: ({node, ...props}) => (
                        <a className="text-blue-600 dark:text-blue-400 hover:underline" {...props} />
                      ),
                      table: ({node, ...props}) => (
                        <div className="overflow-x-auto mb-4">
                          <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600" {...props} />
                        </div>
                      ),
                      th: ({node, ...props}) => (
                        <th className="border border-gray-300 dark:border-gray-600 px-4 py-2 bg-gray-100 dark:bg-gray-700 font-semibold text-left" {...props} />
                      ),
                      td: ({node, ...props}) => (
                        <td className="border border-gray-300 dark:border-gray-600 px-4 py-2" {...props} />
                      ),
                    }}
                  >
                    {markdownContent || 'No content available.'}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Summary Viewer - 50% width, independent scroll */}
        <div className="flex flex-col h-full">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 h-full flex flex-col">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white">AI Summaries</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Three difficulty levels generated on demand.</p>
                </div>
                <button
                  onClick={handleRefreshSummaries}
                  disabled={summaryLoading}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m0 0A7 7 0 0112 5a7 7 0 110 14 7 7 0 01-5.418-2.418m0 0H4v5" />
                  </svg>
                  Refresh
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {summaryLoading ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="mt-3 text-gray-600 dark:text-gray-400">Generating summaries...</span>
                </div>
              ) : summaryError ? (
                <div className="flex flex-col items-center justify-center text-center py-8 space-y-3">
                  <p className="text-red-600 dark:text-red-400">{summaryError}</p>
                  <button
                    onClick={handleRefreshSummaries}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Try Again
                  </button>
                </div>
              ) : summary ? (
                <div className="space-y-4">
                  {SUMMARY_SECTIONS.map((section) => (
                    <div key={section.key} className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <h4 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wide">{section.label}</h4>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{section.description}</p>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                        {summary[section.key] || 'Summary unavailable.'}
                      </p>
                    </div>
                  ))}
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Generated from {summary.chunk_count} chunk{summary.chunk_count === 1 ? '' : 's'} covering{' '}
                    {summary.source_characters.toLocaleString()} characters.
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center text-center py-8 space-y-2">
                  <p className="text-gray-600 dark:text-gray-400">Summaries unavailable. Try refreshing.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
