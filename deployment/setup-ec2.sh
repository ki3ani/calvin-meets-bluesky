#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Update system
print_status "Updating system packages..."
sudo yum update -y || print_error "Failed to update package list"

# Install required packages
print_status "Installing required packages..."
sudo yum install -y \
    python3-pip \
    nginx || print_error "Failed to install required packages"

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    sudo yum install -y docker || print_error "Failed to install Docker"
else
    print_status "Docker already installed"
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose || print_error "Failed to install Docker Compose"
else
    print_status "Docker Compose already installed"
fi

# Start and enable Docker service
print_status "Configuring Docker service..."
sudo systemctl start docker || print_error "Failed to start Docker service"
sudo systemctl enable docker || print_error "Failed to enable Docker service"

# Add ec2-user to docker group
sudo usermod -aG docker ec2-user

# Create app directories
print_status "Creating application directories..."
mkdir -p /home/ec2-user/calvin_bot/comic_images
mkdir -p /home/ec2-user/calvin_bot/data

# Setup Nginx reverse proxy
print_status "Configuring Nginx..."
sudo tee /etc/nginx/conf.d/calvin_bot.conf << EOF
server {
    listen 80;
    server_name \$host;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
EOF

# Start Nginx
sudo systemctl start nginx || print_error "Failed to start Nginx"
sudo systemctl enable nginx || print_error "Failed to enable Nginx"

print_success "EC2 setup completed successfully!"

# Print new group membership notice
echo -e "\n${YELLOW}NOTE: You need to log out and back in for the new docker group membership to take effect.${NC}"