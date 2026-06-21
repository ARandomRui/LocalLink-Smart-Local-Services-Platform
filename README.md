# Local Link
[![GitHub repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/ARandomRui/LocalLink-Smart-Local-Services-Platform)
## 📌 Project Overview
**Local Link** is a local service provider platform designed to connect **service providers** with **customers** seamlessly.  
Built with **Flask, SQLAlchemy, and Flask-Login**, this project is ideal for **students, beginners, and learners** who want to understand how real-world service platforms are built.

This platform can be considered:
- ✅ A **mini-project** for academic purposes.
- ✅ A **major/advanced project** with proper features like booking, rating, and feedback systems.

---

## 🚀 Features
- **User Roles**: Customer, Service Provider, and Admin.
- **Service Listings**: Providers can create and manage services.
- **Booking System**: Customers can book services and track notifications.
- **Payment Integration**: Secure checkouts powered by Stripe API.
- **Rating & Feedback**: Customers can rate services after booking.
- **Complaint System**: Users can submit and track complaints.
- **Chat System**: Real-time communication between customers and providers using WebSockets.
- **Live Notifications**: Real-time push notifications for new messages and booking updates.
- **Location-Based Features**: Address autocomplete and service filtering powered by Google Maps API.
- **Admin Dashboard**: Manage users, services, and complaints.
- **Authentication & Security**: Secure login, password hashing, and Two-Factor Authentication (2FA) with TOTP and QR code scanning.

---

## 🛠️ Tech Stack
- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-SocketIO
- **Database**: SQLite
- **Frontend**: HTML, Bootstrap, Jinja2 Templates
- **Other**: Werkzeug, Stripe API, python-dotenv, PyOTP & qrcode (for 2FA)

---

## 📂 Project Structure
```text
LocalLink-Smart-Local-Services-Platform/
├── app.py                           # Main Flask application
├── local_services.db                # SQLite database
├── .env                             # Environment variables (API Keys)
├── .env.example                     # Template for environment variables
├── requirements.txt                 # Python dependencies
├── local_services_test_accounts.txt # Test account credentials
├── migrations/                      # Database migrations
├── templates/                       # HTML templates
│   ├── admin_dashboard.html
│   ├── base.html
│   ├── booking.html
│   ├── booking_form.html
│   ├── chat.html
│   ├── complaint.html
│   ├── create_service.html
│   ├── customer_dashboard.html
│   ├── customer_notifications.html
│   ├── index.html
│   ├── login.html
│   ├── profile.html
│   ├── provider_chats.html
│   ├── provider_dashboard.html
│   ├── provider_notifications.html
│   ├── rate_service.html
│   ├── register.html
│   ├── services.html
│   ├── setup_2fa.html
│   └── verify_2fa.html
├── static/                          # CSS and JS files
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── LICENSE                          # Open-source License
└── README.md                        # Documentation
```

---

## 📸 Screenshots

<img width="1348" height="630" alt="image" src="https://github.com/user-attachments/assets/ff9dca56-14a1-4d29-bcac-73db07454bf5" />

<img width="1348" height="626" alt="image" src="https://github.com/user-attachments/assets/d1987558-a5c1-4356-8ae5-25c670714a26" />

<img width="1345" height="623" alt="image" src="https://github.com/user-attachments/assets/544cf1d0-b208-497c-9002-7e6656daf765" />

<img width="1349" height="631" alt="image" src="https://github.com/user-attachments/assets/95f93a09-d5f8-48f0-81c7-8dbd23610077" />

<img width="1343" height="627" alt="image" src="https://github.com/user-attachments/assets/8808618d-941a-49f1-8225-1864619e6836" />

---

## 🔑 Prerequisites & API Keys

To run this project with full functionality, you must obtain two free API keys:
1. **Google Maps API Key**: Required for the location autocomplete feature when booking or creating a service. *(Make sure "Places API" and "Maps JavaScript API" are enabled in your Google Cloud Console).*
2. **Stripe Secret Key**: Required to simulate the payment process during checkout. *(You can get a free `sk_test_...` key by signing up for a Stripe developer account).*

### 🛠️ Setting up your `.env` file
Create a file named `.env` in the root directory (or rename `.env.example` to `.env`) and add your API keys in the exact format below:

```text
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
STRIPE_API_KEY=your_stripe_test_secret_key_here
```
*(Note: Do not use quotes around the values).*

---

## ⚙️ Installation & Setup

1. **Clone the repository**  
```bash
git clone https://github.com/ARandomRui/LocalLink-Smart-Local-Services-Platform.git
cd LocalLink-Smart-Local-Services-Platform
```

2. **Create a virtual environment**  
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. **Configure Environment Variables**  
Create a `.env` file in the root directory (or rename `.env.example` to `.env`) and add your API keys:
```text
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
STRIPE_API_KEY=your_stripe_test_secret_key
```

4. **Install dependencies**  
```bash
pip install -r requirements.txt
```

5. **Run the application**  
```bash
python app.py
```

6. **Access in Browser**  
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 👤 Default Admin Credentials
```
Email: admin@example.com
Password: admin123
```

---

## 🎯 Future Enhancements
- ✅ Payment Gateway Integration  
- ✅ Real-time Chat using WebSockets  
- ✅ Push Notifications  
- ✅ Advanced Search & Filtering  

---

## 📝 License
This project is open-source and available under the **MIT License**.

---

## 🙌 Contribution
Contributions, issues, and feature requests are welcome!  
Feel free to fork this repository and submit a pull request.

---

## ✨ Author
Developed by **Vaibhav Rawat**  
For learning and academic purposes.
