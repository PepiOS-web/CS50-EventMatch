import sqlite3

conn = sqlite3.connect("eventmatch.db")
cur = conn.cursor()

print("⏳ Inserting events data...")

talks = [
    ("Future of Manufacturing", "A deep dive into automation and robotics shaping tomorrow’s factories.", "Automation", "10:00", "10:45", "Main Stage", 1),
    ("AI in Industrial Processes", "How AI models are reducing downtime and improving workflows.", "AI & Data", "11:00", "11:45", "Room 2", 1),
    ("Sustainable Materials Innovation", "Exploring the future of composites and circularity.", "Materials", "12:00", "12:45", "Room 3", 2),
    ("Human-Robot Collaboration", "Cobots and the evolving human-machine interface.", "Robotics", "10:00", "10:30", "Tech Theatre", 2),
    ("Cybersecurity for Smart Factories", "Protecting connected infrastructures from attacks.", "IT Security", "15:00", "15:45", "Room 1", 3),
    ("Predictive Maintenance Strategies", "Sensors, data models and forecasting applied to industry.", "Maintenance", "12:30", "13:00", "Stage B", 3),
    ("Circular Economy in Manufacturing", "Designing products with end-of-life reuse in mind.", "Sustainability", "11:00", "11:30", "Room Green", 1),
    ("Digital Twins Explained", "Virtual replicas to optimize industrial assets and operations.", "Industry 4.0", "14:00", "14:45", "Innovation Hub", 2),
    ("High-Performance Composites", "Applications in aerospace, mobility and competitive sports.", "Materials", "16:00", "16:45", "Composites Zone", 3),
    ("Logistics Automation Trends", "How automation drives modern supply chains.", "Logistics", "10:30", "11:15", "Supply Stage", 1),
]

exhibitors = [
    ("RoboTech Solutions", "Advanced robotics for industrial automation.", "Robotics", "A12", 1),
    ("DataForge AI", "AI-driven analytics for predictive maintenance.", "AI & Data", "C03", 1),
    ("GreenComposites", "Sustainable composite materials.", "Materials", "B18", 2),
    ("SecureFactory Labs", "Industrial cybersecurity systems.", "IT Security", "D07", 3),
    ("FlexiCobots", "Collaborative robots for SMEs.", "Robotics", "A21", 2),
    ("NanoMaterials+", "High-resilience nano-enhanced resins.", "Materials", "C10", 3),
    ("LogiChain Systems", "Automation solutions for warehousing.", "Logistics", "F05", 1),
    ("VisionAI Sensors", "Smart cameras for industrial quality control.", "Sensors", "H14", 2),
    ("EcoCycle Tech", "Recycling technologies for circular factories.", "Sustainability", "E09", 3),
    ("AeroCarbon", "Lightweight composites for aerospace.", "Materials", "B02", 2),
]

# Insert talks
cur.executemany("""
INSERT INTO talks (title, description, track, start_time, end_time, location, event_id)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", talks)

# Insert exhibitors
cur.executemany("""
INSERT INTO exhibitors (name, description, sector, stand, event_id)
VALUES (?, ?, ?, ?, ?)
""", exhibitors)

conn.commit()
conn.close()

print("✔ Done! Data successfully inserted.")
