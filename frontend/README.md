# Scipher Frontend

A Next.js frontend application for the Scipher research paper simplification tool. This application allows users to upload PDF research papers and view parsed content with images extracted using Docling.

## Features

- **PDF Upload**: Drag and drop or click to upload PDF files (max 50MB)
- **Real-time Processing Status**: Live updates on document processing status
- **Document Viewer**: View parsed content in multiple formats:
  - Overview with document metadata
  - Structured sections with content
  - Full text view
- **Image Display**: View extracted images from documents
- **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

- Node.js 18+ 
- npm or yarn
- Running Scipher backend server (FastAPI)

## Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables (optional):
Create a `.env.local` file in the root directory:
```env
# Backend API URL - change this if your backend runs on a different port
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## Development

1. Start the development server:
```bash
npm run dev
```

2. Open [http://localhost:3000](http://localhost:3000) in your browser

## Backend Integration

The frontend connects to the FastAPI backend with the following endpoints:

- `POST /api/upload` - Upload PDF files
- `GET /api/status/{doc_id}` - Check processing status
- `GET /api/document/{doc_id}` - Get parsed document content
- `GET /api/document/{doc_id}/sections` - Get document sections
- `GET /api/document/{doc_id}/text` - Get raw text content
- `DELETE /api/document/{doc_id}` - Delete document

## Usage

1. **Upload Document**: 
   - Drag and drop a PDF file or click "Choose File"
   - Wait for upload confirmation

2. **Processing**: 
   - Monitor real-time processing status
   - Processing typically takes 1-3 minutes depending on document size

3. **View Results**:
   - **Overview**: See document metadata and section summary
   - **Sections**: Browse structured content by section type
   - **Full Text**: View complete extracted text

## File Structure

```
src/
├── app/
│   ├── components/
│   │   ├── DocumentUploader.tsx    # File upload component
│   │   ├── ProcessingStatus.tsx    # Status monitoring component
│   │   └── DocumentViewer.tsx      # Document display component
│   ├── lib/
│   │   └── api.ts                  # API client and types
│   ├── layout.tsx                  # Root layout
│   └── page.tsx                    # Main page component
```

## Technologies Used

- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React 19** - UI library

## API Types

The application uses TypeScript interfaces for type safety:

- `DocumentResponse` - Upload response
- `StatusResponse` - Processing status
- `ProcessedContent` - Parsed document data
- `SectionSchema` - Document section structure

## Error Handling

The application includes comprehensive error handling for:
- File upload failures
- Network connectivity issues
- Processing errors
- Invalid file formats
- File size limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Scipher research paper simplification tool.
