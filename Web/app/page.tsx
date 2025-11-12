"use client"

import { useState } from "react"
import type { DocumentResponse, ProcessedContent } from "./lib/api"
import { DocumentUploader } from "./components/DocumentUploader"
import { DocumentViewer } from "./components/DocumentViewer"
import { ProcessingStatus } from "./components/ProcessingStatus"

export default function Home() {
  const [uploadedDocument, setUploadedDocument] = useState<DocumentResponse | null>(null)
  const [processingStatus, setProcessingStatus] = useState<"idle" | "uploaded" | "processing" | "completed" | "failed">("idle")
  const [documentContent, setDocumentContent] = useState<ProcessedContent | null>(null)

  const handleUploadSuccess = (document: DocumentResponse) => {
    setUploadedDocument(document)
    setProcessingStatus("uploaded")
  }

  const handleProcessingComplete = (content: ProcessedContent) => {
    setDocumentContent(content)
    setProcessingStatus("completed")
  }

  const handleStatusUpdate = (status: string) => {
    setProcessingStatus(status)
  }

  if (processingStatus === "idle" && !uploadedDocument) {
    return (
      <div className="min-h-screen bg-black text-white">
        {/* Hero Section */}
        <div className="min-h-screen flex items-center justify-center px-6">
          <div className="max-w-5xl w-full">
            <div className="text-center mb-16">
              {/* Scipher title in hero */}
              <h1
                style={{ fontFamily: "var(--font-playfair)" }}
                className="text-7xl md:text-8xl font-light tracking-tight mb-8 text-white"
              >
                scipher
              </h1>

              <p className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto mb-4 font-light leading-relaxed">
                Transform research papers into structured intelligence
              </p>

              <p className="text-sm md:text-base text-gray-500 max-w-2xl mx-auto mb-12">
                Upload your PDFs and let AI extract insights, summarize content, and organize information with surgical
                precision.
              </p>

              {/* CTA Buttons */}
              <div className="flex gap-4 justify-center mb-20">
                <button
                  onClick={() => document.getElementById("uploader-section")?.scrollIntoView({ behavior: "smooth" })}
                  className="px-8 py-3 bg-white text-black font-semibold rounded-lg hover:bg-gray-200 transition transform hover:scale-105"
                >
                  Start Analyzing
                </button>
                <button className="px-8 py-3 border border-gray-700 text-white font-semibold rounded-lg hover:border-gray-400 hover:bg-gray-900/50 transition">
                  View Demo
                </button>
              </div>
            </div>

            {/* Features Grid */}
            <div className="mb-24">
              <div className="grid md:grid-cols-3 gap-8">
                {[
                  { title: "Instant Processing", desc: "Analyze papers in seconds with advanced AI algorithms" },
                  { title: "Smart Extraction", desc: "Automatically identify sections, abstracts, and citations" },
                  { title: "Deep Insights", desc: "Get structured summaries and AI-powered analysis" },
                ].map((feature, i) => (
                  <div
                    key={i}
                    className="group border border-gray-800 rounded-lg p-8 hover:border-gray-600 transition bg-gray-950/50 backdrop-blur"
                  >
                    <h3 style={{ fontFamily: "var(--font-playfair)" }} className="text-2xl font-light mb-3 text-white">
                      {feature.title}
                    </h3>
                    <p className="text-gray-400 text-sm leading-relaxed">{feature.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* How It Works - Minimal */}
            <div className="mb-24">
              <h2 style={{ fontFamily: "var(--font-playfair)" }} className="text-4xl font-light text-center mb-12">
                Simple workflow
              </h2>
              <div className="max-w-2xl mx-auto space-y-8">
                {[
                  { step: "01", title: "Upload PDF", desc: "Drag and drop your research papers" },
                  { step: "02", title: "AI Processing", desc: "Automatic analysis and extraction" },
                  { step: "03", title: "Explore Results", desc: "Review insights and structured content" },
                ].map((item, i) => (
                  <div key={i} className="flex gap-6 items-start border-l border-gray-800 pl-6">
                    <span className="text-gray-500 text-sm font-light flex-shrink-0 pt-1">{item.step}</span>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-white mb-1">{item.title}</h3>
                      <p className="text-gray-500 text-sm">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Upload Section */}
            <div id="uploader-section" className="mb-12">
              <div className="border border-gray-800 rounded-lg p-12 bg-gray-950/50 backdrop-blur">
                <h3 style={{ fontFamily: "var(--font-playfair)" }} className="text-3xl font-light text-center mb-8">
                  Ready to begin?
                </h3>
                <DocumentUploader onUploadSuccess={handleUploadSuccess} />
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-gray-800 pt-12 pb-8 text-center text-gray-600 text-sm">
              <p>Unlock the power of your research</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="w-full px-6 py-8">
        <div className="flex items-center gap-3 mb-8">
          <button
            onClick={() => {
              setUploadedDocument(null)
              setProcessingStatus("idle")
              setDocumentContent(null)
            }}
            className="text-gray-500 hover:text-white transition"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <div>
            <h1 style={{ fontFamily: "var(--font-playfair)" }} className="text-2xl font-light text-white">
              scipher
            </h1>
            <p className="text-sm text-gray-500">Processing your research paper</p>
          </div>
        </div>

        <div className="w-full">
          {!uploadedDocument ? (
            <DocumentUploader onUploadSuccess={handleUploadSuccess} />
          ) : processingStatus === "completed" && documentContent ? (
            <DocumentViewer
              document={documentContent}
              onNewUpload={() => {
                setUploadedDocument(null)
                setProcessingStatus("idle")
                setDocumentContent(null)
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
  )
}
