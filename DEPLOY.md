# Deployment Instructions

This project consists of a Python Flask API backend and a React/Next.js frontend. They are containerized using Docker Compose for seamless deployment.

## Prerequisites
- Docker and Docker Compose installed on your deployment server (e.g., Ubuntu/Linode).

## Environment Variables
Before deploying, ensure you configure the environment correctly. The application relies on a `.env` file at the project root.

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Update the `.env` file with real secrets for Production:
   - `SECRET_KEY`: Set this to a long random string.
   - `RAZORPAY_KEY_ID` & `RAZORPAY_KEY_SECRET`: If processing payments.

## Deployment with Docker Compose

To start the full stack (Next.js frontend + Flask backend data/API):

```bash
docker-compose up -d --build
```

### Accessing the application
- The **Frontend** will be running on `http://localhost:3000`.
- The **Backend API** will be running on `http://localhost:5000`.

### Rebuilding Containers
Whenever you push new code or change `.env` variables, rebuild using:
```bash
docker-compose up -d --build --force-recreate
```

## Reverse Proxy Configuration (Nginx)
For a production environment, you should use Nginx to reverse proxy the domain to the Frontend container (`port 3000`), and proxy `/api/` traffic to the Backend container (`port 5000`).

Example Nginx server block:

```nginx
server {
    server_name myapp.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Persistent Storage
The backend utilizes SQLite by default. The volumes mapped in `docker-compose.yml` ensure that `data/users.db` and uploaded files (`/uploads`) persist even if the containers are destroyed.

```yaml
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
```
