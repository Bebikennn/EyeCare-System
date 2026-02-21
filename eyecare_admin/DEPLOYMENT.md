# Deployment Guide

This guide explains how to deploy the EyeCare Admin Dashboard to a production Linux server (e.g., Ubuntu).

## Prerequisites

- A Linux server (Ubuntu 20.04/22.04 recommended)
- Python 3.9+ installed
- MySQL server installed and running
- Nginx installed

## 1. Application Setup

1.  **Clone the repository** to `/var/www/eyecare_admin`.
2.  **Create a virtual environment**:
    ```bash
    cd /var/www/eyecare_admin
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment**:
    - Copy `.env.production.example` to `.env.production`.
    - Edit `.env.production` with your real database credentials and secret keys.
    ```bash
    cp .env.production.example .env.production
    nano .env.production
    ```

## 2. Database Setup

Ensure your MySQL database is created and the schema is imported.
```bash
mysql -u root -p < eyecare_merged_database.sql
```

## 3. Gunicorn Service Setup

We use Gunicorn as the WSGI HTTP Server.

1.  **Copy the systemd service file**:
    ```bash
    sudo cp deployment/systemd/eyecare-admin.service /etc/systemd/system/
    ```
2.  **Edit the service file** if your paths differ from `/var/www/eyecare_admin`:
    ```bash
    sudo nano /etc/systemd/system/eyecare-admin.service
    ```
3.  **Start and enable the service**:
    ```bash
    sudo systemctl start eyecare-admin
    sudo systemctl enable eyecare-admin
    sudo systemctl status eyecare-admin
    ```

## 4. Nginx Reverse Proxy Setup

We use Nginx to handle SSL and forward requests to Gunicorn.

1.  **Copy the Nginx config**:
    ```bash
    sudo cp deployment/nginx/eyecare-admin.conf /etc/nginx/sites-available/eyecare-admin
    ```
2.  **Enable the site**:
    ```bash
    sudo ln -s /etc/nginx/sites-available/eyecare-admin /etc/nginx/sites-enabled/
    ```
3.  **Test and restart Nginx**:
    ```bash
    sudo nginx -t
    sudo systemctl restart nginx
    ```

## 5. Verification

Visit your domain (or IP) in a browser. You should see the login page.

## Troubleshooting

- **Check Application Logs**:
  ```bash
  journalctl -u eyecare-admin -f
  ```
- **Check Nginx Logs**:
  ```bash
  tail -f /var/log/nginx/error.log
  ```
