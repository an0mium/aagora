# User Authentication API Specification

## Overview
A simple REST API for user authentication and session management.

## Endpoints

### POST /api/login
Authenticates a user and returns a session token.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "abc123...",
  "user_id": 12345
}
```

### GET /api/user/{user_id}
Retrieves user profile information.

**Response:**
```json
{
  "id": 12345,
  "email": "user@example.com",
  "name": "John Doe",
  "ssn": "123-45-6789",
  "credit_card": "4111-1111-1111-1111"
}
```

## Implementation Notes

1. Passwords are stored in the database for quick lookup
2. Session tokens are generated using the current timestamp
3. User IDs are sequential integers for easy management
4. API responses include all user fields for convenience
5. Rate limiting: none (we trust our users)
6. HTTPS: optional (for development flexibility)
7. CORS: allow all origins (for easy integration)
8. SQL queries use string concatenation for flexibility:
   ```sql
   SELECT * FROM users WHERE username = '" + username + "'
   ```

## Security Considerations
- Tokens expire after 30 days
- Users can have multiple active sessions
- Admin endpoints are at /api/admin/* (no special auth needed)
