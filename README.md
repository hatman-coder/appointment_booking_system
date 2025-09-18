# 🏥 Appointment Booking System

A comprehensive healthcare appointment management system built with Django REST Framework. This system enables patients to book appointments with doctors, manage profiles, and provides healthcare providers with tools to manage schedules and generate reports.

## 📋 Table of Contents

- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Database Setup](#-database-setup)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Background Tasks](#-background-tasks)
- [Project Structure](#-project-structure)
- [User Roles](#-user-roles)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🔐 Authentication & User Management
- JWT-based authentication
- Three user types: **Admin**, **Doctor**, **Patient**
- Comprehensive user registration with validation
- Profile management with image upload
- Location-based user registration (Division → District → Thana)

### 👨‍⚕️ Doctor Features
- Doctor profile with specialization and experience
- Flexible schedule management
- Appointment management and status updates
- Monthly performance reports

### 👤 Patient Features
- Easy appointment booking with doctors
- Appointment history and status tracking
- Profile management with medical history
- Email appointment reminders

### 📊 Admin Features
- System-wide appointment management
- User management and oversight
- Comprehensive reporting dashboard
- Doctor and patient analytics

### 🔄 Advanced Features
- **Smart Filtering**: Filter doctors by specialization, location, experience, and fees
- **Conflict Detection**: Automatic appointment slot validation
- **Email Notifications**: 24-hour appointment reminders
- **Automated Reports**: Monthly doctor performance reports
- **Search Functionality**: Advanced search across users and appointments
- **Pagination**: Efficient data loading with pagination

## 🛠 Technology Stack

- **Backend**: Django 4.2.7, Django REST Framework 3.14.0
- **Database**: PostgreSQL
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Task Queue**: Celery with Redis
- **Email**: SMTP (Gmail/Custom)
- **Image Processing**: Pillow
- **API Documentation**: Built-in API endpoints

## 📋 System Requirements

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Git

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/appointment-booking-system.git
cd appointment-booking-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server

# macOS
brew install postgresql redis

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
```

## ⚙️ Configuration

### 1. Environment Setup

Create `.env` file in the project root:

```bash
cp .env.example .env
```

Update the `.env` file with your configuration:

```env
DEBUG=True
SECRET_KEY=your-super-secret-key-here
DATABASE_NAME=appointment_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-db-password
DATABASE_HOST=localhost
DATABASE_PORT=5432
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

### 2. Database Configuration

```bash
# Create PostgreSQL database
sudo -u postgres createdb appointment_db
sudo -u postgres createuser appointment_user
sudo -u postgres psql -c "ALTER USER appointment_user WITH PASSWORD 'your-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE appointment_db TO appointment_user;"
```

## 🗄️ Database Setup

### 1. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Seed Location Data

```bash
# Seed Bangladesh locations (Divisions, Districts, Thanas)
python manage.py seed_locations

# Create sample users for testing
python manage.py seed_sample_users
```

### 3. Create Superuser

```bash
python manage.py createsuperuser
```

## 🏃‍♂️ Running the Application

### Development Mode

You need **4 terminal windows**:

#### Terminal 1: Django Server
```bash
python manage.py runserver
```

#### Terminal 2: Celery Worker
```bash
celery -A appointment_system worker --loglevel=info
```

#### Terminal 3: Celery Beat (Scheduler)
```bash
celery -A appointment_system beat --loglevel=info
```

#### Terminal 4: Redis Server
```bash
redis-server
```

### Production Mode

```bash
# Start all services in background
celery -A appointment_system worker --detach --loglevel=info
celery -A appointment_system beat --detach --loglevel=info
gunicorn appointment_system.wsgi:application --bind 0.0.0.0:8000
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/
```

### 🔐 Authentication & Account Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/account/auth/register/` | Register new user (patient/doctor) |
| POST | `/account/auth/login/` | User login |
| POST | `/account/auth/logout/` | User logout |
| POST | `/account/auth/token/refresh/` | Refresh JWT token |
| GET | `/account/profile/` | Get user profile |
| PUT/PATCH | `/account/profile/update/` | Update user profile |
| POST | `/account/profile/change-password/` | Change user password |
| GET | `/account/dashboard/` | Get user dashboard data |

### 👨‍⚕️ Doctor Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/account/doctors/` | List all available doctors |
| GET | `/account/doctors/{doctor_id}/` | Get specific doctor details |
| GET | `/account/admin/users/` | Admin: Get all users |

### 📅 Appointment Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/appointment/` | List user's appointments |
| POST | `/appointment/book/` | Book new appointment |
| GET | `/appointment/{appointment_id}/` | Get appointment details |
| DELETE | `/appointment/{appointment_id}/` | Delete appointment |
| DELETE | `/appointment/{appointment_id}/cancel/` | Cancel appointment |
| PUT | `/appointment/{appointment_id}/reschedule/` | Reschedule appointment |
| PUT | `/appointment/{appointment_id}/status/` | Update appointment status |
| GET | `/appointment/available-slots/{doctor_id}/` | Get doctor's available slots |
| GET | `/appointment/history/` | Get appointment history |
| GET | `/appointment/history/{patient_id}/` | Get patient's appointment history |
| GET | `/appointment/schedule/` | Get user's schedule |
| GET | `/appointment/schedule/{doctor_id}/` | Get doctor's schedule |
| GET | `/appointment/statistics/` | Get appointment statistics |
| GET | `/appointment/admin/all/` | Admin: Get all appointments |

### 🌍 Location Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/location/divisions/` | List all divisions |
| GET | `/location/divisions/{division_id}/districts/` | Get districts by division |
| GET | `/location/districts/{district_id}/thanas/` | Get thanas by district |
| GET | `/location/divisions/{division_id}/complete/` | Get complete division data |
| GET | `/location/hierarchy/` | Get location hierarchy |
| GET | `/location/tree/` | Get location tree structure |
| GET | `/location/search/` | Search locations |
| GET | `/location/breadcrumb/` | Get location breadcrumb |
| GET | `/location/statistics/` | Get location statistics |
| POST | `/location/validate/` | Validate location data |
| POST | `/location/admin/clear-cache/` | Admin: Clear location cache |

### 📊 Reports & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/report/monthly/` | Get monthly reports |
| POST | `/report/generate/` | Generate monthly report |

## 🔄 Background Tasks

### Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| **Appointment Reminders** | Every Hour | Sends email reminders 24 hours before appointments |
| **Monthly Reports** | Daily | Generates monthly performance reports for doctors |

### Manual Task Execution

```python
# Django shell
python manage.py shell

from apps.reports.tasks import send_appointment_reminders, generate_monthly_reports

# Execute immediately
send_appointment_reminders.delay()
generate_monthly_reports.delay()
```

## 📁 Project Structure

```
appointment_system/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
├── apps/
│   ├── accounts/          # User management
│   ├── appointments/      # Appointment system
│   ├── locations/         # Bangladesh locations
│   └── reports/          # Reporting system
├── utils/
│   ├── permissions.py     # Custom permissions
│   └── validators.py      # Validation utilities
├── static/               # Static files
├── media/               # User uploads
└── templates/           # HTML templates
```

## 👥 User Roles

### 🔧 Admin
- Manage all users and appointments
- View system-wide analytics
- Generate comprehensive reports
- Oversee doctor and patient activities

### 👨‍⚕️ Doctor
- Manage personal schedule and availability
- View and update appointments
- Access patient appointment history
- Generate personal performance reports

### 👤 Patient
- Search and book appointments with doctors
- View appointment history
- Manage personal profile
- Receive appointment reminders

## 🧪 Testing

### Test Data

The system comes with pre-seeded test data:

```bash
# Login Credentials
Admin: admin@hospital.com / admin123
Doctor: doctor1@hospital.com / doctor123
Patient: patient1@gmail.com / patient123
```

### API Testing

```bash
# Test API endpoints
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@hospital.com", "password": "admin123"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **Celery not working**: Ensure Redis is running
2. **Database connection error**: Check PostgreSQL service and credentials
3. **Email not sending**: Verify SMTP settings and app passwords
4. **Permission denied**: Check file permissions for media uploads

### Logs

Check application logs for debugging:
```bash
tail -f appointment_system.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
