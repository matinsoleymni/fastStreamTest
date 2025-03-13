#!/bin/bash

# رنگ‌ها برای خروجی بهتر
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# متغیرهای پیکربندی
read -p "Enter your domain name (e.g., example.com): " DOMAIN_NAME
read -p "Enter your email (for SSL certificate): " EMAIL

# تابع نمایش پیام
print_message() {
    echo -e "${BLUE}$1${NC}"
}

# تنظیم فایروال
setup_firewall() {
    print_message "Configuring firewall..."
    
    # نصب UFW اگر نصب نباشد
    sudo apt install -y ufw
    
    # تنظیم قوانین پایه
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # اجازه دسترسی به پورت‌های ضروری
    sudo ufw allow ssh
    sudo ufw allow http
    sudo ufw allow https
    sudo ufw allow 8501  # برای Streamlit
    sudo ufw allow 8000  # برای FastAPI
    
    # فعال‌سازی فایروال
    sudo ufw --force enable
}

# نصب بسته‌های مورد نیاز سیستم
install_system_packages() {
    print_message "Installing system packages..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx \
    build-essential libssl-dev libffi-dev python3-dev supervisor git ufw
}

# نصب و پیکربندی Nginx
setup_nginx() {
    print_message "Setting up Nginx configuration..."
    
    # ایجاد فایل پیکربندی Nginx با پشتیبانی از WSS
    sudo tee /etc/nginx/sites-available/$DOMAIN_NAME << EOF
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    '' close;
}

server {
    server_name $DOMAIN_NAME;
    client_max_body_size 100M;

    # تنظیمات SSL
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    keepalive_timeout 70;
    
    # تنظیمات WebSocket
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_buffering off;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_buffering off;
    }

    # تنظیمات WebSocket برای Streamlit
    location /_stcore/stream {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_buffering off;
    }
}
EOF

    # فعال‌سازی سایت
    sudo ln -sf /etc/nginx/sites-available/$DOMAIN_NAME /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # بررسی پیکربندی Nginx
    sudo nginx -t
    
    # راه‌اندازی مجدد Nginx
    sudo systemctl restart nginx
}

# نصب گواهی SSL
setup_ssl() {
    print_message "Setting up SSL certificate..."
    sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos -m $EMAIL --redirect
}

# پیکربندی Supervisor با تنظیمات محیطی
setup_supervisor() {
    print_message "Setting up Supervisor..."
    
    # پیکربندی FastAPI
    sudo tee /etc/supervisor/conf.d/fastapi.conf << EOF
[program:fastapi]
directory=$(pwd)
command=$(pwd)/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
autostart=true
autorestart=true
stderr_logfile=/var/log/fastapi.err.log
stdout_logfile=/var/log/fastapi.out.log
environment=PYTHONPATH="$(pwd)",PATH="$(pwd)/venv/bin"
EOF

    # پیکربندی Streamlit با تنظیمات اضافی
    sudo tee /etc/supervisor/conf.d/streamlit.conf << EOF
[program:streamlit]
directory=$(pwd)
command=$(pwd)/venv/bin/streamlit run ui.py --server.address 0.0.0.0 --server.port 8501 --server.maxUploadSize 100
autostart=true
autorestart=true
stderr_logfile=/var/log/streamlit.err.log
stdout_logfile=/var/log/streamlit.out.log
environment=PYTHONPATH="$(pwd)",PATH="$(pwd)/venv/bin"
EOF

    # ایجاد فایل پیکربندی Streamlit
    mkdir -p ~/.streamlit
    tee ~/.streamlit/config.toml << EOF
[server]
enableCORS = false
enableXsrfProtection = false

[browser]
serverAddress = "$DOMAIN_NAME"
serverPort = 8501

[theme]
primaryColor = "#F63366"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
EOF

    # بازخوانی و به‌روزرسانی Supervisor
    sudo supervisorctl reread
    sudo supervisorctl update
}

# نصب وابستگی‌های Python
setup_python_env() {
    print_message "Setting up Python environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn uvicorn[standard] # برای اجرای FastAPI در محیط تولید
}

# تابع اصلی
main() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}This script must be run as root or with sudo privileges${NC}"
        exit 1
    fi

    print_message "Starting deployment process..."
    
    install_system_packages
    setup_firewall
    setup_python_env
    setup_nginx
    setup_ssl
    setup_supervisor
    
    print_message "Deployment completed successfully!"
    echo -e "${GREEN}Your application is now running at https://$DOMAIN_NAME${NC}"
    echo -e "${BLUE}Logs can be found in /var/log/supervisor/${NC}"
    echo -e "${BLUE}Firewall status:${NC}"
    sudo ufw status

    # مشاهده وضعیت سرویس‌ها
    sudo supervisorctl status

    # راه‌اندازی مجدد یک سرویس
    sudo supervisorctl restart fastapi
    sudo supervisorctl restart streamlit

    # راه‌اندازی مجدد همه سرویس‌ها
    sudo supervisorctl restart all

    # مشاهده لاگ‌ها
    tail -f /var/log/fastapi.err.log
    tail -f /var/log/streamlit.err.log
}

# اجرای اسکریپت
main 