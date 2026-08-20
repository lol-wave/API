# API Quick Reference Guide

## Base URL

```
http://localhost:8000
```

## Authentication

All endpoints require `Authorization: Bearer {access_token}` header (except login/register).

---

## GROUP MANAGEMENT ENDPOINTS

### Create Group (Teacher Only)

```http
POST /create-group
Content-Type: application/json

{
    "name": "Physics Class A",
    "description": "Advanced Physics 101"
}

Response: GroupResponse (201)
{
    "id": 1,
    "name": "Physics Class A",
    "description": "Advanced Physics 101",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
}
```

### Get All Groups

```http
GET /groups
Response: list[GroupResponse]
```

### Get Group Details with Members

```http
GET /group/{group_id}
Response: GroupDetailResponse (200)
{
    "id": 1,
    "name": "Physics Class A",
    "description": "Advanced Physics 101",
    "members": [
        {
            "id": 5,
            "full_name": "John Doe",
            "email": "john@example.com",
            "profile_pic": "/uploads/avatars/...",
            "is_group_admin": false,
            "created_at": "2024-01-10T08:00:00"
        }
    ],
    "objects": [
        {
            "id": 1,
            "name": "Assignment 1",
            "description": "...",
            "deadline": "2024-02-01T23:59:59",
            "group_id": 1,
            "submitted": false,
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:30:00"
        }
    ],
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
}
```

### Get Current User's Group

```http
GET /me/group
Response: GroupDetailResponse
```

### Add User to Group (Teacher Only)

```http
POST /group/{group_id}/members
Content-Type: application/json

{
    "user_id": 5
}

Response: UserMemberResponse (201)
{
    "id": 5,
    "full_name": "John Doe",
    "email": "john@example.com",
    "profile_pic": "/uploads/avatars/...",
    "is_group_admin": false,
    "created_at": "2024-01-10T08:00:00"
}

Error (409): User already in this group
Error (404): User not found
```

### Get Group Members

```http
GET /group/{group_id}/members
Response: list[UserMemberResponse]
```

### Remove User from Group (Teacher Only)

```http
DELETE /group/{group_id}/members/{user_id}
Response: 204 No Content
```

### Promote User to Group Admin (Teacher Only)

```http
POST /group/{group_id}/members/{user_id}/admin
Response: UserMemberResponse
{
    "id": 5,
    "full_name": "John Doe",
    "email": "john@example.com",
    "is_group_admin": true,
    ...
}
```

### Demote Group Admin (Teacher Only)

```http
DELETE /group/{group_id}/members/{user_id}/admin
Response: UserMemberResponse
{
    "id": 5,
    "is_group_admin": false,
    ...
}
```

### Update Group (Teacher Only)

```http
PATCH /group/{group_id}
Content-Type: application/json

{
    "name": "Physics Class B",
    "description": "Updated description"
}

Response: GroupResponse
```

### Delete Group (Teacher Only)

```http
DELETE /group/{group_id}
Response: 204 No Content
```

---

## NOTIFICATION ENDPOINTS

### Create Notification (Teacher Only)

```http
POST /notifications
Content-Type: application/json

{
    "title": "Assignment 1 Due",
    "description": "Physics homework assignment 1 is due tomorrow",
    "notification_type": "warning",
    "icon_url": "https://example.com/icons/warning.png",
    "user_ids": [1, 2, 3, 4]
}

Response: NotificationResponse (201)
{
    "id": 1,
    "title": "Assignment 1 Due",
    "description": "Physics homework assignment 1 is due tomorrow",
    "notification_type": "warning",
    "icon_url": "https://example.com/icons/warning.png",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
}
```

### Create Bulk Notification (Teacher Only)

```http
POST /notifications/bulk
Content-Type: application/json

{
    "title": "System Update",
    "description": "System maintenance scheduled",
    "notification_type": "info",
    "group_id": 1
}

Response: NotificationResponse
```

**Note**: If `group_id` is null, notification goes to ALL users.

### Get User's Notifications

```http
GET /notifications?skip=0&limit=50&is_read=false
Query Parameters:
  - skip: Number of records to skip (default: 0)
  - limit: Number of records to return (default: 50)
  - is_read: Filter by read status (null = all, true/false = specific)

Response: list[UserNotificationResponse]
[
    {
        "id": 1,
        "title": "Assignment 1 Due",
        "description": "Physics homework assignment 1 is due tomorrow",
        "notification_type": "warning",
        "icon_url": "https://example.com/icons/warning.png",
        "is_read": false,
        "read_at": null,
        "created_at": "2024-01-15T10:30:00"
    }
]
```

### Get Unread Notification Count

```http
GET /notifications/unread-count
Response: (200)
{
    "unread_count": 3
}
```

### Mark Notification as Read

```http
PATCH /notifications/{notification_id}
Content-Type: application/json

{
    "is_read": true
}

Response: UserNotificationResponse
{
    "id": 1,
    "title": "Assignment 1 Due",
    "is_read": true,
    "read_at": "2024-01-15T11:30:00",
    ...
}
```

### Delete Notification (from user's list)

```http
DELETE /notifications/{notification_id}
Response: 204 No Content
```

### Clear All Notifications

```http
DELETE /notifications?is_read=false
Query Parameters:
  - is_read: Filter by status (null = all, true/false = specific)

Response: 204 No Content
```

---

## OBJECT ENDPOINTS (Existing, Enhanced)

### Create Object (Teacher Only)

```http
POST /add-object
Content-Type: application/json

{
    "name": "Assignment 1",
    "description": "Physics homework",
    "deadline": "2024-02-01T23:59:59",
    "group_id": 1
}

Response: ObjectResponse (201)
```

### Get All Objects

```http
GET /objects
Response: list[ObjectResponse]
```

### Get Single Object

```http
GET /object/{item_id}
Response: ObjectResponse
```

### Submit Object

```http
POST /object/{item_id}/submit
Content-Type: application/json

{
  "url": "https://example.com/homework/assignment-1"
}

Response: HomeworkSubmissionResponse (201)
{
    "id": 1,
    "object_id": 1,
    "student_id": 7,
    "url": "https://example.com/homework/assignment-1",
    "grade": null,
    "feedback": null,
    ...
}
```

### My Submitted Homework

```http
GET /me/homework
Response: list[MyHomeworkResponse]
[
  {
    "id": 1,
    "object_id": 1,
    "student_id": 7,
    "url": "https://example.com/homework/assignment-1",
    "grade": 92,
    "feedback": "Clear explanation and good evidence.",
    "submitted_at": "2024-01-20T10:30:00",
    "graded_at": "2024-01-21T14:00:00",
    "homework": {
      "id": 1,
      "name": "Assignment 1",
      "description": "Physics homework",
      "deadline": "2024-02-01T23:59:59",
      "group_id": 1,
      "submitted": false,
      "homework_url": null,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  }
]
```

### Teacher Homework Inbox

```http
GET /teacher/homework
Response: list[HomeworkSubmissionResponse]
```

### Grade Homework

```http
PATCH /teacher/homework/{submission_id}/grade
Content-Type: application/json

{
    "grade": 92,
    "feedback": "Clear explanation and good evidence."
}

Response: HomeworkSubmissionResponse
```

---

## ERROR RESPONSES

### 400 Bad Request

```json
{
  "detail": "Invalid input data"
}
```

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Only teachers can perform this action."
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found."
}
```

### 409 Conflict

```json
{
  "detail": "User already in this group."
}
```

---

## NOTIFICATION TYPES

```
- "info": Informational messages (default)
- "warning": Warning messages (e.g., upcoming deadlines)
- "error": Error/failure messages
- "success": Success messages
```

---

## PAGINATION EXAMPLE

Get first 10 unread notifications:

```http
GET /notifications?skip=0&limit=10&is_read=false
```

Get next 10 unread notifications:

```http
GET /notifications?skip=10&limit=10&is_read=false
```

---

## CURL EXAMPLES

### Create Notification

```bash
curl -X POST http://localhost:8000/notifications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Notification",
    "description": "This is a test",
    "notification_type": "info",
    "user_ids": [1, 2, 3]
  }'
```

### Get User Notifications

```bash
curl http://localhost:8000/notifications \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Mark as Read

```bash
curl -X PATCH http://localhost:8000/notifications/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_read": true}'
```

### Add User to Group

```bash
curl -X POST http://localhost:8000/group/1/members \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 5}'
```

---

## COMMON WORKFLOWS

### Notify a Group About Due Date

```
1. POST /notifications/bulk with group_id
   - Sends to all members of the group
   - Type: "warning"
```

### Notify Specific Students

```
1. POST /notifications with user_ids array
   - Sends only to specified users
```

### Manage Group Admins

```
1. POST /group/{id}/members/{user_id}/admin - Promote
2. DELETE /group/{id}/members/{user_id}/admin - Demote
```

### Check Unread Notifications (for UI Badge)

```
1. GET /notifications/unread-count
   - Returns count only, quick operation
```

### Clear Old Notifications

```
1. DELETE /notifications?is_read=true
   - Removes all read notifications
```
