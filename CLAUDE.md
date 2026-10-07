# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Converter is a project for converting PDF files to various formats or extracting/transforming PDF content. The architecture depends on the specific use case (text extraction, format conversion, OCR, etc.), but this document outlines common patterns and workflows.

## Common Commands

Replace these with actual commands once the project is set up:

### Development
```bash
# Install dependencies
npm install
# or: pip install -r requirements.txt
# or: cargo build

# Start development server (if applicable)
npm run dev

# Run the application
npm start
# or: python main.py
```

### Testing
```bash
# Run all tests
npm test
# or: pytest

# Run a single test file
npm test -- path/to/test.js
# or: pytest tests/test_file.py

# Run tests with coverage
npm run test:coverage
```

### Code Quality
```bash
# Lint code
npm run lint

# Format code
npm run format

# Type check (if using TypeScript)
npm run type-check
```

## Architecture Patterns

### 1. **File Input Handling**
- **Validation**: PDF files should be validated before processing (magic bytes check, file size limits).
- **Temporary Storage**: Large files or intermediate states should use temp directories, not memory.
- **Error Recovery**: Implement graceful handling for corrupted PDFs, incomplete uploads, or unsupported versions.

### 2. **PDF Processing Pipeline**
A typical PDF conversion flow:
```
Input PDF → Parse → Extract/Transform → Output Format → Stream/Save
```

Key considerations:
- **Library Choice**: Depends on language (e.g., `pdfkit`/`pdf-parse` for Node.js, `PyPDF2`/`pdfplumber` for Python, `pdfium-render` for Rust)
- **Streaming vs. In-Memory**: For large files, stream processing is preferred to avoid memory exhaustion
- **Format Support**: Keep track of supported PDF versions and encryption methods

### 3. **Output Format Strategy**
- Separate conversion logic by output type (Text, Images, JSON, etc.)
- Each converter should be a distinct module with consistent error handling
- Support batch processing when applicable

### 4. **Error Handling**
- Distinguish between recoverable errors (malformed page) and fatal errors (invalid PDF)
- Log detailed error context (file info, processing stage, system state)
- Return meaningful error messages to users (not stack traces)

## Testing Strategy

### Unit Tests
- Test conversion functions with sample PDFs of varying complexity
- Mock file I/O to avoid flakiness
- Include edge cases: empty PDFs, single-page vs. multi-page, encrypted PDFs, different PDF versions

### Integration Tests
- Test with real PDF files
- Verify output correctness (spot-check extracted text, image quality, etc.)
- Test error scenarios (corrupted files, unsupported features)

### Performance Tests
- Benchmark large file processing (time and memory)
- Set acceptable thresholds for conversion speed

## File Organization

**Suggested structure** (adapt based on tech stack):
```
pdf_converter/
├── src/
│   ├── core/           # PDF parsing and core logic
│   ├── converters/     # Output-specific converters (text, image, etc.)
│   ├── utils/          # File handling, validation, helpers
│   └── types/          # Type definitions (if using TS)
├── tests/              # Test files (mirror src structure)
├── samples/            # Sample PDFs for testing
└── docs/               # Architecture and API docs
```

## Key Considerations

### Performance
- **Memory Management**: PDFs can be large; avoid loading entire files into memory
- **Parallelization**: For batch processing, consider parallel workers (Node clusters, Python multiprocessing)
- **Caching**: Cache parsed PDF structures if reprocessing the same file

### Security
- **File Upload Validation**: Check file type, size, and content before processing
- **Path Traversal**: Never use unsanitized file paths from user input
- **Resource Limits**: Set timeouts and memory limits for PDF processing to prevent DoS

### Compatibility
- **PDF Versions**: Target PDF 1.4 - 2.0 at minimum
- **Character Encoding**: Handle various text encodings in PDFs
- **Dependent Libraries**: Keep PDF processing libraries updated for security patches

## Debugging Tips

- **Enable Verbose Logging**: Add detailed logs around PDF parsing stages to pinpoint failures
- **Use PDF Inspection Tools**: `pdfinfo`, `pdftotext`, or similar tools to inspect PDFs externally
- **Incremental Testing**: Test with progressively more complex PDFs to isolate issues
- **Check Library Docs**: Different PDF libraries have different quirks; consult official docs for edge cases

## Future Extensions

- **Streaming Output**: For large conversions, stream results to clients instead of buffering
- **Format Options**: Add parameters for conversion behavior (e.g., image quality, text extraction mode)
- **Monitoring**: Add metrics for processing time, success rate, and error types
- **Async Processing**: For long-running conversions, use a job queue (Bull, Celery, etc.)
