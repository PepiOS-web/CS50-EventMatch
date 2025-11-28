# EventMatch AI  
### Smart Agenda & Recommendation Engine for Trade Shows  
*CS50 Final Project — Harvard University*

EventMatch AI is a web application built with Flask that helps visitors plan their trade show participation in an intelligent way.  
Users can browse events, explore talks and exhibitors, build a personalized agenda, and receive AI-inspired recommendations based on their interests and schedule.

Admins can manage events, talks, exhibitors, and monitor the overall activity of the system through a dedicated dashboard.

---

## Features

### User Features
- Register and log in with secure password hashing  
- View and update profile (including password changes)  
- Browse all events  
- Explore the program of each event (talks + exhibitors)  
- Add talks and exhibitors to a personal agenda  
- Auto-prevent overlapping talk schedules  
- Export a printable agenda summary  
- Visualize agenda data with interactive charts  
- Calendar-style view of scheduled talks  
- Receive personalized recommendations based on:
  - Saved tracks
  - Saved exhibitors’ sectors
  - Time conflicts

### Admin Features
- Create, edit, and delete:
  - Events  
  - Talks (assigned to events)  
  - Exhibitors (assigned to events)  
- See summary stats (users, talks, exhibitors)  
- Full admin-only access with session-based permissions  

---

## Tech Stack

**Backend:** Flask (Python)  
**Database:** SQLite  
**Frontend:**  
- Bootstrap 5  
- AOS.js (scroll animations)  
- Chart.js (graphics in agenda)  
- FullCalendar-style layout (custom CSS)  
**Authentication:** Werkzeug hashed passwords  
**Session Management:** flask-session (filesystem mode)

---

## Database Schema

### **users**
| id | username | email | hash | is_admin |
|----|----------|-------|------|----------|

### **events**
| id | name | location | start_date | end_date | description |

### **talks**
| id | title | description | track | start_time | end_time | location | event_id |

### **exhibitors**
| id | name | description | sector | stand | event_id |

### **user_talks**
| id | user_id | talk_id |

### **user_exhibitors**
| id | user_id | exhibitor_id |

---

## How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/PepiOS-web/eventmatch-ai.git
cd eventmatch-ai

eventmatch-ai/
│
├── app.py                    # Main Flask application
├── eventmatch.db             # SQLite database
├── requirements.txt
├── schema.sql                # Database schema
│
├── static/
│   ├── styles.css            # Global CSS
│   └── icons/                # (optional)
│
├── templates/
│   ├── layout.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── agenda.html
│   ├── agenda_calendar.html
│   ├── recommendations.html
│   ├── events.html
│   ├── event_detail.html
│   ├── admin_dashboard.html
│   ├── admin_charlas.html
│   └── admin_expositores.html
│
└── README.md

Developed by Martin Garcia Suarez
Harvard CS50 — Final Project

