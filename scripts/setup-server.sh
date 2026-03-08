#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# FinAuto — First-time Linode Server Setup
#
# Run this ONCE on a fresh Linode instance to prepare it for CI/CD deploys.
#
# Usage:
#   chmod +x scripts/setup-server.sh
#   ssh root@YOUR_LINODE_IP "bash -s" < scripts/setup-server.sh
#
# Or copy to server and run:
#   scp scripts/setup-server.sh root@YOUR_LINODE_IP:~
#   ssh root@YOUR_LINODE_IP "bash ~/setup-server.sh"
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Finempire/Finauto.git}"
DEPLOY_PATH="/opt/finauto"
DEPLOY_USER="${DEPLOY_USER:-root}"   # change to a dedicated user if desired
BRANCH="${BRANCH:-main}"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  FinAuto — Server Setup              ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. System update ──────────────────────────────────────────────────────────
echo "==> Updating system packages..."
apt-get update -qq && apt-get upgrade -y -qq

# ── 2. Install Docker ─────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    echo "==> Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "    Docker installed: $(docker --version)"
else
    echo "==> Docker already installed: $(docker --version)"
fi

# Docker Compose v2 (plugin)
if ! docker compose version &>/dev/null; then
    echo "==> Installing Docker Compose plugin..."
    apt-get install -y -qq docker-compose-plugin
fi
echo "    Docker Compose: $(docker compose version)"

# ── 3. Install Git ────────────────────────────────────────────────────────────
if ! command -v git &>/dev/null; then
    echo "==> Installing git..."
    apt-get install -y -qq git
fi

# ── 4. Clone repository ───────────────────────────────────────────────────────
echo ""
echo "==> Setting up deploy directory: $DEPLOY_PATH"
if [ -d "$DEPLOY_PATH/.git" ]; then
    echo "    Repository already exists, pulling latest..."
    cd "$DEPLOY_PATH"
    git fetch origin
    git reset --hard "origin/$BRANCH"
else
    echo "    Cloning $REPO_URL → $DEPLOY_PATH"
    git clone --branch "$BRANCH" "$REPO_URL" "$DEPLOY_PATH"
    cd "$DEPLOY_PATH"
fi

# ── 5. Create .env file ───────────────────────────────────────────────────────
if [ ! -f "$DEPLOY_PATH/.env" ]; then
    echo ""
    echo "==> Creating .env file..."
    # Generate a secure 64-char secret key
    SECRET_KEY=$(openssl rand -hex 32)
    DB_PASS=$(openssl rand -hex 16)

    cat > "$DEPLOY_PATH/.env" << EOF
DB_PASS=$DB_PASS
SECRET_KEY=$SECRET_KEY
ADMIN_EMAIL=admin@finauto.com
ADMIN_PASSWORD=admin123456
EOF
    echo "    .env created with auto-generated secrets."
    echo ""
    echo "    ┌─────────────────────────────────────────┐"
    echo "    │  ⚠  IMPORTANT: Change ADMIN_PASSWORD!    │"
    echo "    │  Edit: $DEPLOY_PATH/.env                 │"
    echo "    └─────────────────────────────────────────┘"
else
    echo "==> .env already exists — skipping."
fi

# ── 6. Build frontend (first time only; CI will handle subsequent builds) ─────
if [ ! -d "$DEPLOY_PATH/frontend/dist" ]; then
    echo ""
    echo "==> Building frontend (first-time only)..."
    if command -v node &>/dev/null; then
        cd "$DEPLOY_PATH/frontend"
        npm ci --silent
        npm run build
        cd "$DEPLOY_PATH"
    else
        echo "    Node not installed — installing temporarily..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y -qq nodejs
        cd "$DEPLOY_PATH/frontend"
        npm ci --silent
        npm run build
        cd "$DEPLOY_PATH"
        # Optionally remove Node after build to keep server clean:
        # apt-get remove -y nodejs
    fi
    echo "    Frontend built ✓"
fi

# ── 7. Start containers ───────────────────────────────────────────────────────
echo ""
echo "==> Starting containers..."
cd "$DEPLOY_PATH"
docker compose up -d --build

echo ""
echo "==> Waiting 10s for containers to initialize..."
sleep 10
docker compose ps

# ── 8. Set up SSH key for GitHub Actions deploys ──────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════"
echo "  NEXT STEPS — Configure GitHub Actions secrets"
echo "══════════════════════════════════════════════════════"
echo ""
echo "  1. Generate a deploy SSH key (run on your LOCAL machine):"
echo ""
echo "     ssh-keygen -t ed25519 -C 'github-actions-finauto' -f ~/.ssh/finauto_deploy"
echo "     cat ~/.ssh/finauto_deploy.pub   # → paste into server authorized_keys"
echo "     cat ~/.ssh/finauto_deploy       # → paste as LINODE_SSH_KEY secret"
echo ""
echo "  2. Add public key to this server:"
echo "     echo 'PASTE_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
echo ""
echo "  3. Add these secrets to your GitHub repo:"
echo "     (Settings → Secrets and variables → Actions → New repository secret)"
echo ""
echo "     LINODE_HOST  = $(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_LINODE_IP')"
echo "     LINODE_USER  = $DEPLOY_USER"
echo "     LINODE_SSH_KEY = <contents of ~/.ssh/finauto_deploy>"
echo "     LINODE_PORT  = 22   (optional, only if non-standard)"
echo ""
echo "  4. Push a commit to main — GitHub Actions will deploy automatically!"
echo ""
echo "══════════════════════════════════════════════════════"
echo ""
echo "  App should be running at: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_LINODE_IP')"
echo ""
