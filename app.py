<<<<<<< HEAD
from flask import Flask, render_template, redirect, url_for, session, request, flash, abort, current_app
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import date, datetime, timedelta
from collections import defaultdict
from functools import wraps
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func
import uuid


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


UPLOAD_FOLDER = "static/movie-poster"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


app.config["REMEMBER_COOKIE_DURATION"] = 0
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not getattr(current_user, "is_admin", False):
            abort(403)  
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            if not current_user.is_authenticated:
                return login_manager.unauthorized()

            if current_user.role not in roles:
                flash("Access denied!", "danger")
                return redirect(url_for("index"))   

            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def create_seats_for_showtime(showtime_id):
    existing = Seat.query.filter_by(showtime_id=showtime_id).first()
    if existing:
        return  

    gold_rows = ["A", "B", "C", "D", "E", "F"]
    silver_rows = ["G", "H", "I"]

    seats = []
    for row in gold_rows:
        for num in range(1, 21):
            seats.append(Seat(
                showtime_id=showtime_id,
                seat_row=row,
                seat_number=num,
                seat_type="royal_gold",
                price=250,
                is_booked=False
            ))

    for row in silver_rows:
        for num in range(1, 21):
            seats.append(Seat(
                showtime_id=showtime_id,
                seat_row=row,
                seat_number=num,
                seat_type="royal_silver",
                price=220,
                is_booked=False
            ))

    db.session.bulk_save_objects(seats)
    db.session.commit()


# MODELS

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user") 
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Movie(db.Model):
    __tablename__ = "movies"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)
    language = db.Column(db.String(50))
    genres = db.Column(db.String(100))
    certificate = db.Column(db.String(10))
    rating = db.Column(db.Float)
    poster = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    featured_image = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Theatre(db.Model):
    __tablename__ = "theatres"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    is_imax = db.Column(db.Boolean, default=False)
    is_3d = db.Column(db.Boolean, default=False)
    is_dolby = db.Column(db.Boolean, default=False)
    is_4dx = db.Column(db.Boolean, default=False)

class Showtime(db.Model):
    __tablename__ = "showtimes"
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)
    theatre_id = db.Column(db.Integer, db.ForeignKey("theatres.id"), nullable=False)
    movie = db.relationship('Movie', backref='showtimes')
    theatre = db.relationship('Theatre', backref='showtimes')
    show_date = db.Column(db.Date, nullable=False)
    show_time = db.Column(db.Time, nullable=False)

class Seat(db.Model):
    __tablename__ = "seats"
    id = db.Column(db.Integer, primary_key=True)
    showtime_id = db.Column(db.Integer, db.ForeignKey("showtimes.id"), nullable=False)
    seat_row = db.Column(db.String(1))
    seat_number = db.Column(db.Integer)
    seat_type = db.Column(db.String(20))
    price = db.Column(db.Integer)
    is_booked = db.Column(db.Boolean, default=False)
    locked_until = db.Column(db.DateTime, nullable=True)

class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    showtime_id = db.Column(db.Integer, db.ForeignKey("showtimes.id"), nullable=False)
    total_amount = db.Column(db.Integer)
    booking_time = db.Column(db.DateTime, default=datetime.now)
    booking_seats = db.relationship("BookingSeat", backref="booking")
    showtime = db.relationship('Showtime', backref='bookings')
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.now)

class BookingSeat(db.Model):
    __tablename__ = "booking_seats"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey("seats.id"), nullable=False)
    seat = db.relationship("Seat")

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    refunds = db.relationship('Refund', backref='payment', lazy=True, cascade="all, delete-orphan")

class Refund(db.Model):
    __tablename__ = 'refunds' 
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    refund_amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    refund_reason = db.Column(db.String(255))
    gateway_refund_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default='pending') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SignupForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create Account")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")

@app.route("/")
def index():
    hero_movies = (
        Movie.query
        .filter(Movie.is_active == True, Movie.is_featured == True)
        .order_by(Movie.created_at.desc())
        .limit(3)
        .all()
    )

    all_movies = Movie.query.all()

    return render_template(
        "index.html",
        hero_movies=hero_movies,
        all_movies=all_movies
    )

@app.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template("movie.html", movie=movie)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists", "danger")
            return render_template("signup.html", form=form)

        user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("index"))

    return render_template("signup.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)

            if user.role == "admin":
                return redirect(url_for("admin_movies"))
            elif user.role == "manager":
                return redirect(url_for("admin_movies"))
            elif user.role == "staff":
                return redirect(url_for("admin_bookings"))
            else:
                return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()

    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/select-showtime/<int:movie_id>")
@login_required
def select_showtime(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    today = date.today()

    dates = [today + timedelta(days=i) for i in range(7)]

    date_str = request.args.get("date")
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    rows = (
        db.session.query(Showtime, Theatre)
        .join(Theatre, Showtime.theatre_id == Theatre.id)
        .filter(Showtime.movie_id == movie.id)
        .filter(Showtime.show_date == selected_date)
        .order_by(Theatre.id, Showtime.show_time)
        .all()
    )

    theatres_map = {}
    for showtime, theatre in rows:
        if theatre.id not in theatres_map:
            theatres_map[theatre.id] = {"theatre": theatre, "times": []}
        theatres_map[theatre.id]["times"].append(showtime)

    return render_template(
        "select_showtime.html",
        movie=movie,
        theatres_map=theatres_map,
        dates=dates,
        selected_date=selected_date,
        current_date=today
    )

@app.route("/go-to-seats", methods=["POST"])
@login_required
def go_to_seats():
    showtime_id = request.form.get("showtime_id")

    if not showtime_id:
        flash("Please select a showtime.", "warning")
        return redirect(request.referrer)

    return redirect(url_for("select_seats", showtime_id=showtime_id))


@app.route("/select-seats/<int:showtime_id>")
@login_required
def select_seats(showtime_id):
    showtime = Showtime.query.get_or_404(showtime_id)
    movie = Movie.query.get_or_404(showtime.movie_id)
    theatre = Theatre.query.get_or_404(showtime.theatre_id)

    create_seats_for_showtime(showtime_id)

    seats = (
        Seat.query
        .filter_by(showtime_id=showtime_id)
        .order_by(Seat.seat_type, Seat.seat_row, Seat.seat_number)
        .all()
    )

    grouped = defaultdict(lambda: defaultdict(list))

    for seat in seats:
        grouped[seat.seat_type][seat.seat_row].append(seat)

    return render_template(
        "select_seats.html",
        movie=movie,
        theatre=theatre,
        showtime=showtime,
        grouped=grouped
    )

@app.route("/select-seats-post", methods=["POST"])
@login_required
def select_seats_post():

    seat_ids = request.form.getlist("seat_ids")
    showtime_id = request.form.get("showtime_id")

    if not seat_ids:
        flash("No seats selected.", "danger")
        return redirect(url_for("select_seats", showtime_id=showtime_id))

    seats = Seat.query.filter(Seat.id.in_(seat_ids)).all()

    for seat in seats:

        if seat.is_booked:
            flash("Seat already booked!", "danger")
            return redirect(url_for("select_seats", showtime_id=showtime_id))

        if seat.locked_until and seat.locked_until > datetime.now():
            flash("Seat temporarily locked!", "warning")
            return redirect(url_for("select_seats", showtime_id=showtime_id))

        seat.locked_until = datetime.now() + timedelta(minutes=5)

    db.session.commit()

    session["selected_seats"] = seat_ids
    session["showtime_id"] = showtime_id

    return redirect(url_for("payment"))

@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
  
    seat_ids = session.get("selected_seats")
    showtime_id = session.get("showtime_id")

    if not seat_ids or not showtime_id:
        flash("Please select seats first.", "danger")
        return redirect(url_for("index"))

    seats = Seat.query.filter(Seat.id.in_(seat_ids)).all()
    showtime = Showtime.query.get_or_404(showtime_id)
    movie = Movie.query.get(showtime.movie_id)
    theatre = Theatre.query.get(showtime.theatre_id)

    total = sum(seat.price for seat in seats)
    fees = int(total * 0.08)
    grand_total = total + fees

    if request.method == "POST":
        
        payment_method = request.form.get("payment_method")
        
        if not payment_method:
            flash("You must select a payment method (UPI or Card) to continue.", "danger")
            return redirect(url_for("payment"))
            
        valid_methods = ["UPI", "Debit/Credit Card"]
        if payment_method not in valid_methods:
            flash("Invalid payment method selected.", "danger")
            return redirect(url_for("payment"))

        for seat in seats:
            if not seat.locked_until or seat.locked_until < datetime.now():
                flash("Seat lock expired! Please reselect.", "danger")
                return redirect(url_for("select_seats", showtime_id=showtime_id))

            if seat.is_booked:
                flash("Seat already booked!", "danger")
                return redirect(url_for("select_seats", showtime_id=showtime_id))

            seat.is_booked = True
            seat.locked_until = None

        booking = Booking(
            user_id=current_user.id,
            showtime_id=showtime_id,
            total_amount=grand_total,
            status="confirmed"
        )
        db.session.add(booking)
        
        db.session.flush() 

        # 6. Link the Seats to the Booking
        for seat in seats:
            db.session.add(BookingSeat(
                booking_id=booking.id,
                seat_id=seat.id
            ))

        transaction_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        
        payment_record = Payment(
            booking_id=booking.id,
            user_id=current_user.id,    
            amount=grand_total,          
            payment_method=payment_method, 
            transaction_id=transaction_id,
            status="completed"          
        )
        db.session.add(payment_record)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("A database error occurred during payment.", "danger")
            return redirect(url_for("index"))

        # 9. Clean up the session and move to the success page
        session.pop("selected_seats", None)
        session.pop("showtime_id", None)
        
        # Store the booking ID so the success ticket page can display it
        session["last_booking_id"] = booking.id

        return redirect(url_for("booking_success"))

    # If it's a GET request, just render the payment page
    return render_template(
        "payment.html",
        seats=seats,
        total=total,
        fees=fees,
        grand_total=grand_total,
        movie=movie,
        theatre=theatre,
        showtime=showtime
    )

@app.route("/booking_success")
@login_required
def booking_success():
    
    booking = (
        Booking.query
        .filter_by(user_id=current_user.id)
        .order_by(Booking.id.desc())
        .first()
    )

    if not booking:
        flash("No booking found.", "danger")
        return redirect(url_for("index"))

    showtime = Showtime.query.get(booking.showtime_id)
    movie = Movie.query.get(showtime.movie_id)
    theatre = Theatre.query.get(showtime.theatre_id)

    booking_seats = BookingSeat.query.filter_by(booking_id=booking.id).all()
    seats = Seat.query.filter(Seat.id.in_([bs.seat_id for bs in booking_seats])).all()

    return render_template(
        "booking_success.html",
        booking=booking,
        movie=movie,
        theatre=theatre,
        showtime=showtime,
        seats=seats
    )

@app.route("/account")
@login_required
def account():
   
    bookings = (
        db.session.query(Booking, Showtime, Movie, Theatre)
        .join(Showtime, Booking.showtime_id == Showtime.id)
        .join(Movie, Showtime.movie_id == Movie.id)
        .join(Theatre, Showtime.theatre_id == Theatre.id)
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.booking_time.desc())
        .all()
    )

    booking_list = []

    for booking, showtime, movie, theatre in bookings:
       
        seat_rows = (
            db.session.query(Seat)
            .join(BookingSeat, BookingSeat.seat_id == Seat.id)
            .filter(BookingSeat.booking_id == booking.id)
            .all()
        )

        seat_labels = [f"{s.seat_row}{s.seat_number}" for s in seat_rows]

        booking_list.append({
            "id": booking.id,
            "movie_title": movie.title,
            "theatre_name": theatre.name,
            "show_date": showtime.show_date.strftime("%d %b %Y"),
            "show_time": showtime.show_time.strftime("%I:%M %p"),
            "seats": ", ".join(seat_labels),
            "amount": booking.total_amount,
            "booking_time": booking.booking_time.strftime("%d %b %Y, %I:%M %p")
        })

    return render_template("account.html", bookings=booking_list)

# Admin Route

@app.route("/admin/reports")
@login_required
@admin_required
@roles_required("super_admin", "admin")
def admin_reports():

    total_revenue = db.session.query(func.sum(Booking.total_amount)).scalar() or 0
    total_bookings = Booking.query.count()
    total_users = User.query.count()

    today = datetime.utcnow().date()
    today_bookings = Booking.query.filter(func.date(Booking.booking_time) == today).count()
    today_revenue = db.session.query(func.sum(Booking.total_amount))\
        .filter(func.date(Booking.booking_time) == today).scalar() or 0

    last_7_days = []
    revenue_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        revenue = db.session.query(func.sum(Booking.total_amount))\
            .filter(func.date(Booking.booking_time) == day).scalar() or 0

        last_7_days.append(day.strftime("%d %b"))
        revenue_data.append(int(revenue))

    top_movies = db.session.query(
        Movie.title,
        func.count(Booking.id).label("total_bookings")
    ).join(Showtime, Showtime.movie_id == Movie.id)\
     .join(Booking, Booking.showtime_id == Showtime.id)\
     .group_by(Movie.title)\
     .order_by(func.count(Booking.id).desc())\
     .limit(5).all()

    return render_template(
        "admin/reports.html",
        total_revenue=total_revenue,
        total_bookings=total_bookings,
        total_users=total_users,
        today_bookings=today_bookings,
        today_revenue=today_revenue,
        labels=last_7_days,
        revenue_data=revenue_data,
        top_movies=top_movies
    )

@app.route("/admin/movies")
@login_required
@roles_required("super_admin", "admin")
def admin_movies():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template("admin/movies.html", movies=movies)

@app.route("/admin/movies/add", methods=["GET", "POST"])
@login_required
@admin_required
@roles_required("super_admin", "admin")
def admin_add_movie():
    if request.method == "POST":
        print("Files received:", request.files) 
        print("Form data:", request.form)
        
        poster_file = request.files.get("poster")
        poster_filename = None
        if poster_file and poster_file.filename:
            filename = secure_filename(poster_file.filename)
            poster_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            poster_file.save(poster_path)
            poster_filename = filename

        featured_file = request.files.get("featured_image")
        featured_filename = None
        if featured_file and featured_file.filename:
            f_filename = secure_filename(featured_file.filename)
            featured_path = os.path.join(app.config["UPLOAD_FOLDER"], f_filename)
            featured_file.save(featured_path)
            featured_filename = f_filename

        movie = Movie(
            title=request.form.get("title"),
            language=request.form.get("language"),
            genres=request.form.get("genres"),
            certificate=request.form.get("certificate"),
            duration=request.form.get("duration"),
            rating=request.form.get("rating"),
            poster=poster_filename,
            featured_image=featured_filename, 
            is_featured="is_featured" in request.form,
            is_active=True
        )

        db.session.add(movie)
        db.session.commit()

        flash("Movie added successfully!", "success")
        return redirect(url_for("admin_movies"))

    return render_template("admin/movie_form.html")

@app.route("/admin/movies/edit/<int:movie_id>", methods=["POST"])
@login_required
@admin_required
def admin_edit_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    try:
        movie.title = request.form.get("title")
        movie.language = request.form.get("language")
        movie.genres = request.form.get("genres")
        movie.certificate = request.form.get("certificate")
        movie.duration = request.form.get("duration", type=int) or 0
        movie.rating = request.form.get("rating", type=float) or 0.0
        movie.is_featured = "is_featured" in request.form

        file = request.files.get("poster")
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            unique_filename = f"movie_{movie.id}_{filename}"
            upload_path = os.path.join(current_app.root_path, 'static/movie-poster', unique_filename)
            file.save(upload_path)
            movie.poster = unique_filename

        db.session.commit()
        flash(f"Updated '{movie.title}' successfully!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for("admin_movies"))

@app.route("/admin/movies/delete/<int:movie_id>")
@login_required
@admin_required
def admin_delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if Showtime.query.filter_by(movie_id=movie_id).first():
        flash("Cannot delete movie: It has active showtimes.", "danger")
        return redirect(url_for("admin_movies"))

    db.session.delete(movie)
    db.session.commit()

    flash("Movie deleted successfully!", "success")
    return redirect(url_for("admin_movies"))

@app.route("/admin/theatres")
@login_required
@admin_required
def admin_theatres():
    theatres = Theatre.query.all()
    return render_template("admin/theatres.html", theatres=theatres)

@app.route("/admin/theatres/add", methods=["POST"])
@login_required
@admin_required
def admin_add_theatre():
    t = Theatre(
        name=request.form["name"],
        location=request.form["location"],
        is_imax="is_imax" in request.form,
        is_3d="is_3d" in request.form,
        is_4dx="is_4dx" in request.form,
        is_dolby="is_dolby" in request.form,
    )
    db.session.add(t)
    db.session.commit()
    flash("Theatre added!", "success")
    return redirect(url_for("admin_theatres"))

@app.route("/admin/theatres/edit/<int:theatre_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_theatre(theatre_id):
    theatre = Theatre.query.get_or_404(theatre_id)

    if request.method == "POST":
        theatre.name = request.form.get("name")
        theatre.location = request.form.get("location")

        theatre.is_imax = "is_imax" in request.form
        theatre.is_3d = "is_3d" in request.form
        theatre.is_4dx = "is_4dx" in request.form
        theatre.is_dolby = "is_dolby" in request.form

        db.session.commit()
        flash("Theatre updated successfully!", "success")
        return redirect(url_for("admin_theatres"))

    return render_template("admin/edit_theatre.html", theatre=theatre)

@app.route("/admin/theatres/delete/<int:theatre_id>")
@login_required
@admin_required
def admin_delete_theatre(theatre_id):
    theatre = Theatre.query.get_or_404(theatre_id)

    if Showtime.query.filter_by(theatre_id=theatre_id).first():
        flash("Cannot delete theatre with showtimes!", "danger")
        return redirect(url_for("admin_theatres"))

    db.session.delete(theatre)
    db.session.commit()

    flash("Theatre deleted successfully!", "success")
    return redirect(url_for("admin_theatres"))

@app.route('/admin/booking/<int:booking_id>/cancel', methods=['GET', 'POST'])
@login_required
def admin_delete_bookings(booking_id):

    booking = Booking.query.get_or_404(booking_id)
    
    if booking.status == 'cancelled':
        flash('This booking is already cancelled.', 'warning')
        return redirect(url_for('admin_bookings'))

    booking.status = 'cancelled'
    
    for booked_seat in booking.booking_seats:
        booked_seat.seat.is_booked = False
        
    payment = Payment.query.filter_by(booking_id=booking.id).first()
    
    if payment and payment.status == 'completed':
        payment.status = 'refunded'
        
        new_refund = Refund(
            payment_id=payment.id,
            user_id=booking.user_id,
            refund_amount=payment.amount, # Or subtract cancellation fees here
            reason="Admin Cancelled Booking",
            status="processed"
        )
        db.session.add(new_refund)

    db.session.commit()
    
    flash(f'Booking #{booking.id} cancelled and ₹{payment.amount} refunded.', 'success')
    return redirect(url_for('admin_bookings'))

@app.route("/admin/showtimes")
@login_required
@admin_required
def admin_showtimes():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Showtime.query.join(Movie).join(Theatre)

    if search:
        query = query.filter(
            db.or_(
                Movie.title.ilike(f"%{search}%"),
                Theatre.name.ilike(f"%{search}%")
            )
        )
    showtimes_paginated = query.order_by(
        Showtime.show_date.desc(), 
        Showtime.show_time.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    movies = Movie.query.all()
    theatres = Theatre.query.all()
    return render_template(
        "admin/showtimes.html", 
        showtimes=showtimes_paginated, 
        movies=movies, 
        theatres=theatres,
        search=search
    )

@app.route("/admin/showtimes/add", methods=["POST"])
@login_required
@admin_required
def admin_add_showtime():

    movie_id = request.form.get("movie_id")
    theatre_id = request.form.get("theatre_id")
    start_date = request.form.get("start_date")
    days = int(request.form.get("days", 1))

    show_times = request.form.getlist("show_times")

    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    for i in range(days):

        current_date = start_date + timedelta(days=i)

        for t in show_times:

            if not t:
                continue

            show_time = datetime.strptime(t, "%H:%M").time()

            st = Showtime(
                movie_id=movie_id,
                theatre_id=theatre_id,
                show_date=current_date,
                show_time=show_time
            )

            db.session.add(st)
            db.session.flush()

            create_seats_for_showtime(st.id)

    db.session.commit()

    flash("Showtimes generated successfully!", "success")

    return redirect(url_for("admin_showtimes"))

@app.route("/admin/showtimes/edit/<int:showtime_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_showtime(showtime_id):
    showtime = Showtime.query.get_or_404(showtime_id)
    movies = Movie.query.all()
    theatres = Theatre.query.all()

    if request.method == "POST":
        movie_id = request.form.get("movie_id")
        theatre_id = request.form.get("theatre_id")
        show_date = request.form.get("show_date")
        show_time = request.form.get("show_time")

        if not all([movie_id, theatre_id, show_date, show_time]):
            flash("All fields are required.", "danger")
            return redirect(url_for('admin_edit_showtime', showtime_id=showtime.id))

        showtime.movie_id = int(movie_id)
        showtime.theatre_id = int(theatre_id)
        showtime.show_date = datetime.strptime(show_date, "%Y-%m-%d").date()
        
        try:
            showtime.show_time = datetime.strptime(show_time, "%H:%M").time()
        except ValueError:
            
            showtime.show_time = datetime.strptime(show_time, "%H:%M:%S").time()

        db.session.commit()
        flash("Showtime updated successfully!", "success")
        return redirect(url_for("admin_showtimes"))

    return render_template("admin/edit_showtime.html", showtime=showtime, movies=movies, theatres=theatres)

@app.route("/admin/showtimes/delete/<int:showtime_id>")
@login_required
@admin_required
def admin_delete_showtime(showtime_id):
    showtime = Showtime.query.get_or_404(showtime_id)

    existing_bookings = Booking.query.filter_by(showtime_id=showtime_id).first()
    
    if existing_bookings:
        flash("Cannot delete this showtime: Tickets have already been booked!", "danger")
        return redirect(url_for("admin_showtimes"))


    Seat.query.filter_by(showtime_id=showtime_id).delete()

    db.session.delete(showtime)
    db.session.commit()

    flash("Showtime deleted successfully.", "success")
    return redirect(url_for("admin_showtimes"))

@app.route("/admin/showtimes/clear", methods=["POST"])
@login_required
@admin_required
def admin_clear_showtimes():

    BookingSeat.query.delete()
    Payment.query.delete()
    Booking.query.delete()
    Seat.query.delete()
    Showtime.query.delete()

    db.session.commit()

    flash("All showtimes + bookings cleared!", "success")
    return redirect(url_for("admin_showtimes"))

@app.route("/admin/bookings")
@login_required
@roles_required("super_admin", "admin", "staff")
def admin_bookings():
    # Fetch all bookings, newest first
    bookings = Booking.query.order_by(Booking.booking_time.desc()).all()

    booking_list = []

    for booking in bookings:
        showtime = Showtime.query.get(booking.showtime_id)
        movie = Movie.query.get(showtime.movie_id)
        theatre = Theatre.query.get(showtime.theatre_id)
        user = User.query.get(booking.user_id)

        booking_seats = BookingSeat.query.filter_by(booking_id=booking.id).all()

        seat_rows = Seat.query.filter(
            Seat.id.in_([bs.seat_id for bs in booking_seats])
        ).all()

        seat_labels = [f"{s.seat_row}{s.seat_number}" for s in seat_rows]

        booking_list.append({
            "id": booking.id,
            "user_id": booking.user_id,
            "movie": movie,
            "theatre": theatre,
            "showtime": showtime,
            "seats": seat_labels,
            "total_amount": booking.total_amount,
            "booking_time": booking.booking_time,
            "status": booking.status,

        })

    return render_template("admin/bookings.html", bookings=booking_list)

@app.route("/admin/bookings/delete/<int:booking_id>")
@login_required
@roles_required("admin", "super_admin")
def admin_delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.status == "cancelled":
        flash("This booking is already cancelled.", "warning")
        return redirect(url_for("admin_bookings"))

    booking_seats = BookingSeat.query.filter_by(booking_id=booking.id).all()
    for bs in booking_seats:
        seat = Seat.query.get(bs.seat_id)
        if seat:
            seat.is_booked = False
            seat.locked_until = None 

    booking.status = "cancelled"

    payment = Payment.query.filter_by(booking_id=booking.id).first()
    refund_amount = 0

    if payment and payment.status == "completed":
        payment.status = "refunded"
        refund_amount = payment.amount
        
        new_refund = Refund(
            payment_id=payment.id,
            user_id=booking.user_id,
            refund_amount=refund_amount,
            reason="Admin Cancelled Booking",
            status="processed"
        )
        db.session.add(new_refund)

    try:
        db.session.commit()
        flash(f"Booking #{booking.id} cancelled. Seats freed and ₹{refund_amount} refunded.", "success")
    except Exception as e:
        db.session.rollback()
        flash("A database error occurred while cancelling the booking.", "danger")

    return redirect(url_for("admin_bookings"))


@app.route("/admin/users/toggle-role/<int:user_id>")
@login_required
@roles_required("super_admin")  
def admin_toggle_user(user_id):

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot change your own role.", "warning")
        return redirect(url_for("admin_users"))

    if user.role == "super_admin":
        flash("Super Admin cannot be modified!", "danger")
        return redirect(url_for("admin_users"))

    if user.role == "user":
        user.role = "staff"
    elif user.role == "staff":
        user.role = "manager"
    elif user.role == "manager":
        user.role = "admin"
    elif user.role == "admin":
        user.role = "user"

    db.session.commit()

    flash("User role updated!", "success")
    return redirect(url_for("admin_users"))

@app.route("/admin/users")
@login_required
@roles_required("super_admin", "admin")
def admin_users():
    users = User.query.all()
    return render_template("admin/users.html", users=users)

@app.route("/admin/users/update-role/<int:user_id>", methods=["POST"])
@login_required
@roles_required("super_admin")  
def admin_update_user_role(user_id):

    user = User.query.get_or_404(user_id)

    new_role = request.form.get("role")

    if user.role == "super_admin":
        flash("Super Admin cannot be modified!", "danger")
        return redirect(url_for("admin_users"))

    if user.id == current_user.id:
        flash("You cannot change your own role!", "warning")
        return redirect(url_for("admin_users"))

    allowed_roles = ["user", "staff", "manager", "admin"]

    if new_role not in allowed_roles:
        flash("Invalid role selected!", "danger")
        return redirect(url_for("admin_users"))

    user.role = new_role

    user.is_admin = True if new_role in ["admin", "super_admin"] else False

    db.session.commit()

    flash("User role updated successfully!", "success")
    return redirect(url_for("admin_users"))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

@app.before_request
def clear_session_on_server_restart():
    if not app.config.get("_session_reset_done"):
        session.clear()
        app.config["_session_reset_done"] = True    
=======
from flask import Flask, render_template, redirect, url_for, session, request, flash, abort, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import date, datetime, timedelta
from collections import defaultdict
from functools import wraps
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func
import uuid
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bookmyshow_secret_key")

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", "harsh@1210"))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "bookmyshow")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


UPLOAD_FOLDER = "static/movie-poster"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not getattr(current_user, "is_admin", False):
            abort(403)  
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            if not current_user.is_authenticated:
                return login_manager.unauthorized()

            if current_user.role not in roles:
                flash("Access denied!", "danger")
                return redirect(url_for("index"))   

            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def create_seats_for_showtime(showtime_id):
    existing = Seat.query.filter_by(showtime_id=showtime_id).first()
    if existing:
        return  

    gold_rows = ["A", "B", "C", "D", "E", "F"]
    silver_rows = ["G", "H", "I"]

    seats = []
    for row in gold_rows:
        for num in range(1, 21):
            seats.append(Seat(
                showtime_id=showtime_id,
                seat_row=row,
                seat_number=num,
                seat_type="royal_gold",
                price=250,
                is_booked=False
            ))

    for row in silver_rows:
        for num in range(1, 21):
            seats.append(Seat(
                showtime_id=showtime_id,
                seat_row=row,
                seat_number=num,
                seat_type="royal_silver",
                price=220,
                is_booked=False
            ))

    db.session.bulk_save_objects(seats)
    db.session.commit()


# MODELS

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user") 
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Movie(db.Model):
    __tablename__ = "movies"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)
    language = db.Column(db.String(50))
    genres = db.Column(db.String(100))
    certificate = db.Column(db.String(10))
    rating = db.Column(db.Float)
    poster = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    featured_image = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Theatre(db.Model):
    __tablename__ = "theatres"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    is_imax = db.Column(db.Boolean, default=False)
    is_3d = db.Column(db.Boolean, default=False)
    is_dolby = db.Column(db.Boolean, default=False)
    is_4dx = db.Column(db.Boolean, default=False)

class Showtime(db.Model):
    __tablename__ = "showtimes"
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)
    theatre_id = db.Column(db.Integer, db.ForeignKey("theatres.id"), nullable=False)
    movie = db.relationship('Movie', backref='showtimes')
    theatre = db.relationship('Theatre', backref='showtimes')
    show_date = db.Column(db.Date, nullable=False)
    show_time = db.Column(db.Time, nullable=False)

class Seat(db.Model):
    __tablename__ = "seats"
    id = db.Column(db.Integer, primary_key=True)
    showtime_id = db.Column(db.Integer, db.ForeignKey("showtimes.id"), nullable=False)
    seat_row = db.Column(db.String(1))
    seat_number = db.Column(db.Integer)
    seat_type = db.Column(db.String(20))
    price = db.Column(db.Integer)
    is_booked = db.Column(db.Boolean, default=False)
    locked_until = db.Column(db.DateTime, nullable=True)

class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    showtime_id = db.Column(db.Integer, db.ForeignKey("showtimes.id"), nullable=False)
    total_amount = db.Column(db.Integer)
    booking_time = db.Column(db.DateTime, default=datetime.now)
    booking_seats = db.relationship("BookingSeat", backref="booking")
    showtime = db.relationship('Showtime', backref='bookings')
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.now)

class BookingSeat(db.Model):
    __tablename__ = "booking_seats"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey("seats.id"), nullable=False)
    seat = db.relationship("Seat")

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    refunds = db.relationship('Refund', backref='payment', lazy=True, cascade="all, delete-orphan")

class Refund(db.Model):
    __tablename__ = 'refunds' 
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    refund_amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    refund_reason = db.Column(db.String(255))
    gateway_refund_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default='pending') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SignupForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create Account")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")

@app.route("/")
def index():
    hero_movies = (
        Movie.query
        .filter(Movie.is_active == True, Movie.is_featured == True)
        .order_by(Movie.created_at.desc())
        .limit(3)
        .all()
    )

    all_movies = Movie.query.all()

    return render_template(
        "index.html",
        hero_movies=hero_movies,
        all_movies=all_movies
    )

@app.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template("movie.html", movie=movie)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists", "danger")
            return render_template("signup.html", form=form)

        user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("index"))

    return render_template("signup.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)

            if user.role == "admin":
                return redirect(url_for("admin_movies"))
            elif user.role == "manager":
                return redirect(url_for("admin_movies"))
            elif user.role == "staff":
                return redirect(url_for("admin_bookings"))
            else:
                return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/select-showtime/<int:movie_id>")
@login_required
def select_showtime(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    today = date.today()

    dates = [today + timedelta(days=i) for i in range(7)]

    date_str = request.args.get("date")
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    rows = (
        db.session.query(Showtime, Theatre)
        .join(Theatre, Showtime.theatre_id == Theatre.id)
        .filter(Showtime.movie_id == movie.id)
        .filter(Showtime.show_date == selected_date)
        .order_by(Theatre.id, Showtime.show_time)
        .all()
    )

    theatres_map = {}
    for showtime, theatre in rows:
        if theatre.id not in theatres_map:
            theatres_map[theatre.id] = {"theatre": theatre, "times": []}
        theatres_map[theatre.id]["times"].append(showtime)

    return render_template(
        "select_showtime.html",
        movie=movie,
        theatres_map=theatres_map,
        dates=dates,
        selected_date=selected_date,
        current_date=today
    )

@app.route("/go-to-seats", methods=["POST"])
@login_required
def go_to_seats():
    showtime_id = request.form.get("showtime_id")

    if not showtime_id:
        flash("Please select a showtime.", "warning")
        return redirect(request.referrer)

    return redirect(url_for("select_seats", showtime_id=showtime_id))


@app.route("/select-seats/<int:showtime_id>")
@login_required
def select_seats(showtime_id):
    showtime = Showtime.query.get_or_404(showtime_id)
    movie = Movie.query.get_or_404(showtime.movie_id)
    theatre = Theatre.query.get_or_404(showtime.theatre_id)

    create_seats_for_showtime(showtime_id)

    seats = (
        Seat.query
        .filter_by(showtime_id=showtime_id)
        .order_by(Seat.seat_type, Seat.seat_row, Seat.seat_number)
        .all()
    )

    grouped = defaultdict(lambda: defaultdict(list))

    for seat in seats:
        grouped[seat.seat_type][seat.seat_row].append(seat)

    return render_template(
        "select_seats.html",
        movie=movie,
        theatre=theatre,
        showtime=showtime,
        grouped=grouped
    )

@app.route("/select-seats-post", methods=["POST"])
@login_required
def select_seats_post():

    seat_ids = request.form.getlist("seat_ids")
    showtime_id = request.form.get("showtime_id")

    if not seat_ids:
        flash("No seats selected.", "danger")
        return redirect(url_for("select_seats", showtime_id=showtime_id))

    seats = Seat.query.filter(Seat.id.in_(seat_ids)).all()

    for seat in seats:

        if seat.is_booked:
            flash("Seat already booked!", "danger")
            return redirect(url_for("select_seats", showtime_id=showtime_id))

        if seat.locked_until and seat.locked_until > datetime.now():
            flash("Seat temporarily locked!", "warning")
            return redirect(url_for("select_seats", showtime_id=showtime_id))

        seat.locked_until = datetime.now() + timedelta(minutes=5)

    db.session.commit()

    session["selected_seats"] = seat_ids
    session["showtime_id"] = showtime_id

    return redirect(url_for("payment"))

@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
  
    seat_ids = session.get("selected_seats")
    showtime_id = session.get("showtime_id")

    if not seat_ids or not showtime_id:
        flash("Please select seats first.", "danger")
        return redirect(url_for("index"))

    seats = Seat.query.filter(Seat.id.in_(seat_ids)).all()
    showtime = Showtime.query.get_or_404(showtime_id)
    movie = Movie.query.get(showtime.movie_id)
    theatre = Theatre.query.get(showtime.theatre_id)

    total = sum(seat.price for seat in seats)
    fees = int(total * 0.08)
    grand_total = total + fees

    if request.method == "POST":
        
        payment_method = request.form.get("payment_method")
        
        if not payment_method:
            flash("You must select a payment method (UPI or Card) to continue.", "danger")
            return redirect(url_for("payment"))
            
        valid_methods = ["UPI", "Debit/Credit Card"]
        if payment_method not in valid_methods:
            flash("Invalid payment method selected.", "danger")
            return redirect(url_for("payment"))

        for seat in seats:
            if not seat.locked_until or seat.locked_until < datetime.now():
                flash("Seat lock expired! Please reselect.", "danger")
                return redirect(url_for("select_seats", showtime_id=showtime_id))

            if seat.is_booked:
                flash("Seat already booked!", "danger")
                return redirect(url_for("select_seats", showtime_id=showtime_id))

            seat.is_booked = True
            seat.locked_until = None

        booking = Booking(
            user_id=current_user.id,
            showtime_id=showtime_id,
            total_amount=grand_total,
            status="confirmed"
        )
        db.session.add(booking)
        
        db.session.flush() 

        # 6. Link the Seats to the Booking
        for seat in seats:
            db.session.add(BookingSeat(
                booking_id=booking.id,
                seat_id=seat.id
            ))

        transaction_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        
        payment_record = Payment(
            booking_id=booking.id,
            user_id=current_user.id,    
            amount=grand_total,          
            payment_method=payment_method, 
            transaction_id=transaction_id,
            status="completed"          
        )
        db.session.add(payment_record)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("A database error occurred during payment.", "danger")
            return redirect(url_for("index"))

        # 9. Clean up the session and move to the success page
        session.pop("selected_seats", None)
        session.pop("showtime_id", None)
        
        # Store the booking ID so the success ticket page can display it
        session["last_booking_id"] = booking.id

        return redirect(url_for("booking_success"))

    # If it's a GET request, just render the payment page
    return render_template(
        "payment.html",
        seats=seats,
        total=total,
        fees=fees,
        grand_total=grand_total,
        movie=movie,
        theatre=theatre,
        showtime=showtime
    )

@app.route("/booking_success")
@login_required
def booking_success():
    
    booking = (
        Booking.query
        .filter_by(user_id=current_user.id)
        .order_by(Booking.id.desc())
        .first()
    )

    if not booking:
        flash("No booking found.", "danger")
        return redirect(url_for("index"))

    showtime = Showtime.query.get(booking.showtime_id)
    movie = Movie.query.get(showtime.movie_id)
    theatre = Theatre.query.get(showtime.theatre_id)

    booking_seats = BookingSeat.query.filter_by(booking_id=booking.id).all()
    seats = Seat.query.filter(Seat.id.in_([bs.seat_id for bs in booking_seats])).all()

    return render_template(
        "booking_success.html",
        booking=booking,
        movie=movie,
        theatre=theatre,
        showtime=showtime,
        seats=seats
    )

@app.route("/account")
@login_required
def account():
   
    bookings = (
        db.session.query(Booking, Showtime, Movie, Theatre)
        .join(Showtime, Booking.showtime_id == Showtime.id)
        .join(Movie, Showtime.movie_id == Movie.id)
        .join(Theatre, Showtime.theatre_id == Theatre.id)
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.booking_time.desc())
        .all()
    )

    booking_list = []

    for booking, showtime, movie, theatre in bookings:
       
        seat_rows = (
            db.session.query(Seat)
            .join(BookingSeat, BookingSeat.seat_id == Seat.id)
            .filter(BookingSeat.booking_id == booking.id)
            .all()
        )

        seat_labels = [f"{s.seat_row}{s.seat_number}" for s in seat_rows]

        booking_list.append({
            "id": booking.id,
            "movie_title": movie.title,
            "theatre_name": theatre.name,
            "show_date": showtime.show_date.strftime("%d %b %Y"),
            "show_time": showtime.show_time.strftime("%I:%M %p"),
            "seats": ", ".join(seat_labels),
            "amount": booking.total_amount,
            "booking_time": booking.booking_time.strftime("%d %b %Y, %I:%M %p")
        })

    return render_template("account.html", bookings=booking_list)

# Admin Route

@app.route("/admin/reports")
@login_required
@admin_required
@roles_required("super_admin", "admin")
def admin_reports():

    total_revenue = db.session.query(func.sum(Booking.total_amount)).scalar() or 0
    total_bookings = Booking.query.count()
    total_users = User.query.count()

    today = datetime.utcnow().date()
    today_bookings = Booking.query.filter(func.date(Booking.booking_time) == today).count()
    today_revenue = db.session.query(func.sum(Booking.total_amount))\
        .filter(func.date(Booking.booking_time) == today).scalar() or 0

    last_7_days = []
    revenue_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        revenue = db.session.query(func.sum(Booking.total_amount))\
            .filter(func.date(Booking.booking_time) == day).scalar() or 0

        last_7_days.append(day.strftime("%d %b"))
        revenue_data.append(int(revenue))

    top_movies = db.session.query(
        Movie.title,
        func.count(Booking.id).label("total_bookings")
    ).join(Showtime, Showtime.movie_id == Movie.id)\
     .join(Booking, Booking.showtime_id == Showtime.id)\
     .group_by(Movie.title)\
     .order_by(func.count(Booking.id).desc())\
     .limit(5).all()

    return render_template(
        "admin/reports.html",
        total_revenue=total_revenue,
        total_bookings=total_bookings,
        total_users=total_users,
        today_bookings=today_bookings,
        today_revenue=today_revenue,
        labels=last_7_days,
        revenue_data=revenue_data,
        top_movies=top_movies
    )

@app.route("/admin/movies")
@login_required
@roles_required("super_admin", "admin")
def admin_movies():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template("admin/movies.html", movies=movies)

@app.route("/admin/movies/add", methods=["GET", "POST"])
@login_required
@admin_required
@roles_required("super_admin", "admin")
def admin_add_movie():
    if request.method == "POST":
        print("Files received:", request.files) 
        print("Form data:", request.form)
        
        poster_file = request.files.get("poster")
        poster_filename = None
        if poster_file and poster_file.filename:
            filename = secure_filename(poster_file.filename)
            poster_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            poster_file.save(poster_path)
            poster_filename = filename

        featured_file = request.files.get("featured_image")
        featured_filename = None
        if featured_file and featured_file.filename:
            f_filename = secure_filename(featured_file.filename)
            featured_path = os.path.join(app.config["UPLOAD_FOLDER"], f_filename)
            featured_file.save(featured_path)
            featured_filename = f_filename

        movie = Movie(
            title=request.form.get("title"),
            language=request.form.get("language"),
            genres=request.form.get("genres"),
            certificate=request.form.get("certificate"),
            duration=request.form.get("duration"),
            rating=request.form.get("rating"),
            poster=poster_filename,
            featured_image=featured_filename, 
            is_featured="is_featured" in request.form,
            is_active=True
        )

        db.session.add(movie)
        db.session.commit()

        flash("Movie added successfully!", "success")
        return redirect(url_for("admin_movies"))

    return render_template("admin/movie_form.html")

@app.route("/admin/movies/edit/<int:movie_id>", methods=["POST"])
@login_required
@admin_required
def admin_edit_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    try:
        movie.title = request.form.get("title")
        movie.language = request.form.get("language")
        movie.genres = request.form.get("genres")
        movie.certificate = request.form.get("certificate")
        movie.duration = request.form.get("duration", type=int) or 0
        movie.rating = request.form.get("rating", type=float) or 0.0
        movie.is_featured = "is_featured" in request.form

        file = request.files.get("poster")
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            unique_filename = f"movie_{movie.id}_{filename}"
            upload_path = os.path.join(current_app.root_path, 'static/movie-poster', unique_filename)
            file.save(upload_path)
            movie.poster = unique_filename

        db.session.commit()
        flash(f"Updated '{movie.title}' successfully!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for("admin_movies"))

@app.route("/admin/movies/delete/<int:movie_id>")
@login_required
@admin_required
def admin_delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if Showtime.query.filter_by(movie_id=movie_id).first():
        flash("Cannot delete movie: It has active showtimes.", "danger")
        return redirect(url_for("admin_movies"))

    db.session.delete(movie)
    db.session.commit()

    flash("Movie deleted successfully!", "success")
    return redirect(url_for("admin_movies"))

@app.route("/admin/theatres")
@login_required
@admin_required
def admin_theatres():
    theatres = Theatre.query.all()
    return render_template("admin/theatres.html", theatres=theatres)

@app.route("/admin/theatres/add", methods=["POST"])
@login_required
@admin_required
def admin_add_theatre():
    t = Theatre(
        name=request.form["name"],
        location=request.form["location"],
        is_imax="is_imax" in request.form,
        is_3d="is_3d" in request.form,
        is_4dx="is_4dx" in request.form,
        is_dolby="is_dolby" in request.form,
    )
    db.session.add(t)
    db.session.commit()
    flash("Theatre added!", "success")
    return redirect(url_for("admin_theatres"))

@app.route("/admin/theatres/edit/<int:theatre_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_theatre(theatre_id):
    theatre = Theatre.query.get_or_404(theatre_id)

    if request.method == "POST":
        theatre.name = request.form.get("name")
        theatre.location = request.form.get("location")

        theatre.is_imax = "is_imax" in request.form
        theatre.is_3d = "is_3d" in request.form
        theatre.is_4dx = "is_4dx" in request.form
        theatre.is_dolby = "is_dolby" in request.form

        db.session.commit()
        flash("Theatre updated successfully!", "success")
        return redirect(url_for("admin_theatres"))

    return render_template("admin/edit_theatre.html", theatre=theatre)

@app.route("/admin/theatres/delete/<int:theatre_id>")
@login_required
@admin_required
def admin_delete_theatre(theatre_id):
    theatre = Theatre.query.get_or_404(theatre_id)

    if Showtime.query.filter_by(theatre_id=theatre_id).first():
        flash("Cannot delete theatre with showtimes!", "danger")
        return redirect(url_for("admin_theatres"))

    db.session.delete(theatre)
    db.session.commit()

    flash("Theatre deleted successfully!", "success")
    return redirect(url_for("admin_theatres"))

@app.route('/admin/booking/<int:booking_id>/cancel', methods=['GET', 'POST'])
@login_required
def admin_delete_bookings(booking_id):

    booking = Booking.query.get_or_404(booking_id)
    
    if booking.status == 'cancelled':
        flash('This booking is already cancelled.', 'warning')
        return redirect(url_for('admin_bookings'))

    booking.status = 'cancelled'
    
    for booked_seat in booking.booking_seats:
        booked_seat.seat.is_booked = False
        
    payment = Payment.query.filter_by(booking_id=booking.id).first()
    
    if payment and payment.status == 'completed':
        payment.status = 'refunded'
        
        new_refund = Refund(
            payment_id=payment.id,
            user_id=booking.user_id,
            refund_amount=payment.amount, # Or subtract cancellation fees here
            reason="Admin Cancelled Booking",
            status="processed"
        )
        db.session.add(new_refund)

    db.session.commit()
    
    flash(f'Booking #{booking.id} cancelled and ₹{payment.amount} refunded.', 'success')
    return redirect(url_for('admin_bookings'))

@app.route("/admin/showtimes")
@login_required
@admin_required
def admin_showtimes():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Showtime.query.join(Movie).join(Theatre)

    if search:
        query = query.filter(
            db.or_(
                Movie.title.ilike(f"%{search}%"),
                Theatre.name.ilike(f"%{search}%")
            )
        )
    showtimes_paginated = query.order_by(
        Showtime.show_date.desc(), 
        Showtime.show_time.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    movies = Movie.query.all()
    theatres = Theatre.query.all()
    return render_template(
        "admin/showtimes.html", 
        showtimes=showtimes_paginated, 
        movies=movies, 
        theatres=theatres,
        search=search
    )

@app.route("/admin/showtimes/add", methods=["POST"])
@login_required
@admin_required
def admin_add_showtime():

    movie_id = request.form.get("movie_id")
    theatre_id = request.form.get("theatre_id")
    start_date = request.form.get("start_date")
    days = int(request.form.get("days", 1))

    show_times = request.form.getlist("show_times")

    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    for i in range(days):

        current_date = start_date + timedelta(days=i)

        for t in show_times:

            if not t:
                continue

            show_time = datetime.strptime(t, "%H:%M").time()

            st = Showtime(
                movie_id=movie_id,
                theatre_id=theatre_id,
                show_date=current_date,
                show_time=show_time
            )

            db.session.add(st)
            db.session.flush()

            create_seats_for_showtime(st.id)

    db.session.commit()

    flash("Showtimes generated successfully!", "success")

    return redirect(url_for("admin_showtimes"))

@app.route("/admin/showtimes/edit/<int:showtime_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_showtime(showtime_id):
    showtime = Showtime.query.get_or_404(showtime_id)
    movies = Movie.query.all()
    theatres = Theatre.query.all()

    if request.method == "POST":
        movie_id = request.form.get("movie_id")
        theatre_id = request.form.get("theatre_id")
        show_date = request.form.get("show_date")
        show_time = request.form.get("show_time")

        if not all([movie_id, theatre_id, show_date, show_time]):
            flash("All fields are required.", "danger")
            return redirect(url_for('admin_edit_showtime', showtime_id=showtime.id))

        showtime.movie_id = int(movie_id)
        showtime.theatre_id = int(theatre_id)
        showtime.show_date = datetime.strptime(show_date, "%Y-%m-%d").date()
        
        try:
            showtime.show_time = datetime.strptime(show_time, "%H:%M").time()
        except ValueError:
            
            showtime.show_time = datetime.strptime(show_time, "%H:%M:%S").time()

        db.session.commit()
        flash("Showtime updated successfully!", "success")
        return redirect(url_for("admin_showtimes"))

    return render_template("admin/edit_showtime.html", showtime=showtime, movies=movies, theatres=theatres)

@app.route("/admin/showtimes/delete/<int:showtime_id>")
@login_required
@admin_required
def admin_delete_showtime(showtime_id):
    showtime = Showtime.query.get_or_404(showtime_id)

    existing_bookings = Booking.query.filter_by(showtime_id=showtime_id).first()
    
    if existing_bookings:
        flash("Cannot delete this showtime: Tickets have already been booked!", "danger")
        return redirect(url_for("admin_showtimes"))


    Seat.query.filter_by(showtime_id=showtime_id).delete()

    db.session.delete(showtime)
    db.session.commit()

    flash("Showtime deleted successfully.", "success")
    return redirect(url_for("admin_showtimes"))

@app.route("/admin/showtimes/clear", methods=["POST"])
@login_required
@admin_required
def admin_clear_showtimes():

    BookingSeat.query.delete()
    Payment.query.delete()
    Booking.query.delete()
    Seat.query.delete()
    Showtime.query.delete()

    db.session.commit()

    flash("All showtimes + bookings cleared!", "success")
    return redirect(url_for("admin_showtimes"))

@app.route("/admin/bookings")
@login_required
@roles_required("super_admin", "admin", "staff")
def admin_bookings():
    # Fetch all bookings, newest first
    bookings = Booking.query.order_by(Booking.booking_time.desc()).all()

    booking_list = []

    for booking in bookings:
        showtime = Showtime.query.get(booking.showtime_id)
        movie = Movie.query.get(showtime.movie_id)
        theatre = Theatre.query.get(showtime.theatre_id)
        user = User.query.get(booking.user_id)

        booking_seats = BookingSeat.query.filter_by(booking_id=booking.id).all()

        seat_rows = Seat.query.filter(
            Seat.id.in_([bs.seat_id for bs in booking_seats])
        ).all()

        seat_labels = [f"{s.seat_row}{s.seat_number}" for s in seat_rows]

        booking_list.append({
            "id": booking.id,
            "user_id": booking.user_id,
            "movie": movie,
            "theatre": theatre,
            "showtime": showtime,
            "seats": seat_labels,
            "total_amount": booking.total_amount,
            "booking_time": booking.booking_time,
            "status": booking.status,

        })

    return render_template("admin/bookings.html", bookings=booking_list)

@app.route("/admin/bookings/delete/<int:booking_id>")
@login_required
@roles_required("admin", "super_admin")
def admin_delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.status == "cancelled":
        flash("This booking is already cancelled.", "warning")
        return redirect(url_for("admin_bookings"))

    booking_seats = BookingSeat.query.filter_by(booking_id=booking.id).all()
    for bs in booking_seats:
        seat = Seat.query.get(bs.seat_id)
        if seat:
            seat.is_booked = False
            seat.locked_until = None 

    booking.status = "cancelled"

    payment = Payment.query.filter_by(booking_id=booking.id).first()
    refund_amount = 0

    if payment and payment.status == "completed":
        payment.status = "refunded"
        refund_amount = payment.amount
        
        new_refund = Refund(
            payment_id=payment.id,
            user_id=booking.user_id,
            refund_amount=refund_amount,
            reason="Admin Cancelled Booking",
            status="processed"
        )
        db.session.add(new_refund)

    try:
        db.session.commit()
        flash(f"Booking #{booking.id} cancelled. Seats freed and ₹{refund_amount} refunded.", "success")
    except Exception as e:
        db.session.rollback()
        flash("A database error occurred while cancelling the booking.", "danger")

    return redirect(url_for("admin_bookings"))


@app.route("/admin/users/toggle-role/<int:user_id>")
@login_required
@roles_required("super_admin")  
def admin_toggle_user(user_id):

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot change your own role.", "warning")
        return redirect(url_for("admin_users"))

    if user.role == "super_admin":
        flash("Super Admin cannot be modified!", "danger")
        return redirect(url_for("admin_users"))

    if user.role == "user":
        user.role = "staff"
    elif user.role == "staff":
        user.role = "manager"
    elif user.role == "manager":
        user.role = "admin"
    elif user.role == "admin":
        user.role = "user"

    db.session.commit()

    flash("User role updated!", "success")
    return redirect(url_for("admin_users"))

@app.route("/admin/users")
@login_required
@roles_required("super_admin", "admin")
def admin_users():
    users = User.query.all()
    return render_template("admin/users.html", users=users)

@app.route("/admin/users/update-role/<int:user_id>", methods=["POST"])
@login_required
@roles_required("super_admin")  
def admin_update_user_role(user_id):

    user = User.query.get_or_404(user_id)

    new_role = request.form.get("role")

    if user.role == "super_admin":
        flash("Super Admin cannot be modified!", "danger")
        return redirect(url_for("admin_users"))

    if user.id == current_user.id:
        flash("You cannot change your own role!", "warning")
        return redirect(url_for("admin_users"))

    allowed_roles = ["user", "staff", "manager", "admin"]

    if new_role not in allowed_roles:
        flash("Invalid role selected!", "danger")
        return redirect(url_for("admin_users"))

    user.role = new_role

    user.is_admin = True if new_role in ["admin", "super_admin"] else False

    db.session.commit()

    flash("User role updated successfully!", "success")
    return redirect(url_for("admin_users"))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
>>>>>>> 3117341 (Fixed DB config)
