#!/bin/bash

# رنگ‌ها برای خروجی بهتر
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# دریافت نام دامنه
read -p "Enter your domain name (e.g., example.com): " DOMAIN_NAME

# تابع نمایش پیام
print_message() {
    echo -e "${BLUE}$1${NC}"
}

# به‌روزرسانی تنظیمات Nginx
print_message "Updating Nginx configuration..."

# ایجاد فایل پیکربندی Nginx با پشتیبانی از WSS
sudo tee /etc/nginx/sites-available/$DOMAIN_NAME << EOF
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    '' close;
}

upstream streamlit {
    server localhost:8501;
    keepalive 32;
}

upstream fastapi {
    server localhost:8000;
    keepalive 32;
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
    proxy_buffers 8 32k;
    proxy_buffer_size 64k;

    # گزینه‌های اضافی برای WebSocket
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection \$connection_upgrade;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;

    location / {
        proxy_pass http://streamlit;
        proxy_next_upstream error timeout http_500 http_502 http_503 http_504;
        proxy_buffering off;
        proxy_set_header Connection \$connection_upgrade;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api {
        proxy_pass http://fastapi;
        proxy_next_upstream error timeout http_500 http_502 http_503 http_504;
        proxy_buffering off;
        proxy_set_header Connection \$connection_upgrade;
        proxy_cache_bypass \$http_upgrade;
    }

    location /_stcore/stream {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    location /_stcore/health {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_redirect off;
    }
}
EOF

# بررسی پیکربندی Nginx
print_message "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    print_message "Restarting services..."
    
    # راه‌اندازی مجدد Nginx
    sudo systemctl restart nginx
    
    # راه‌اندازی مجدد سرویس‌ها
    sudo supervisorctl restart all
    
    print_message "Configuration updated successfully!"
    echo -e "${GREEN}Your application should now be running at https://$DOMAIN_NAME${NC}"
    
    # نمایش وضعیت سرویس‌ها
    echo -e "${BLUE}Service status:${NC}"
    sudo supervisorctl status
else
    echo -e "${RED}Nginx configuration test failed. Please check the configuration.${NC}"
    exit 1
fi 