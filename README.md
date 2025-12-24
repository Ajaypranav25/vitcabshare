# 🚕 VIT Cab Share

A **backend-heavy Flask web application** that enables **VIT students** to share cab rides securely using **Google OAuth authentication**.  
The platform allows students to create rides, book available seats, and manage bookings — all restricted to verified `@vitstudent.ac.in` emails.

---

## 📌 Problem Statement

Students at VIT frequently travel to common locations (e.g., Katpadi Railway Station) and end up booking separate cabs.  
This application solves that by allowing students to **coordinate cab sharing**, reducing cost and improving convenience.

---

## 🚀 Features

### 🔐 Authentication
- Google OAuth 2.0 login
- Restricted to **VIT student emails only**
- Secure session management

### 👤 User Management
- Automatic profile creation on first login
- Mandatory phone number completion
- Profile editing support

### 🚗 Ride Management
- Create rides with:
  - Departure time
  - Total seats
  - Cost per person
  - Meeting & drop points
- View your own created rides
- Real-time seat availability tracking

### 📖 Booking System
- Book **one seat per user per ride**
- Prevents:
  - Double bookings
  - Booking your own ride
- Cancel bookings with automatic seat restoration

### 🗂 Dashboards
- Available rides dashboard
- My Rides
- My Bookings
- Ride details with participant list

---

## 🛠 Tech Stack

**Backend**
- Python
- Flask
- Flask-SQLAlchemy
- Authlib (Google OAuth)

**Database**
- SQLAlchemy
- supabase

**Frontend**
- Jinja2 Templates
- HTML / CSS (Flask rendering)

**Other Tools**
- dotenv for environment variables
- Werkzeug session handling
- vercel

---

## 🧱 Database Schema

### User
- `id`
- `name`
- `email` (unique)
- `phone`
- `google_id`
- Relationships: rides, bookings

### Ride
- `id`
- `user_id` (creator)
- `departure_time`
- `total_seats`
- `available_seats`
- `cost_per_person`
- `meeting_point`
- `drop_point`
- `notes`

### Booking
- `id`
- `ride_id`
- `user_id`
- `seats_booked`
- `booked_at`

---

## 🧪 Authentication Rules

- Only Google accounts with `@vitstudent.ac.in` emails are allowed
- Other domains are rejected automatically

---

## 🔒 Security Measures

- OAuth-based authentication
- Session validation on all protected routes
- Email domain verification
- Automatic session clearing on logout

---

## 📈 Future Enhancements

- Ride auto-expiry cleanup
- Admin moderation panel
- In-app messaging


---

## 🧠 What This Project Demonstrates

- Flask backend architecture
- OAuth authentication flow
- Relational database modeling
- Backend validations & constraints
- Real-world problem solving

---

## 👤 Author

**Ajay Pranav**  
Computer Science Student  
VIT Vellore

