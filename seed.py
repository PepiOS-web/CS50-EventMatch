import sqlite3

def main():
    conn = sqlite3.connect("eventmatch.db")
    cur = conn.cursor()

    # --- Charlas de ejemplo ---
    talks = [
        ("Opening Keynote: The Future of Manufacturing", "Kickoff session for the event", "Keynote", "10:00", "10:45", "Main Stage"),
        ("AI for Quality Control", "Using computer vision to detect defects", "AI & Data", "11:00", "11:45", "Room A"),
        ("Robotics in Assembly Lines", "Collaborative robots in factories", "Automation", "12:00", "12:45", "Room B"),
        ("Sustainability in Production", "Reducing waste and energy consumption", "Sustainability", "15:00", "15:45", "Room C"),
        ("Cybersecurity for OT", "How to protect industrial networks", "Cybersecurity", "16:00", "16:45", "Room B"),
        ("Digital Twins 101", "Virtual replicas of your factory", "AI & Data", "17:00", "17:45", "Room A"),
    ]

    # --- Expositores de ejemplo ---
    exhibitors = [
        ("Siemens", "Automation, PLCs and industrial control", "Automation", "A10"),
        ("ABB", "Robotics and industrial automation", "Robotics", "B20"),
        ("Bosch Rexroth", "Motion control and hydraulics", "Components", "C15"),
        ("AWS for Industry", "Cloud, data lakes and analytics", "Cloud & Data", "D05"),
        ("Schneider Electric", "Energy management and IoT", "Energy & IoT", "E12"),
        ("KUKA Robotics", "Industrial robots and cobots", "Robotics", "F03"),
    ]

    # Insertar charlas
    cur.executemany("""
        INSERT INTO talks (title, description, track, start_time, end_time, location)
        VALUES (?, ?, ?, ?, ?, ?)
    """, talks)

    # Insertar expositores
    cur.executemany("""
        INSERT INTO exhibitors (name, description, sector, stand)
        VALUES (?, ?, ?, ?)
    """, exhibitors)

    conn.commit()
    conn.close()
    print("Charlas y expositores insertados correctamente.")

if __name__ == "__main__":
    main()
