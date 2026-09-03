# E-Commerce Platform

A Django-based e-commerce platform built with Django, PostgreSQL, Redis, Docker, and Docker Compose.

## Features

- User registration and login
- Email verification
- User profile management
- Address management
- Password reset
- Product listing
- Product categories
- Product variants
- Product search
- Product filtering
- Price filtering
- Size and color filtering
- Stock filtering
- Product sorting
- Product pagination
- Shopping cart
- Order management
- PostgreSQL database
- Redis integration
- Dockerized development environment
- Automated CI using GitHub Actions
- Pytest test suite
- Flake8 code quality checks

---

## Technology Stack

- Python 3.12
- Django
- PostgreSQL 16
- Redis 7
- Docker
- Docker Compose
- Pytest
- Flake8
- GitHub Actions

---

## Prerequisites

Before running the project on another system, install:

- Git
- Docker
- Docker Compose

Check the installation:

```bash
git --version
docker --version
docker compose version


Clone the Repository

Clone the project:

git clone <GITHUB_REPOSITORY_URL>

Go to the project directory:

cd ecommerce-platform



Environment Configuration

The project uses environment variables for configuration.

Create a .env file in the project root.

Example:

SECRET_KEY=your-secret-key
DEBUG=True

POSTGRES_DB=ecommerce
POSTGRES_USER=ecommerce
POSTGRES_PASSWORD=ecommerce
POSTGRES_HOST=db
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379/0

Do not commit the .env file to GitHub.

The .env file is already included in .gitignore.


Start the Project with Docker

Build the Docker containers:

docker compose build

Start the containers:

docker compose up -d

Or build and start in one command:

docker compose up -d --build

Check running containers:

docker compose ps


Database Migration

Run Django migrations:

docker compose exec web python manage.py migrate

Check Django configuration:

docker compose exec web python manage.py check


Create Superuser

Create an admin user:

docker compose exec web python manage.py createsuperuser

Follow the prompts to enter:

Username
Email
Password


Collect Static Files

Run:

docker compose exec web python manage.py collectstatic --noinput
Access the Application

Open:

http://localhost:8000/

Django Admin:

http://localhost:8000/admin/




Docker Services

The project uses Docker Compose to manage the required services.

Typical services:

web
db
redis
Django Application
docker compose logs -f web
PostgreSQL
docker compose logs -f db
Redis
docker compose logs -f redis
Redis Check

Verify that Redis is running:

docker compose exec redis redis-cli ping

Expected result:

PONG
Django Management Commands
Check project
docker compose exec web python manage.py check
Make migrations
docker compose exec web python manage.py makemigrations
Apply migrations
docker compose exec web python manage.py migrate
Create superuser
docker compose exec web python manage.py createsuperuser
Django shell
docker compose exec web python manage.py shell
Collect static files
docker compose exec web python manage.py collectstatic --noinput
Testing

The project uses Pytest.

Run all tests:

docker compose exec web pytest --tb=short -q

Run a specific test file:

docker compose exec web pytest path/to/test_file.py
Code Quality / Linting

The project uses Flake8.

Run:

docker compose exec web flake8 . --max-line-length=120 --exclude=migrations,__pycache__,.venv
GitHub Actions

The project includes a GitHub Actions CI workflow.

Workflow file:

.github/workflows/ci.yml

The CI workflow runs on:

Push to main
Push to dev
Pull requests targeting main
Pull requests targeting dev

The CI pipeline performs:

Checkout source code
        ↓
Setup Python 3.12
        ↓
Start PostgreSQL 16
        ↓
Start Redis 7
        ↓
Install dependencies
        ↓
Run Flake8
        ↓
Run Pytest
        ↓
PASS / FAIL
Development Workflow

Create a feature branch from dev:

git checkout dev
git pull origin dev
git checkout -b feature/<feature-name>

After making changes:

git status

Add changes:

git add .

Commit:

git commit -m "Description of changes"

Push the branch:

git push -u origin feature/<feature-name>

Then create a Pull Request from:

feature/<feature-name> → dev
Daily Development Commands

Start the project:

docker compose up -d

Check containers:

docker compose ps

Check Django:

docker compose exec web python manage.py check

Run tests:

docker compose exec web pytest --tb=short -q

Run linting:

docker compose exec web flake8 . --max-line-length=120 --exclude=migrations,__pycache__,.venv
Stop the Project

Stop containers:

docker compose down

Start again:

docker compose up -d
Rebuild the Project

After changing dependencies or Docker configuration:

docker compose down
docker compose up -d --build

For a completely fresh build:

docker compose down
docker compose build --no-cache
docker compose up -d
Troubleshooting
Check all containers
docker compose ps
Check all logs
docker compose logs -f
Check Django logs
docker compose logs -f web
Check PostgreSQL logs
docker compose logs -f db
Check Redis logs
docker compose logs -f redis
Django configuration error
docker compose exec web python manage.py check
Database migration issue
docker compose exec web python manage.py showmigrations
docker compose exec web python manage.py migrate
Redis connection issue
docker compose exec redis redis-cli ping

Expected:

PONG
Security

Never commit sensitive information to GitHub.

The following should not be committed:

.env
*.pem
*.key
*.log
db.sqlite3

Never commit:

Django SECRET_KEY
Database passwords
API keys
SMTP credentials
Production credentials
Cloud credentials

Use environment variables for sensitive configuration.

Project Structure

A typical project structure:

ecommerce-platform/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── accounts/
├── catalog/
├── orders/
│
├── templates/
├── static/
│
├── requirements/
│   └── dev.txt
│
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── .env
└── README.md
Quick Start

For a new developer/system:

git clone <GITHUB_REPOSITORY_URL>

cd ecommerce-platform

# Create/configure .env

docker compose up -d --build

docker compose exec web python manage.py migrate

docker compose exec web python manage.py createsuperuser

docker compose exec web python manage.py collectstatic --noinput

docker compose exec web python manage.py check

Then open:

http://localhost:8000/
License

Add the project's license information here.

Maintainer

E-Commerce Platform Development Team


### Then push only the README

Since your project is **already pushed**, you don't need to push the whole project again.

Create the file:

```bash
cd ~/.gemini/antigravity/scratch/ecommerce-platform
nano README.md

Paste the above content and save it.

Then:

git status
git add README.md
git commit -m "Add project README"
git push origin main

That's it. Your GitHub repository will now show the README.md on the repository homepage.

