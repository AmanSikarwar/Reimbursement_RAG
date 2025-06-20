# Flutter Integration API Documentation

Complete API reference for integrating the Invoice Reimbursement System with Flutter applications.

## 🌐 Base URL

```
Production: https://your-api-domain.com/api/v1
Development: http://localhost:8000/api/v1
```

## 🔑 Authentication

Currently, the API uses basic authentication. For production, consider implementing JWT or OAuth2.

### Headers

```http
Content-Type: application/json
Accept: application/json
```

For file uploads:

```http
Content-Type: multipart/form-data
```

For streaming endpoints:

```http
Accept: text/event-stream
```

## 📋 API Endpoints

### 1. Health Check Endpoints

#### Quick Health Check

```http
GET /health/quick
```

**Response:**

```json
{
  "status": "ok",
  "timestamp": "2024-06-20T10:30:00Z",
  "uptime": 3600.5
}
```

#### Comprehensive Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-06-20T10:30:00Z",
  "uptime_seconds": 3600.5,
  "services": [
    {
      "name": "vector_store",
      "status": "healthy",
      "response_time_ms": 45.2
    },
    {
      "name": "llm_service",
      "status": "healthy",
      "response_time_ms": 123.4
    }
  ]
}
```

### 2. Invoice Analysis Endpoints

#### Analyze Invoices (Standard)

```http
POST /analyze-invoices
Content-Type: multipart/form-data
```

**Request Body (Form Data):**

- `employee_name` (string): Name of the employee
- `policy_file` (file): PDF file containing HR policy
- `invoices_zip` (file): ZIP file containing invoice PDFs

**Response:**

```json
{
  "success": true,
  "message": "Processed 3 invoices successfully",
  "employee_name": "John Doe",
  "total_invoices": 3,
  "processed_invoices": 3,
  "failed_invoices": 0,
  "results": [
    {
      "filename": "invoice1.pdf",
      "status": "fully_reimbursed",
      "reason": "All expenses comply with company policy",
      "total_amount": 150.00,
      "reimbursement_amount": 150.00,
      "currency": "USD",
      "categories": ["meals", "transportation"],
      "policy_violations": null
    }
  ],
  "processing_errors": null,
  "timestamp": "2024-06-20T10:30:00Z"
}
```

#### Analyze Invoices (Streaming)

```http
POST /analyze-invoices-stream
Content-Type: multipart/form-data
Accept: text/event-stream
```

**Request Body:** Same as standard analysis

**Response (Server-Sent Events):**

```
data: {"type": "metadata", "data": {"employee_name": "John Doe", "total_invoices": 3}, "timestamp": "2024-06-20T10:30:00Z"}

data: {"type": "progress", "data": {"current_invoice": 1, "total_invoices": 3, "stage": "extracting"}, "timestamp": "2024-06-20T10:30:00Z"}

data: {"type": "result", "data": {"filename": "invoice1.pdf", "status": "fully_reimbursed", "amount": 150.00}, "timestamp": "2024-06-20T10:30:00Z"}

data: {"type": "done", "data": {"summary": "Processing complete"}, "timestamp": "2024-06-20T10:30:00Z"}
```

### 3. Chat Endpoints

#### Chat with Invoices (Standard)

```http
POST /chat
Content-Type: application/json
```

**Request Body:**

```json
{
  "query": "Show me all declined invoices for John Doe",
  "session_id": "user123",
  "filters": {
    "employee_name": "John Doe",
    "status": "declined"
  },
  "include_sources": true
}
```

**Response:**

```json
{
  "response": "I found 2 declined invoices for John Doe. Here are the details...",
  "session_id": "user123",
  "sources": [
    {
      "document_id": "doc_123",
      "filename": "invoice2.pdf",
      "employee_name": "John Doe",
      "status": "declined",
      "similarity_score": 0.95,
      "excerpt": "Invoice for business dinner exceeded policy limits..."
    }
  ],
  "retrieved_documents": 2,
  "query_type": "employee_specific",
  "confidence_score": 0.89,
  "suggestions": [
    "Show me approved invoices for John Doe",
    "What was the total amount of declined invoices?",
    "Which invoices had policy violations?"
  ],
  "timestamp": "2024-06-20T10:30:00Z"
}
```

#### Chat with Invoices (Streaming)

```http
POST /chat/stream
Content-Type: application/json
Accept: text/event-stream
```

**Request Body:** Same as standard chat

**Response (Server-Sent Events):**

```
data: {"type": "metadata", "data": {"sources": [], "retrieved_documents": 2}, "timestamp": "2024-06-20T10:30:00Z"}

data: {"type": "content", "data": "I found 2 declined invoices", "timestamp": "2024-06-20T10:30:00Z"}

data: {"type": "content", "data": " for John Doe...", "timestamp": "2024-06-20T10:30:00Z"}

data: {"type": "suggestions", "data": ["Show approved invoices", "Check policy violations"], "timestamp": "2024-06-20T10:30:00Z"}

data: {"type": "done", "data": null, "timestamp": "2024-06-20T10:30:00Z"}
```

#### Chat History Management

```http
# Get chat history
GET /chat/history/{session_id}

# Clear chat history  
DELETE /chat/history/{session_id}
```

## 🎯 Flutter Integration Examples

### 1. HTTP Client Setup

```dart
// api_client.dart
import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';

class ApiClient {
  late Dio _dio;
  static const String baseUrl = 'https://your-api-domain.com/api/v1';
  
  ApiClient() {
    _dio = Dio();
    _dio.options.baseUrl = baseUrl;
    _dio.options.connectTimeout = Duration(seconds: 30);
    _dio.options.receiveTimeout = Duration(minutes: 5); // Long timeout for file processing
    
    // Add logging in debug mode
    if (kDebugMode) {
      _dio.interceptors.add(PrettyDioLogger(
        requestHeader: true,
        requestBody: true,
        responseBody: true,
        responseHeader: false,
        error: true,
        compact: true,
      ));
    }
    
    // Add error handling interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onError: (error, handler) {
        // Handle common errors
        if (error.response?.statusCode == 429) {
          // Rate limit exceeded
          throw RateLimitException();
        } else if (error.response?.statusCode == 413) {
          // File too large
          throw FileTooLargeException();
        }
        handler.next(error);
      },
    ));
  }
  
  Dio get dio => _dio;
}
```

### 2. Invoice Analysis Service

```dart
// invoice_service.dart
import 'dart:io';
import 'package:dio/dio.dart';

class InvoiceService {
  final ApiClient _apiClient;
  
  InvoiceService(this._apiClient);
  
  Future<InvoiceAnalysisResponse> analyzeInvoices({
    required String employeeName,
    required File policyFile,
    required File invoicesZip,
  }) async {
    try {
      FormData formData = FormData.fromMap({
        'employee_name': employeeName,
        'policy_file': await MultipartFile.fromFile(
          policyFile.path,
          filename: 'policy.pdf',
        ),
        'invoices_zip': await MultipartFile.fromFile(
          invoicesZip.path,
          filename: 'invoices.zip',
        ),
      });
      
      Response response = await _apiClient.dio.post(
        '/analyze-invoices',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );
      
      return InvoiceAnalysisResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  Stream<InvoiceAnalysisStreamChunk> analyzeInvoicesStream({
    required String employeeName,
    required File policyFile,
    required File invoicesZip,
  }) async* {
    try {
      FormData formData = FormData.fromMap({
        'employee_name': employeeName,
        'policy_file': await MultipartFile.fromFile(policyFile.path),
        'invoices_zip': await MultipartFile.fromFile(invoicesZip.path),
      });
      
      Response<ResponseBody> response = await _apiClient.dio.post<ResponseBody>(
        '/analyze-invoices-stream',
        data: formData,
        options: Options(
          headers: {
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
          },
          responseType: ResponseType.stream,
        ),
      );
      
      await for (String line in response.data!.stream
          .transform(utf8.decoder)
          .transform(LineSplitter())) {
        if (line.startsWith('data: ')) {
          String jsonData = line.substring(6);
          if (jsonData.trim().isNotEmpty && jsonData != '[DONE]') {
            Map<String, dynamic> data = json.decode(jsonData);
            yield InvoiceAnalysisStreamChunk.fromJson(data);
          }
        }
      }
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  Exception _handleError(DioException e) {
    if (e.response?.data is Map<String, dynamic>) {
      final errorData = e.response!.data as Map<String, dynamic>;
      return ApiException(
        message: errorData['message'] ?? 'Unknown error',
        statusCode: e.response?.statusCode ?? 0,
        details: errorData['details'],
      );
    }
    return NetworkException(e.message ?? 'Network error');
  }
}
```

### 3. Chat Service

```dart
// chat_service.dart
class ChatService {
  final ApiClient _apiClient;
  
  ChatService(this._apiClient);
  
  Future<ChatResponse> sendMessage({
    required String query,
    String? sessionId,
    SearchFilters? filters,
    bool includeSources = true,
  }) async {
    try {
      Response response = await _apiClient.dio.post('/chat', data: {
        'query': query,
        'session_id': sessionId,
        'filters': filters?.toJson(),
        'include_sources': includeSources,
      });
      
      return ChatResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  Stream<ChatStreamChunk> sendMessageStream({
    required String query,
    String? sessionId,
    SearchFilters? filters,
    bool includeSources = true,
  }) async* {
    try {
      Response<ResponseBody> response = await _apiClient.dio.post<ResponseBody>(
        '/chat/stream',
        data: {
          'query': query,
          'session_id': sessionId,
          'filters': filters?.toJson(),
          'include_sources': includeSources,
        },
        options: Options(
          headers: {'Accept': 'text/event-stream'},
          responseType: ResponseType.stream,
        ),
      );
      
      await for (String line in response.data!.stream
          .transform(utf8.decoder)
          .transform(LineSplitter())) {
        if (line.startsWith('data: ')) {
          String jsonData = line.substring(6);
          if (jsonData.trim().isNotEmpty && jsonData != '[DONE]') {
            Map<String, dynamic> data = json.decode(jsonData);
            yield ChatStreamChunk.fromJson(data);
          }
        }
      }
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  Future<List<ChatMessage>> getChatHistory(String sessionId) async {
    try {
      Response response = await _apiClient.dio.get('/chat/history/$sessionId');
      return (response.data as List)
          .map((json) => ChatMessage.fromJson(json))
          .toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  Future<void> clearChatHistory(String sessionId) async {
    try {
      await _apiClient.dio.delete('/chat/history/$sessionId');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
}
```

### 4. Model Classes

```dart
// models/invoice_analysis_response.dart
class InvoiceAnalysisResponse {
  final bool success;
  final String message;
  final String employeeName;
  final int totalInvoices;
  final int processedInvoices;
  final int failedInvoices;
  final List<InvoiceAnalysisResult>? results;
  final List<ProcessingError>? processingErrors;
  final DateTime timestamp;
  
  InvoiceAnalysisResponse({
    required this.success,
    required this.message,
    required this.employeeName,
    required this.totalInvoices,
    required this.processedInvoices,
    required this.failedInvoices,
    this.results,
    this.processingErrors,
    required this.timestamp,
  });
  
  factory InvoiceAnalysisResponse.fromJson(Map<String, dynamic> json) {
    return InvoiceAnalysisResponse(
      success: json['success'],
      message: json['message'],
      employeeName: json['employee_name'],
      totalInvoices: json['total_invoices'],
      processedInvoices: json['processed_invoices'],
      failedInvoices: json['failed_invoices'],
      results: json['results']?.map<InvoiceAnalysisResult>(
        (result) => InvoiceAnalysisResult.fromJson(result),
      ).toList(),
      processingErrors: json['processing_errors']?.map<ProcessingError>(
        (error) => ProcessingError.fromJson(error),
      ).toList(),
      timestamp: DateTime.parse(json['timestamp']),
    );
  }
}

// models/chat_response.dart
class ChatResponse {
  final String response;
  final String sessionId;
  final List<DocumentSource>? sources;
  final int retrievedDocuments;
  final String queryType;
  final double? confidenceScore;
  final List<String>? suggestions;
  final DateTime timestamp;
  
  ChatResponse({
    required this.response,
    required this.sessionId,
    this.sources,
    required this.retrievedDocuments,
    required this.queryType,
    this.confidenceScore,
    this.suggestions,
    required this.timestamp,
  });
  
  factory ChatResponse.fromJson(Map<String, dynamic> json) {
    return ChatResponse(
      response: json['response'],
      sessionId: json['session_id'],
      sources: json['sources']?.map<DocumentSource>(
        (source) => DocumentSource.fromJson(source),
      ).toList(),
      retrievedDocuments: json['retrieved_documents'],
      queryType: json['query_type'],
      confidenceScore: json['confidence_score']?.toDouble(),
      suggestions: json['suggestions']?.cast<String>(),
      timestamp: DateTime.parse(json['timestamp']),
    );
  }
}
```

### 5. Error Handling

```dart
// exceptions/api_exceptions.dart
class ApiException implements Exception {
  final String message;
  final int statusCode;
  final List<dynamic>? details;
  
  ApiException({
    required this.message,
    required this.statusCode,
    this.details,
  });
  
  @override
  String toString() => 'ApiException: $message (Status: $statusCode)';
}

class NetworkException implements Exception {
  final String message;
  
  NetworkException(this.message);
  
  @override
  String toString() => 'NetworkException: $message';
}

class RateLimitException implements Exception {
  @override
  String toString() => 'Rate limit exceeded. Please try again later.';
}

class FileTooLargeException implements Exception {
  @override
  String toString() => 'File size exceeds the maximum allowed limit.';
}
```

### 6. Usage in Widgets

```dart
// Example usage in a Flutter widget
class InvoiceAnalysisScreen extends StatefulWidget {
  @override
  _InvoiceAnalysisScreenState createState() => _InvoiceAnalysisScreenState();
}

class _InvoiceAnalysisScreenState extends State<InvoiceAnalysisScreen> {
  final InvoiceService _invoiceService = GetIt.instance<InvoiceService>();
  bool _isAnalyzing = false;
  List<InvoiceAnalysisStreamChunk> _progressUpdates = [];
  
  Future<void> _analyzeInvoices() async {
    setState(() {
      _isAnalyzing = true;
      _progressUpdates.clear();
    });
    
    try {
      await for (InvoiceAnalysisStreamChunk chunk in _invoiceService.analyzeInvoicesStream(
        employeeName: _employeeNameController.text,
        policyFile: _selectedPolicyFile!,
        invoicesZip: _selectedInvoicesZip!,
      )) {
        setState(() {
          _progressUpdates.add(chunk);
        });
        
        if (chunk.type == 'done') {
          break;
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    } finally {
      setState(() {
        _isAnalyzing = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Invoice Analysis')),
      body: Column(
        children: [
          // File selection widgets
          // ...
          
          ElevatedButton(
            onPressed: _isAnalyzing ? null : _analyzeInvoices,
            child: _isAnalyzing 
              ? CircularProgressIndicator()
              : Text('Analyze Invoices'),
          ),
          
          // Progress updates
          Expanded(
            child: ListView.builder(
              itemCount: _progressUpdates.length,
              itemBuilder: (context, index) {
                final update = _progressUpdates[index];
                return ListTile(
                  title: Text(update.type),
                  subtitle: Text(update.data?.toString() ?? ''),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
```

## ⚠️ Important Notes

1. **File Size Limits**: Default maximum file size is 50MB. Adjust as needed.

2. **Rate Limiting**: Default limit is 100 requests per minute per IP.

3. **Streaming Connections**: Keep alive for real-time updates, handle disconnections gracefully.

4. **Error Handling**: Always implement proper error handling for network issues and API errors.

5. **Session Management**: Use consistent session IDs for chat continuity.

6. **Security**: Always validate file types and sizes on the client side before uploading.

## 🔧 Testing

Use tools like Postman or curl to test endpoints:

```bash
# Health check
curl https://your-api-domain.com/api/v1/health/quick

# File upload test
curl -X POST https://your-api-domain.com/api/v1/analyze-invoices \
  -F "employee_name=John Doe" \
  -F "policy_file=@policy.pdf" \
  -F "invoices_zip=@invoices.zip"

# Chat test
curl -X POST https://your-api-domain.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all invoices", "session_id": "test123"}'
```

This API documentation provides everything needed to integrate the Invoice Reimbursement System with your Flutter application! 🚀
