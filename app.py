from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vitcabshare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    rides = db.relationship('Ride', backref='creator', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
        return render_template('dashboard.html', rides=rides)
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        user = User(name=name, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/create_ride', methods=['GET', 'POST'])
def create_ride():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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

    ride = Ride.query.get_or_404(ride_id)
    seats_requested = int(request.form['seats'])

    if ride.user_id == session['user_id']:
        flash('You cannot book your own ride', 'error')
        return redirect(url_for('index'))

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

    flash(f'Successfully booked {seats_requested} seat(s)!', 'success')
    return redirect(url_for('my_bookings'))

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
    return render_template('ride_details.html', ride=ride, bookings=bookings)

# Initialize database
with app.app_context():
    db.create_all()




if __name__ == '__main__':
    app.run(debug=True)