# Logs API Documentation

## Overview
The Logs API provides endpoints to retrieve application logs from the MongoDB database with comprehensive pagination support, filtering capabilities, and multiple response formats.

## Endpoints

### 1. GET `/api/logs` - Advanced Logs with Pagination

Retrieves logs with full pagination support and metadata.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Number of logs per page (1-1000) |
| `skip` | integer | 0 | Number of logs to skip (for offset-based pagination) |
| `page` | integer | 1 | Page number (alternative to skip, automatically calculates skip) |
| `level` | string | null | Filter by log level (INFO, ERROR, WARNING, DEBUG) |
| `before` | string | null | ISO timestamp to get logs before this date |

#### Response Format

```json
{
  "logs": [
    {
      "id": "string",
      "timestamp": "2025-06-27T19:05:43.577000",
      "level": "INFO",
      "message": "Request processed successfully",
      "url": "http://localhost:5000/api/users/login",
      "extra_data": {
        "request_ip": "127.0.0.1",
        "response_status": 200
      }
    }
  ],
  "pagination": {
    "total": 267,
    "limit": 10,
    "skip": 20,
    "page": 3,
    "total_pages": 27,
    "has_more": true
  }
}
```

#### Examples

```bash
# Get first 10 logs
GET /api/logs?limit=10&page=1

# Get logs from page 3 with 5 logs per page
GET /api/logs?limit=5&page=3

# Filter by ERROR level only
GET /api/logs?level=ERROR&limit=20

# Get logs before a specific timestamp
GET /api/logs?before=2025-06-27T19:00:00Z&limit=50

# Use skip for offset-based pagination
GET /api/logs?limit=10&skip=20
```

### 2. GET `/api/logs/simple` - Simple Logs (Backward Compatibility)

Retrieves logs in a simple array format without pagination metadata.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum number of logs to return |
| `level` | string | null | Filter by log level |
| `before` | string | null | ISO timestamp to get logs before this date |

#### Response Format

```json
[
  {
    "id": "string",
    "timestamp": "2025-06-27T19:05:43.577000",
    "level": "INFO",
    "message": "Request processed successfully",
    "url": "http://localhost:5000/api/users/login",
    "extra_data": {
      "request_ip": "127.0.0.1",
      "response_status": 200
    }
  }
]
```

## Log Levels

The system supports the following log levels:

- **INFO**: General information about application operations
- **ERROR**: Error conditions that need attention
- **WARNING**: Warning conditions that should be monitored
- **DEBUG**: Detailed debugging information

## Pagination Details

### Page vs Skip Parameters

- **Page Parameter**: Use `page=N` for user-friendly page navigation. The system automatically calculates the skip value as `(page - 1) * limit`.
- **Skip Parameter**: Use `skip=N` for direct offset control. If both are provided, `page` takes precedence.

### Pagination Metadata

The response includes comprehensive pagination information:

- `total`: Total number of logs matching the filter criteria
- `limit`: Number of logs per page
- `skip`: Number of logs skipped
- `page`: Current page number
- `total_pages`: Total number of pages available
- `has_more`: Boolean indicating if more logs are available

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid parameter: limit must be a positive integer"
}
```

### 503 Service Unavailable
```json
{
  "error": "Database connection not available"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to retrieve logs"
}
```

## Performance Notes

1. **Indexing**: Logs are sorted by timestamp in descending order (newest first)
2. **Limits**: Maximum limit is capped at 1000 logs per request for performance
3. **Filtering**: Level filtering is case-insensitive and converted to uppercase
4. **Date Filtering**: The `before` parameter accepts ISO 8601 formatted timestamps

## Usage Examples

### Python with requests

```python
import requests

# Get paginated logs
response = requests.get('http://localhost:5000/api/logs', params={
    'limit': 20,
    'page': 1,
    'level': 'ERROR'
})

data = response.json()
logs = data['logs']
pagination = data['pagination']

print(f"Found {pagination['total']} total logs")
print(f"Showing page {pagination['page']} of {pagination['total_pages']}")
```

### JavaScript with fetch

```javascript
async function getLogs(page = 1, limit = 20, level = null) {
    const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString()
    });
    
    if (level) {
        params.append('level', level);
    }
    
    const response = await fetch(`/api/logs?${params}`);
    const data = await response.json();
    
    return data;
}

// Usage
const result = await getLogs(1, 10, 'ERROR');
console.log(`Total logs: ${result.pagination.total}`);
```

## Implementation Details

The logs endpoint is implemented in the `LogService` class with the following key features:

1. **Efficient Pagination**: Uses MongoDB's `skip()` and `limit()` methods
2. **Count Optimization**: Separate count query for accurate pagination metadata
3. **Flexible Filtering**: Supports multiple filter criteria simultaneously
4. **Data Transformation**: Consistent DTO format with proper ID conversion
5. **Error Handling**: Comprehensive error handling with fallback responses

## Database Schema

Logs are stored in MongoDB with the following structure:

```javascript
{
  _id: ObjectId,
  timestamp: ISODate,
  level: String,
  message: String,
  url: String,
  extra_data: Object,
  created_at: ISODate,
  updated_at: ISODate
}
``` 