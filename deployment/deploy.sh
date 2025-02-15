#!/bin/bash

EC2_IP="18.233.168.79"
KEY_PATH="/home/kenneth-kimani/Downloads/calvin-bot.pem"
APP_NAME="calvin_bot"
EC2_USER="ec2-user"

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
}

print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Function to retry commands
retry() {
    local n=1
    local max=5
    local delay=15
    while true; do
        "$@" && break || {
            if [[ $n -lt $max ]]; then
                ((n++))
                print_status "Command failed. Attempt $n/$max. Retrying in $delay seconds..."
                sleep $delay;
            else
                print_error "The command has failed after $n attempts."
                return 1
            fi
        }
    done
}

# Validate inputs
if [ -z "$EC2_IP" ] || [ -z "$KEY_PATH" ]; then
    print_error "Please set EC2_IP and KEY_PATH in the script"
    exit 1
fi

if [ ! -f "$KEY_PATH" ]; then
    print_error "Key file not found at $KEY_PATH"
    exit 1
fi

# Set correct permissions for key file
chmod 400 "$KEY_PATH"

print_status "Starting deployment to EC2 ($EC2_IP)..."

# Test SSH connection
print_status "Testing SSH connection..."
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $EC2_USER@"$EC2_IP" 'echo "SSH connection successful"'; then
    print_error "SSH connection failed"
    exit 1
fi
print_success "SSH connection established"

# Copy setup script and execute it
print_status "Setting up EC2 environment..."
if ! scp -i "$KEY_PATH" -o "CompressionLevel=9" setup-ec2.sh $EC2_USER@"$EC2_IP":/home/$EC2_USER/; then
    print_error "Failed to copy setup script"
    exit 1
fi

if ! ssh -i "$KEY_PATH" $EC2_USER@"$EC2_IP" 'bash setup-ec2.sh'; then
    print_error "EC2 setup script failed"
    exit 1
fi
print_success "EC2 environment setup completed"

# Create a temporary tar file
print_status "Creating application archive..."
cd ..
tar czf /tmp/app.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='*.png' \
    --exclude='comic_images' \
    --exclude='*.jpg' \
    --exclude='*.jpeg' \
    --exclude='*.gif' \
    --exclude='.pytest_cache' \
    --exclude='*.db' \
    .
cd - > /dev/null

# Copy and extract application files
print_status "Copying application files..."
if ! retry scp -C -i "$KEY_PATH" /tmp/app.tar.gz $EC2_USER@"$EC2_IP":/tmp/; then
    print_error "Failed to copy application archive"
    rm /tmp/app.tar.gz
    exit 1
fi

print_status "Extracting application files..."
ssh -i "$KEY_PATH" $EC2_USER@"$EC2_IP" "rm -rf /home/$EC2_USER/$APP_NAME/* && mkdir -p /home/$EC2_USER/$APP_NAME && tar xzf /tmp/app.tar.gz -C /home/$EC2_USER/$APP_NAME/ && rm /tmp/app.tar.gz"
rm /tmp/app.tar.gz
print_success "Application files copied and extracted"

# Copy environment file
print_status "Setting up environment..."
if [ -f ../.env ]; then
    if ! scp -i "$KEY_PATH" ../.env $EC2_USER@"$EC2_IP":/home/$EC2_USER/$APP_NAME/.env; then
        print_error "Failed to copy .env file"
        exit 1
    fi
else
    print_error ".env file not found in parent directory"
    exit 1
fi
print_success "Environment file copied"

# Start application
print_status "Starting application..."
if ! ssh -i "$KEY_PATH" $EC2_USER@"$EC2_IP" "cd /home/$EC2_USER/$APP_NAME && docker-compose up -d --build"; then
    print_error "Failed to start application"
    exit 1
fi

# Wait for application to start
print_status "Waiting for application to start..."
sleep 15

# Test application
print_status "Testing application..."
if curl -s --retry 5 --retry-delay 5 http://$EC2_IP:8000/status > /dev/null; then
    print_success "Application is running!"
    echo -e "\nYou can access your application at:"
    echo -e " - API: http://$EC2_IP:8000"
    echo -e " - Admin: http://$EC2_IP:8000/status"
else
    print_error "Application health check failed"
    echo "Check docker logs on the server using:"
    echo "ssh -i $KEY_PATH $EC2_USER@$EC2_IP 'docker logs calvin_bot'"
    exit 1
fi