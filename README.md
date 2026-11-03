# 🛒 Full Stack E-Commerce Application

A full-stack E-Commerce web application built using **React, FastAPI, and PostgreSQL**. The application provides product browsing, user authentication, shopping cart management, and backend APIs for managing products and orders.

## 🚀 Technologies Used

### Frontend
- React.js
- JavaScript
- HTML5
- CSS3
- Vite

### Backend
- Python
- FastAPI
- SQLAlchemy
- REST API
- JWT Authentication
- Password Hashing

### Database
- PostgreSQL

### Testing
- Pytest
- API Testing

## ✨ Features

### Customer Features
- User registration and login
- Secure password hashing
- Browse available products
- View individual product details
- Search products
- Filter products by category and price
- Sort products by price
- Product pagination
- Add products to shopping cart
- Update cart quantities
- Remove products from cart
- View stock availability

### Backend Features
- RESTful API development using FastAPI
- PostgreSQL database integration
- SQLAlchemy ORM
- JWT-based authentication
- Product management APIs
- Cart management APIs
- Order management APIs
- Input validation and error handling
- Automated API tests using Pytest

## 📁 Project Structure

```text
online-store/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── security.py
│   ├── create_tables.py
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_cart.py
│       ├── test_orders.py
│       └── test_products.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   ├── Cart.jsx
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── ProductDetails.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/mutukurivijayasaidurgarao-design/ecommerce-online-store.git
cd ecommerce-online-store
```

### 2. Backend Setup

Open a terminal:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pwdlib[argon2] python-jose[cryptography] pytest httpx
```

Configure your PostgreSQL database credentials in your database configuration.

Create database tables:

```bash
python create_tables.py
```

Start the backend server:

```bash
python -m uvicorn main:app --reload
```

Backend URL:

`http://127.0.0.1:8000`

API Documentation:

`http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

`http://localhost:5173`

## 🧪 Running Tests

From the backend directory, run:

```bash
pytest -v
```

## 🔐 Security

- Password hashing using Argon2.
- JWT-based authentication.
- Protected API endpoints.
- Environment-based configuration for sensitive credentials.

## 🎯 Project Objective

The objective of this project is to develop a practical full-stack E-Commerce application while implementing frontend development, backend API development, database integration, authentication, and software testing concepts.

## 👨‍💻 Developer

**Vijaya Sai Durgarao Mutukuri**

- GitHub: [mutukurivijayasaidurgarao-design](https://github.com/mutukurivijayasaidurgarao-design)
- LinkedIn: [Vijaya Sai Durga Rao](https://www.linkedin.com/in/mutukuri-vijaya-sai-durga-rao-651864258/)

---

⭐ If you find this project interesting, consider giving it a star!
