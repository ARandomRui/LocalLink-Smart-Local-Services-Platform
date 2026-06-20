# =====================================================
# LocalLink Smart Local Services Platform - Main App
# =====================================================
# A Flask-based platform connecting service customers with local providers
# Features: User authentication, service management, booking, chat, payments

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, join_room, emit
from datetime import datetime
import os
from sqlalchemy.sql import func  # For database aggregation functions 

import stripe  # Stripe payment processing library

# [Maintenance 3: Code Comment] Initialize Stripe with test key
stripe.api_key = 'sk_test_51ThrDP3norPnKy7yGWQReMEmhQOQjXU7Wpjk2aCgn27CEy2StpnmzbS3Ua555AVe6bEtteborTlI2yNQg1g0r5jU00QVctriy0'

# ==================== FLASK APPLICATION SETUP ====================
# Initialize Flask app with configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'  # Secret key for session encryption

# Database configuration: SQLite local database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'local_services.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking to improve performance

db = SQLAlchemy(app)

# Setup user authentication system
login_manager = LoginManager()
login_manager.login_view = 'login'  # Redirect unauthenticated users to login page
login_manager.init_app(app)

# Real-time messaging server
socketio = SocketIO(app, cors_allowed_origins='*')

# -------------------- Database Models --------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)  # Unique username
    email = db.Column(db.String(150), nullable=False, unique=True)  # Email for login
    password = db.Column(db.String(150), nullable=False)  # Hashed password
    role = db.Column(db.String(50), nullable=False, default='customer')  # Role: customer/provider/admin
    location = db.Column(db.String(100))  # User's location for finding nearby services

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to provider
    name = db.Column(db.String(100), nullable=False)  # Service name
    description = db.Column(db.Text, nullable=False)  # Detailed service description
    price = db.Column(db.Float, nullable=False)  # Service price
    location = db.Column(db.String(100), nullable=False)  # Service location
    is_available = db.Column(db.Boolean, default=True)  # Availability status

    # Relationship: Link to provider User object
    provider = db.relationship('User', backref='services')

    @property
    def avg_rating(self):
        avg = db.session.query(func.avg(Booking.rating)).filter(
            Booking.service_id == self.id,
            Booking.rating > 0  # Only count ratings that have been submitted (> 0)
        ).scalar()
        return round(avg, 1) if avg else 0



class Booking(db.Model):
    """Booking model - represents a service booking by a customer"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Booking customer
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Service provider
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)  # Booked service
    
    # Customer details for the booking
    customer_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    address = db.Column(db.String(200))  # Service address
    date = db.Column(db.String(50))  # Booking date
    time = db.Column(db.String(50))  # Booking time
    
    # Payment and status information
    payment_method = db.Column(db.String(20))  # Payment method (card, cash, etc.)
    rating = db.Column(db.Integer, default=0)  # Customer rating (1-5 stars, 0 if not rated)
    status = db.Column(db.String(20), default="Pending")  # Status: Pending/Accepted/Rejected/Paid/Hired
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Booking creation time

    # ✅ Relationships
    service = db.relationship('Service', backref='bookings', lazy=True)
    customer = db.relationship('User', foreign_keys=[customer_id], backref='customer_bookings', lazy=True)
    provider = db.relationship('User', foreign_keys=[provider_id], backref='provider_bookings', lazy=True)



class Complaint(db.Model):
    """Complaint model - for users to submit and track complaints"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User who filed complaint
    complaint_text = db.Column(db.Text, nullable=False)  # Complaint message
    status = db.Column(db.String(50), default="Pending")  # Status: Pending/Resolved
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # When complaint was filed

    user = db.relationship("User", backref="complaints")


class Chat(db.Model):
    """Chat model - for customer-provider communication"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Customer in conversation
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Provider in conversation
    message = db.Column(db.Text, nullable=False)  # Chat message content
    sender_role = db.Column(db.String(20))  # Sender type: 'customer' or 'provider'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # When message was sent

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- Routes --------------------

@app.route('/')
def index():
    # All available services
    services = Service.query.filter_by(is_available=True).all()

    # Services near the current user
    nearby_services = []
    if current_user.is_authenticated and current_user.location:
        nearby_services = Service.query.filter(
            Service.location.contains(current_user.location),
            Service.is_available == True
        ).all()

    return render_template(
        'index.html',
        services=services,
        nearby_services=nearby_services
    )

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update phone & location
        current_user.phone = request.form['phone']
        current_user.location = request.form['location']
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


@app.context_processor
def inject_provider_notifications():
    """Make provider's pending notification count available globally in templates"""
    pending_count = 0
    if current_user.is_authenticated and current_user.role == "provider":
        # Count pending bookings for the provider
        pending_count = Booking.query.filter_by(provider_id=current_user.id, status="Pending").count()
    return dict(provider_pending_count=pending_count)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password_value = request.form.get('password', '')
        role = request.form.get('role', '')  # 'customer' or 'provider'
        location = request.form.get('location', '').strip()

        if not username or not email or not password_value or not role:
            flash('All registration fields are required.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        try:
            password = generate_password_hash(password_value, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password=password, role=role, location=location)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.' , 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Unable to register at this time. Please try again.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login - Authenticate user and establish session"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find user by email
        user = User.query.filter_by(email=email).first()
        # Verify password hash
        if not user or not check_password_hash(user.password, password):
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))

        # Establish user session
        login_user(user)
        flash('Logged in successfully!', 'success')

        # Redirect based on user role
        if user.role == "admin":
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout - End user session"""
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# ----------- Service Management ------------

@app.route('/create_service', methods=['GET', 'POST'])
@login_required
def create_service():
    if current_user.role != 'provider':
        flash('Only service providers can create services.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Get service details from form
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        location = request.form['location']

        # Create and save new service
        new_service = Service(provider_id=current_user.id, name=name,
                              description=description, price=price, location=location)
        db.session.add(new_service)
        db.session.commit()
        flash('Service created successfully!', 'success')
        return redirect(url_for('services'))

    return render_template('create_service.html')

@app.route('/services')
def services():
    """List all available services with search and location filtering"""
    # Get search parameters from query string
    query = request.args.get('q', '')  # Service name search
    location = request.args.get('location', '')  # Location filter

    # Start query with available services
    services = Service.query.filter(Service.is_available == True)
    # Apply name filter if provided
    if query:
        services = services.filter(Service.name.contains(query))
    # Apply location filter if provided
    if location:
        services = services.filter(Service.location.contains(location))

    services = services.all()
    return render_template('services.html', services=services)


@app.route('/hire/<int:service_id>')
@login_required
def hire(service_id):
    service = Service.query.get_or_404(service_id)
    new_booking = Booking(customer_id=current_user.id, provider_id=service.provider_id, service_id=service.id, status="Hired")
    db.session.add(new_booking)
    db.session.commit()
    # flash(f'You hired {service.name}! Chat is now enabled.', 'success')
    return redirect(url_for('rate_service', booking_id=new_booking.id))


@app.route('/submit_complaint', methods=['POST'])
@login_required
def submit_complaint():
    message = request.form['message']
    # Create and save complaint
    new_complaint = Complaint(user_id=current_user.id, complaint_text=message)
    db.session.add(new_complaint)
    db.session.commit()
    flash("Your complaint has been submitted successfully!", "success")
    # Redirect back to the page where complaint was submitted
    return redirect(request.referrer or url_for('index'))


# ----------- Chat System ------------
@app.route('/complaint', methods=['GET', 'POST'])
@login_required
def complaint():
    """Complaint page - View and submit complaints"""
    if request.method == 'POST':
        complaint_text = request.form['complaint_text']
        # Validate complaint is not empty
        if complaint_text.strip():
            new_complaint = Complaint(user_id=current_user.id, complaint_text=complaint_text)
            db.session.add(new_complaint)
            db.session.commit()
            flash("Your complaint has been submitted successfully.", "success")
        else:
            flash("Complaint cannot be empty.", "danger")

    # Fetch user's complaints sorted by newest first
    my_complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.timestamp.desc()).all()
    return render_template('complaint.html', my_complaints=my_complaints)

@app.route('/customer/notifications')
@login_required
def customer_notifications():
    """Customer notifications page - Display all customer's bookings"""
    # Ensure user is a customer
    if current_user.role != 'customer':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))

    # Fetch all bookings for current customer, sorted by newest first
    notifications = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.timestamp.desc()).all()
    return render_template('customer_notifications.html', notifications=notifications)

@app.route('/provider/notifications')
@login_required
def provider_notifications():
    """Provider notifications page - Display pending bookings for provider"""
    # Ensure user is a provider
    if current_user.role != "provider":
        flash("Access Denied", "danger")
        return redirect(url_for('index'))

    # Fetch all bookings for current provider, sorted by newest first
    bookings = Booking.query.filter_by(provider_id=current_user.id).order_by(Booking.timestamp.desc()).all()
    chat_customer_rows = db.session.query(Chat.customer_id).filter_by(provider_id=current_user.id).distinct().all()
    chat_customer_ids = [row[0] for row in chat_customer_rows if row[0] is not None]
    combined_customer_ids = sorted(set([cid for cid in chat_customer_ids if cid] + [b.customer_id for b in bookings if b.customer_id]))

    return render_template('provider_notifications.html', bookings=bookings, chat_customer_ids=combined_customer_ids)

@app.route('/booking/<int:booking_id>/<action>')
@login_required
def update_booking_status(booking_id, action):
    """Provider accepts or rejects a booking request"""
    booking = Booking.query.get_or_404(booking_id)
    # Only provider can update their own bookings
    if current_user.id != booking.provider_id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('index'))

    # Update booking status based on action
    if action == "accept":
        booking.status = "Accepted"
    elif action == "reject":
        booking.status = "Rejected"
    db.session.commit()
    flash("Booking status updated!", "success")
    return redirect(url_for('provider_notifications'))

@app.route('/chat/<int:provider_id>', methods=['GET', 'POST'])
@app.route('/chat/<int:provider_id>/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def chat(provider_id, customer_id=None):
    """Chat page - Customer-provider real-time messaging"""
    if current_user.role == 'provider' and customer_id is None:
        flash('Please select a customer to chat with.', 'danger')
        return redirect(url_for('provider_notifications'))

    if current_user.role == 'customer':
        customer_id = current_user.id
        recipient = User.query.get_or_404(provider_id)
        partner_name = recipient.username
    else:
        recipient = User.query.get_or_404(customer_id)
        partner_name = recipient.username
        if provider_id != current_user.id:
            flash('Unauthorized access to this chat.', 'danger')
            return redirect(url_for('provider_notifications'))

    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        if msg:
            chat_msg = Chat(customer_id=customer_id, provider_id=provider_id,
                            message=msg, sender_role=current_user.role)
            db.session.add(chat_msg)
            db.session.commit()

    chats = Chat.query.filter_by(provider_id=provider_id, customer_id=customer_id).order_by(Chat.timestamp.asc()).all()
    return render_template('chat.html', chats=chats, provider_id=provider_id, customer_id=customer_id, partner_name=partner_name)

@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    if not room:
        emit('status', {'msg': 'Invalid chat room.'})
        return
    if not current_user.is_authenticated:
        emit('status', {'msg': 'Please log in to join the chat.'})
        return
    join_room(room)
    emit('status', {'msg': f'{current_user.username} joined the chat.'}, room=room)

@socketio.on('send_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        emit('status', {'msg': 'Please log in to send messages.'})
        return

    message = data.get('message', '').strip()
    provider_id = data.get('provider_id')
    customer_id = data.get('customer_id')
    room = data.get('room')

    if current_user.role == 'customer':
        customer_id = current_user.id

    if not message or not provider_id or not customer_id or not room:
        emit('status', {'msg': 'Message not sent. Missing required data.'})
        return

    if current_user.role == 'provider' and current_user.id != provider_id:
        emit('status', {'msg': 'Unauthorized provider.'})
        return

    if current_user.role == 'customer' and current_user.id != customer_id:
        emit('status', {'msg': 'Unauthorized customer.'})
        return

    provider = User.query.get(provider_id)
    if not provider:
        emit('status', {'msg': 'Provider not found.'})
        return

    chat_msg = Chat(customer_id=customer_id, provider_id=provider_id,
                    message=message, sender_role=current_user.role)
    db.session.add(chat_msg)
    db.session.commit()

    emit('receive_message', {
        'message': message,
        'sender_role': current_user.role,
        'sender_name': current_user.username,
        'timestamp': datetime.utcnow().strftime('%H:%M')
    }, room=room)

    emit('message_notification', {
        'message': message,
        'sender_role': current_user.role,
        'sender_name': current_user.username,
        'provider_id': provider_id,
        'customer_id': customer_id,
        'timestamp': datetime.utcnow().strftime('%H:%M')
    }, room=room)

@app.route('/provider/chats')
@login_required
def provider_chats():
    """Provider chat inbox page for customers who have initiated a conversation."""
    if current_user.role != 'provider':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    chats = Chat.query.filter_by(provider_id=current_user.id).order_by(Chat.timestamp.desc()).all()
    conversations = []
    seen = set()
    for chat in chats:
        if not chat.customer_id or chat.customer_id in seen:
            continue
        seen.add(chat.customer_id)
        customer = User.query.get(chat.customer_id)
        if customer:
            conversations.append({
                'customer': customer,
                'last_message': chat.message,
                'timestamp': chat.timestamp,
                'customer_id': chat.customer_id
            })

    return render_template('provider_chats.html', conversations=conversations)

@app.route('/rate/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def rate_service(booking_id):
    """Rate a service - Customer provides 1-5 star rating"""
    booking = Booking.query.get_or_404(booking_id)

    # Only customer can rate their own bookings
    if booking.customer_id != current_user.id:
        flash("You can only rate your own bookings.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        rating = int(request.form['rating'])
        # Validate rating is between 1-5
        if 1 <= rating <= 5:
            booking.rating = rating
            db.session.commit()
            flash("Thank you for rating!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid rating.", "danger")

    return render_template('rate_service.html', booking=booking)

@app.route('/book/<int:service_id>', methods=['GET', 'POST'])
@login_required
def book(service_id):
    """Book a service - Customer fills detailed booking form"""
    service = Service.query.get_or_404(service_id)
    provider_id = service.provider_id

    if request.method == 'POST':
        # Create booking with customer details
        booking = Booking(
            customer_id=current_user.id,
            provider_id=provider_id,
            service_id=service.id,
            customer_name=request.form['customer_name'],
            age=request.form['age'],
            gender=request.form['gender'],
            address=request.form['address'],
            date=request.form['date'],
            time=request.form['time'],
            payment_method=request.form['payment_method'],
            status="Pending"  # Awaiting provider acceptance
        )
        db.session.add(booking)
        db.session.commit()
        flash("Booking request sent to provider!", "success")
        return redirect(url_for('customer_notifications'))

    return render_template('booking_form.html', service=service)


# ----------- Admin Dashboard ------------

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Admin access only.', 'danger')
        return redirect(url_for('index'))

    # Gather statistics and data for admin dashboard
    providers = User.query.filter_by(role="provider").all()
    customers = User.query.filter_by(role="customer").all()
    active_services = Service.query.filter_by(is_available=True).all()
    bookings = Booking.query.all()
    complaints = Complaint.query.order_by(Complaint.timestamp.desc()).all()

    return render_template(
        'admin_dashboard.html',
        providers=providers,
        customers=customers,
        active_services=active_services,
        bookings=bookings,
        complaints=complaints
    )

# ✅ Delete Provider
@app.route('/admin/delete_provider/<int:provider_id>')
@login_required
def delete_provider(provider_id):
    if current_user.role == "admin":
        provider = User.query.get_or_404(provider_id)
        db.session.delete(provider)
        db.session.commit()
        flash("Provider account deleted!", "success")
    return redirect(url_for('admin'))

# ✅ Delete Customer
@app.route('/admin/delete_customer/<int:customer_id>')
@login_required
def delete_customer(customer_id):
    """Admin action - Delete a customer account"""
    if current_user.role == "admin":
        customer = User.query.get_or_404(customer_id)
        db.session.delete(customer)
        db.session.commit()
        flash("Customer account deleted!", "success")
    return redirect(url_for('admin'))

# ✅ Delete Service
@app.route('/admin/delete_service/<int:service_id>')
@login_required
def delete_service(service_id):
    """Admin action - Delete a service listing"""
    if current_user.role == "admin":
        service = Service.query.get_or_404(service_id)
        db.session.delete(service)
        db.session.commit()
        flash("Service deleted successfully!", "success")
    return redirect(url_for('admin'))

# ✅ Mark Complaint Resolved
@app.route('/admin/resolve_complaint/<int:complaint_id>')
@login_required
def resolve_complaint(complaint_id):
    if current_user.role == "admin":
        complaint = Complaint.query.get_or_404(complaint_id)
        complaint.status = "Resolved"
        db.session.commit()
        flash("Complaint marked as resolved!", "success")
    return redirect(url_for('admin'))

# ==========================================
# (Enhancement 3 )
# Handles the creation of secure checkout sessions and payment success callbacks.
# ==========================================

@app.route('/create-checkout-session/<int:booking_id>', methods=['POST'])
@login_required
def create_checkout_session(booking_id):
    """
    [Enhancement 3: Stripe API] 
    Creates a checkout session dynamically based on service price.
    Redirects the user to the Stripe Hosted Checkout page.
    """
    # Only customers can make payments
    if current_user.role != 'customer':
        return redirect(url_for('index'))
        
    booking = Booking.query.get_or_404(booking_id)
    service = Service.query.get(booking.service_id)

    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],  # Accept credit card payments
            line_items=[
                {
                    'price_data': {
                        'currency': 'myr',  # Malaysian Ringgit
                        'unit_amount': int(service.price * 100),  # Stripe uses smallest currency unit (sen)
                        'product_data': {
                            'name': service.name,
                            'description': f"Payment for Booking ID: #{booking.id}",
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            # Redirect after successful payment
            success_url=url_for('payment_success', booking_id=booking.id, _external=True),
            # Redirect if customer cancels payment
            cancel_url=url_for('customer_notifications', _external=True),
        )
        # Redirect to Stripe hosted checkout
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('customer_notifications'))

@app.route('/payment_success/<int:booking_id>')
@login_required
def payment_success(booking_id):
    """
    [Enhancement 3: Stripe API] 
    Callback route after successful payment to update Database status to 'Paid'.
    """
    booking = Booking.query.get_or_404(booking_id)
    booking.status = "Paid"  # Update booking status after successful payment
    db.session.commit()
    flash("Payment successful! The provider has been notified.", "success")
    return redirect(url_for('customer_notifications'))

# -------------------- Run & Auto Admin Creation --------------------

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()

        # ✅ Auto-create admin if not exists
        if not User.query.filter_by(role='admin').first():
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password=generate_password_hash("admin123", method='pbkdf2:sha256'),
                role="admin"
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Default admin created: Email: admin@example.com | Password: admin123")

    # Start Flask development server with SocketIO support (debug=True enables hot-reload)
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
