from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv() 

app = Flask(__name__)

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")

# Use os.getenv to pull the keys securely
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google OAuth Configuration
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID') #
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


db = SQLAlchemy(app)
oauth = OAuth(app)

# Configure Google OAuth
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    rides = db.relationship('Ride', backref='creator', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    cost_per_person = db.Column(db.Integer, nullable=False)
    meeting_point = db.Column(db.String(200), nullable=False)
    drop_point = db.Column(db.String(200), nullable=False, default='Katpadi Railway Station')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='ride', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seats_booked = db.Column(db.Integer, nullable=False)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        rides = Ride.query.filter(Ride.departure_time > datetime.now(), Ride.available_seats > 0).order_by(Ride.departure_time).all()
        
        # Get user's bookings to check which rides they've already booked
        user_bookings = {booking.ride_id for booking in Booking.query.filter_by(user_id=session['user_id']).all()}
        
        return render_template('dashboard.html', rides=rides, user_bookings=user_bookings)
    return render_template('index.html')

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        # Check if email is from VIT
        if not user_info['email'].endswith('@vitstudent.ac.in'):
            flash('Please use your VIT student email (@vitstudent.ac.in)', 'error')
            return redirect(url_for('index'))
        
        # Check if user exists
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            # Create new user
            user = User(
                name=user_info['name'],
                email=user_info['email'],
                google_id=user_info['sub']
            )
            db.session.add(user)
            db.session.commit()
        
        # Log in user
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        
        flash('Login successful!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/complete_profile', methods=['GET', 'POST'])
def complete_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # If user not found, clear session and redirect to login
    if not user:
        session.clear()
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        phone = request.form['phone']
        user.phone = phone
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('complete_profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # If user not found, clear session and redirect to login
    if not user:
        session.clear()
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        phone = request.form['phone']
        user.phone = phone
        db.session.commit()
        flash('Phone number updated successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/create_ride', methods=['GET', 'POST'])
def create_ride():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # If user not found, clear session and redirect to login
    if not user:
        session.clear()
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
    
    # Check if user has completed profile
    if not user.phone:
        flash('Please complete your profile before creating a ride', 'error')
        return redirect(url_for('complete_profile'))

    if request.method == 'POST':
        departure_time = datetime.strptime(request.form['departure_time'], '%Y-%m-%dT%H:%M')
        total_seats = int(request.form['total_seats'])
        cost_per_person = int(request.form['cost_per_person'])
        meeting_point = request.form['meeting_point']
        drop_point = request.form['drop_point']
        notes = request.form.get('notes', '')

        ride = Ride(
            user_id=session['user_id'],
            departure_time=departure_time,
            total_seats=total_seats,
            available_seats=total_seats,
            cost_per_person=cost_per_person,
            meeting_point=meeting_point,
            drop_point=drop_point,
            notes=notes
        )
        db.session.add(ride)
        db.session.commit()

        flash('Ride created successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('create_ride.html')

@app.route('/book_ride/<int:ride_id>', methods=['POST'])
def book_ride(ride_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # If user not found, clear session and redirect to login
    if not user:
        session.clear()
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
    
    # Check if user has completed profile
    if not user.phone:
        flash('Please complete your profile before booking a ride', 'error')
        return redirect(url_for('complete_profile'))

    ride = Ride.query.get_or_404(ride_id)

    if ride.user_id == session['user_id']:
        flash('You cannot book your own ride', 'error')
        return redirect(url_for('index'))

    # Check if user has already booked this ride
    existing_booking = Booking.query.filter_by(ride_id=ride_id, user_id=session['user_id']).first()
    if existing_booking:
        flash('You have already booked this ride', 'error')
        return redirect(url_for('index'))

    # Only allow 1 seat per person
    seats_requested = 1

    if seats_requested > ride.available_seats:
        flash('Not enough seats available', 'error')
        return redirect(url_for('index'))

    booking = Booking(
        ride_id=ride_id,
        user_id=session['user_id'],
        seats_booked=seats_requested
    )
    ride.available_seats -= seats_requested

    db.session.add(booking)
    db.session.commit()

    flash(f'Successfully booked {seats_requested} seat!', 'success')
    return redirect(url_for('my_bookings'))

@app.route('/cancel_booking/<int:ride_id>', methods=['POST'])
def cancel_booking(ride_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    booking = Booking.query.filter_by(ride_id=ride_id, user_id=session['user_id']).first()
    
    if not booking:
        flash('Booking not found', 'error')
        return redirect(url_for('index'))
    
    ride = Ride.query.get(ride_id)
    
    # Return the seat to available seats
    ride.available_seats += booking.seats_booked
    
    # Delete the booking
    db.session.delete(booking)
    db.session.commit()
    
    flash('Booking cancelled successfully', 'success')
    return redirect(url_for('index'))

@app.route('/my_rides')
def my_rides():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    rides = Ride.query.filter_by(user_id=session['user_id']).order_by(Ride.departure_time.desc()).all()
    return render_template('my_rides.html', rides=rides)

@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    bookings = Booking.query.filter_by(user_id=session['user_id']).order_by(Booking.booked_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/ride_details/<int:ride_id>')
def ride_details(ride_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    ride = Ride.query.get_or_404(ride_id)
    bookings = Booking.query.filter_by(ride_id=ride_id).all()
    
    # Check if current user has booked this ride
    user_booking = Booking.query.filter_by(ride_id=ride_id, user_id=session['user_id']).first()
    
    return render_template('ride_details.html', ride=ride, bookings=bookings, user_booking=user_booking)

@app.route('/delete_ride/<int:ride_id>', methods=['POST'])
def delete_ride(ride_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    ride = Ride.query.get_or_404(ride_id)

    # Ensure only the creator can delete the ride
    if ride.user_id != session['user_id']:
        flash('You are not authorized to delete this ride', 'error')
        return redirect(url_for('my_rides'))

    # Optional: prevent deletion if there are existing bookings
    if ride.bookings:
        flash('Cannot delete ride with existing bookings', 'error')
        return redirect(url_for('my_rides'))

    Booking.query.filter_by(ride_id=ride_id).delete()

    db.session.delete(ride)
    db.session.commit()

    flash('Ride deleted successfully', 'success')
    return redirect(url_for('my_rides'))

@app.route('/reset_db')
def reset_db():
    try:
        # 1. Drop all tables defined in the models
        db.drop_all()
        # 2. Recreate all tables
        db.create_all()
        return "Database tables cleared and recreated successfully!"
    except Exception as e:
        return f"An error occurred during reset: {e}"

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)