# ChatApp - Full-Stack iOS Chat Application

A real-time chat app with a Django backend (REST + WebSockets) and an iOS frontend (SwiftUI). 
Currently in development.

## 📌 Project Overview
A **local development** chat app featuring:
- **1:1 real-time messaging** (no group chats)
- **User auth** via OAuth 2.0 + JWT
- Self-contained **Dockerized** infrastructure

## 🛠️ Technology Stack
- **Frontend**: SwiftUI
- **Backend**: Django, Gunicorn (HTTP), Daphne (WebSocket)
- **Database**: PostgreSQL
- **Authentication**: OAuth 2.0, JWT
- **Real-time**: WebSocket (Redis channel layer)
- **Infrastructure**: Docker, Nginx

## ⚙️ Project Architecture

### Three-tier architecture
<img width="800" alt="Screen Shot 2024-09-22 at 9 36 59 PM" src="https://github.com/user-attachments/assets/2616876f-0e30-4fed-ad31-db442c039473">

### Database schema
<img width="700" alt="Screenshot 2025-04-13 at 17 56 31" src="https://github.com/user-attachments/assets/9906eff0-a6c0-49bf-9bc3-8553f19119da" />

## UI Design
[View Full Figma Prototype](https://www.figma.com/design/Qip3qsv3B7VWAZOhubplKW/IOS-Chat-App?node-id=3-96&t=BEV0arpvZRia6rIb-1)

## 🛠️ Setup & Usage

### Prerequisites
- Docker & Docker Compose
- Xcode (for iOS development)
- OAuth credentials from Google & 42 Intranet

### 1. Configure environment
Create `.env` in the `devops` directory:

```env
# Credentials for PostgreSQL
POSTGRES_HOST='your postgres host'
POSTGRES_PORT='your postgres port'
POSTGRES_DB='your postgres db'
POSTGRES_USER='your postgres user'
POSTGRES_PASSWORD='your postgres password'

# Credentials for Google OAuth
GOOGLE_CLIENT_ID='your google client id'
GOOGLE_CLIENT_SECRET='your google client secret'
GOOGLE_REDIRECT_URI='your google redirect uri'
GOOGLE_AUTH_URI='your google auth uri'
GOOGLE_TOKEN_URI='your google token uri'

# Credentials for 42 OAuth Intra
CLIENT_42_ID='your 42 client id'
CLIENT_42_SECRET='your 42 client secret'
REDIRECT_42_URI='your 42 redirect uri'
AUTH_42_URI='your 42 auth uri'
TOKEN_42_URI='your 42 token uri'
```
### 2. Start containers

```sh
# Build and run in detached mode
docker-compose -f devops/docker-compose.yml up --build -d

# View logs (optional)
docker-compose logs -f
```

### 3. Access services
- **Backend API**: `http://localhost:8081/api/`
- **Websocket**: `http://localhost:8081/ws/`

### 4. IOS App
**In Progress...**
