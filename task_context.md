# Task Context

## Task

Implement user authentication using OAuth2.

## Owned by

backend-team

## What I think I need to do

- Add login endpoint to handle OAuth2 flow
- Create session management service
- Implement password hashing for fallback auth
- Add logout endpoint to invalidate sessions

## What I'm unsure about

- Which OAuth provider to use (Google, GitHub, etc.)
- Session storage strategy (Redis vs database)
- How to handle token refresh

## Constraints I know

- Must use existing PostgreSQL database
- No breaking changes to current API
- Session timeout max 24 hours

## Things I'm assuming (might be wrong)

- Users already have email addresses in the system
- We can add columns to the users table
- Frontend can handle OAuth redirect flow
