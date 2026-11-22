# 🎬 CineSeat – Movie Ticket Booking System

CineSeat is a web-based movie ticket booking application developed using **Python, Flask, and MySQL**. It allows users to browse movies, select showtimes, choose seats, and manage their bookings through an interactive booking system.

The project demonstrates full-stack web development, database management, user authentication, and payment workflow integration.

## ✨ Features

- **User Authentication** – User registration, login, and logout.
- **Movie Booking** – Browse movies and select available showtimes.
- **Interactive Seat Selection** – Choose seats based on availability.
- **Seat Categories** – Gold and Silver seating options with different prices.
- **Dynamic Pricing** – Calculate ticket costs and booking fees.
- **Payment Workflow** – Select UPI or Debit/Credit Card as a payment method.
- **Booking Confirmation** – Display booking details after a successful booking.
- **Booking Management** – View booking information and payment details.
- **Refund Status** – Display refund status where supported.
- **Database Integration** – Store user, movie, seat, booking, and payment information.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| MySQL | Relational database |
| SQLAlchemy | Database ORM |
| HTML5 | Page structure |
| CSS3 | Styling |
| Bootstrap | Responsive UI |
| JavaScript | Frontend interactions |
| Jinja2 | Dynamic HTML templates |
| Git & GitHub | Version control |

## 📂 Project Structure

```text
CineSeat/
├── app.py
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── requirements.txt
├── .gitignore
└── README.md
```

*Note: Adjust the structure above to match your actual project files and folders.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/harsht1210/CineSeat-Flask.git
```

### 2. Navigate to the project directory

```bash
cd CineSeat-Flask
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```
### 5. Configure the database

- Create a MySQL database for CineSeat.
- Configure your database connection using your project's configuration settings or environment variables.
- Create the required tables using your existing schema or migration setup.
- Keep database credentials in a local `.env` file and never commit them to GitHub.

Example environment variables:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=mysql+pymysql://username:password@localhost/database_name
```

Update the variable names to match those used in your application.

### 6. Run the application

If your Flask entry point is `app.py`, run:

```bash
flask --app app run --debug
```

Open your browser at:

http://127.0.0.1:5000/

## 🎟️ How It Works

1. Register or log in to your account.
2. Browse available movies.
3. Select a movie and showtime.
4. Choose your preferred seats from the available Gold and Silver categories.
5. Review the ticket price and applicable booking fees.
6. Select a payment method.
7. Complete the booking workflow and view the confirmation details.

*Actual steps depend on the features and payment integration implemented in your project.*

## 💡 Key Learning Outcomes

- Building a web application using Flask.
- Implementing authentication and session management.
- Designing relational database models with SQLAlchemy.
- Handling seat availability and booking logic.
- Calculating ticket prices and booking fees.
- Managing payment records and booking status.
- Organizing backend routes, models, and templates.
- Using Git and GitHub for source control.

## 🚀 Future Enhancements

- Integrate a live payment gateway.
- Add movie search and filtering.
- Implement automated seat locking during checkout.
- Add email booking confirmations.
- Improve admin dashboards and reporting.
- Deploy the application to a cloud platform.

## 👨‍💻 Author

**Harsh Tembekar**

- GitHub: [harsht1210](https://github.com/harsht1210)
- Portfolio: [harshtportfolio.netlify.app](https://harshportfolio123.netlify.app/)

---

⭐ If you find this project interesting, consider giving the repository a star!
