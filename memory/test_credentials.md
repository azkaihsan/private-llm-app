# Test Credentials

## Admin (seeded on backend startup from backend/.env ADMIN_EMAIL / ADMIN_PASSWORD)
- Email: admin@openwebui.local
- Password: Admin@123
- Role: admin

## Regular user
- Create via public signup (`POST /api/auth/signup` or the Sign Up form). Signup is open; the first user ever becomes admin, others get role `user`.

## Auth endpoints
- POST /api/auth/signup  {name, email, password} -> {token, user}
- POST /api/auth/login   {email, password} -> {token, user}
- GET  /api/auth/me      (Bearer token)
- Admin only: GET/POST /api/admin/users, PUT/DELETE /api/admin/users/{id}, GET/PUT /api/connections, POST /api/connections/test
- Token stored in localStorage key `openwebui_token`, sent as `Authorization: Bearer <token>`
