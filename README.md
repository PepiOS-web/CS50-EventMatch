# EventMatch
#### Video Demo:  <https://www.youtube.com/watch?v=IBqSJkNYI04>
#### Description:

Smart Agenda & Recommendation System for Trade Shows — CS50 Final Project

EventMatch is a web application designed to help attendees navigate trade shows efficiently.
Users can explore events, discover talks and exhibitors, receive personalized AI-like recommendations, and build a smart, conflict-free agenda.
Administrators can manage events, talks, exhibitors, and oversee platform data.

This project was built as my CS50 Final Project, combining Flask, SQLite, Bootstrap, and interactive web technologies.

User Features
Register / Login / Logout system with session management
Personal profile page with username/email editing and password change
Browse events and see all talks & exhibitors belonging to each
Smart recommendations based on:
	User agenda (tracks and sectors)
	User preferences
	Schedule conflict avoidance

Add talks or exhibitors to a personal agenda
Agenda calendar view (structured by time)
Printable/PDF agenda summary
Clean and responsive interface with Bootstrap 5 and AOS animations

Admins have access to a full dashboard:
Add / edit / delete:
	Events
	Talks
	Exhibitors
Assign talks and exhibitors to specific events
View platform statistics (total users, total talks, etc.)

Recommendation Logic
The recommendation engine uses:
Tracks of talks the user has saved
Sectors of exhibitors already saved
Time conflict detection
Scoring system to rank recommended sessions
This ensures suggestions feel personalized and relevant.

Database Structure
EventMatch uses SQLite with the following core tables:

	users
	events
	talks
	exhibitors
	user_talks
	user_exhibitors

Technologies Used
Python + Flask
SQLite
HTML, CSS, Bootstrap 5
Jinja2 Templates
JavaScript + Chart.js
AOS (Animate On Scroll)
html2pdf.js for exporting agenda summaries

Installation & Setup

Clone the repository
git clone https://github.com/yourusername/eventmatch.git
cd eventmatch

Create a virtual environment
   python -m venv venv
   source venv/bin/activate     # macOS / Linux
   venv\Scripts\activate        # Windows

3. pip install -r requirements.txt

File Structure

/eventmatch
│
├── app.py
├── eventmatch.db
├── requirements.txt
│
├── /templates
│   ├── layout.html
│   ├── index.html
│   ├── profile.html
│   ├── agenda.html
│   ├── agenda_calendar.html
│   ├── recommendations.html
│   ├── events.html
│   ├── event_detail.html
│   ├── admin_dashboard.html
│   ├── admin_charlas.html
│   ├── admin_expositores.html
│
└── /static
    ├── styles.css
    └── (icons, scripts, images)


