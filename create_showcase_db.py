import random
import sys
from datetime import date, timedelta

import mysql.connector as mcon

HOST = "localhost"
USER = "Regyzide"
PASSWORD = "Ab1311ab#"

DB_NAME = "study_planner_showcase"
STUDENT = "User_1"
STUDENT_PASSWORD = "showcase123"

SUBJECTS = ["Physics", "Chemistry", "Maths", "Computer Science", "English"]

TODAY = date.today()


def ago(days):
    return TODAY - timedelta(days=days)

ROUNDS = [
    ("Unit Test 1", 150, 50,  (28, 31, 33, 41, 38)),
    ("Mid Term",    115, 100, (58, 64, 70, 85, 79)),
    ("Unit Test 2",  80, 50,  (31, 34, 37, 44, 39)),
    ("Pre-Board 1",  45, 100, (63, 69, 74, 89, 81)),
    ("Pre-Board 2",  12, 100, (66, 72, 79, 91, 84)),
]
EXTRA_TESTS = [
    ("Maths Quiz 4",     "Maths",            28, 14, 20),
    ("Physics Practical", "Physics",         20, 21, 30),
    ("CS Lab Test",      "Computer Science",  6, 35, 50),
]

TESTS = []
for name, days_ago, maximum, marks in ROUNDS:
    for offset, (subject, scored) in enumerate(zip(SUBJECTS, marks)):
        TESTS.append((name, subject, ago(days_ago - offset), scored, maximum))
for name, subject, days_ago, scored, maximum in EXTRA_TESTS:
    TESTS.append((name, subject, ago(days_ago), scored, maximum))

SCHEDULES = [
    ("Physics",          20, "01.00.00", "Electrostatics numericals",              [3700]),
    ("Physics",           9, "00.45.00", "Ray optics: lenses and mirrors",         [2800]),
    ("Chemistry",        14, "01.30.00", "Organic reaction mechanisms",            [2700, 2900]),
    ("Chemistry",         5, "00.30.00", "Revise the mole concept",                [1900]),
    ("Maths",            16, "01.00.00", "Integration practice set",              [3700]),
    ("Maths",            10, "02.00.00", "Calculus problem set from the textbook", [4300, 3300]),
    ("Maths",             3, "00.30.00", "Matrices: determinants",                 [1800, 1900]),
    ("Maths",             3, "00.30.00", "Matrices: inverse and rank",             []),
    ("Computer Science", 18, "01.00.00", "Python: classes and inheritance",        [3700]),
    ("Computer Science",  7, "00.45.00", "SQL joins and group by",                 [2800]),
    ("English",          11, "00.40.00", "Essay writing: argumentative essay",     [2500]),
    ("English",           2, "00.30.00", "Poetry analysis: figures of speech",     [1900]),
    ("English",           0, "00.30.00", "Reading comprehension passages",         [1900]),
    ("Physics",           4, "01.00.00", "Thermodynamics (only half finished)",    [1500]),
    ("Chemistry",         6, "00.45.00", "Chemical bonding (missed)",              []),
    ("Maths",             0, "01.00.00", "Revise vectors before the mock test",    [2100]),
    ("Maths",            -1, "01.30.00", "Full-length mock paper",                 []),
    ("Physics",          -2, "01.00.00", "Waves and oscillations",                 []),
    ("Computer Science", -2, "01.00.00", "Data structures: stacks and queues",     []),
    ("Chemistry",        -3, "00.45.00", "Periodic table trends",                  []),
    ("English",          -4, "00.30.00", "Grammar and tenses practice",            []),
    ("Chemistry",        -5, "02.00.00", "Pre-board revision: physical chemistry", []),
]

HABITS = {
    "Physics":          (0.62, 1500, 5400),
    "Chemistry":        (0.55, 1200, 4800),
    "Maths":            (0.65, 1500, 5400),
    "Computer Science": (0.35,  900, 3600),
    "English":          (0.30,  900, 3000),
}
DAYS_OF_HISTORY = 160

DDL = [
    "Create table SST(TestID int(5) primary key, Username varchar(30) not null, TestName varchar(30) not null, "
    "Subject varchar(30) not null, TestDate date, UserMarks int(3) not null, MaxMarks int(3) not null)",

    "Create table Sessions(SessionId int(6) primary key, Username varchar(30) not null, Subject varchar(30) not null, "
    "SessionDate date not null, Status int(1), SessionTime varchar(10))",

    "Create table Schedules(ScheduleId int(6) primary key, Username varchar(30) not null, Subject varchar(30) not null, "
    "ScheduledTime varchar(15) not null, ScheduledDate date not null, Remarks varchar(500))",

    "Create table Accounts(Username varchar(30) primary key, Password varchar(30) not null)",

    "Create table Subjects(Username varchar(30) not null, SubjectName varchar(30) not null, "
    "primary key (Username, SubjectName))",
]


def build_sessions():
    rows = []
    reserved = set()
    for subject, days_ago, _time, _remarks, studied in SCHEDULES:
        reserved.add((subject, days_ago))
        for number, seconds in enumerate(studied):
            finished = number == len(studied) - 1
            rows.append((subject, ago(days_ago), 1 if finished else 0, seconds))
    chance = random.Random(2024)
    for days_ago in range(1, DAYS_OF_HISTORY + 1):
        for subject in SUBJECTS:
            likelihood, shortest, longest = HABITS[subject]
            if (subject, days_ago) in reserved or chance.random() > likelihood:
                continue
            rows.append((subject, ago(days_ago), 0, chance.randrange(shortest, longest, 60)))
    rows.sort(key=lambda row: row[1])
    return rows


def main():
    if "<your" in USER or "<your" in PASSWORD:
        sys.exit("Open this file and fill in USER and PASSWORD (your MySQL login) at the top first.")
    try:
        conn = mcon.connect(host=HOST, user=USER, password=PASSWORD)
    except mcon.Error as problem:
        sys.exit(f"Could not connect to MySQL: {problem}")
    cur = conn.cursor()
    try:
        cur.execute(f"Drop database if exists `{DB_NAME}`")
        cur.execute(f"Create database `{DB_NAME}`")
        cur.execute(f"Use `{DB_NAME}`")
        for statement in DDL:
            cur.execute(statement)

        cur.execute("Insert into Accounts values (%s, %s)", (STUDENT, STUDENT_PASSWORD))
        cur.executemany("Insert into Subjects values (%s, %s)", [(STUDENT, subject) for subject in SUBJECTS])

        cur.executemany("Insert into SST values (%s, %s, %s, %s, %s, %s, %s)",
                        [(number, STUDENT, name, subject, day, scored, maximum)
                         for number, (name, subject, day, scored, maximum) in enumerate(sorted(TESTS, key=lambda t: t[2]), 1)])

        sessions = build_sessions()
        cur.executemany("Insert into Sessions values (%s, %s, %s, %s, %s, %s)",
                        [(number, STUDENT, subject, day, status, f"{seconds:.2f}")
                         for number, (subject, day, status, seconds) in enumerate(sessions, 1)])

        ordered = sorted(SCHEDULES, key=lambda s: (-s[1], s[0]))
        cur.executemany("Insert into Schedules values (%s, %s, %s, %s, %s, %s)",
                        [(number, STUDENT, subject, scheduled, ago(days_ago), remarks)
                         for number, (subject, days_ago, scheduled, remarks, _studied) in enumerate(ordered, 1)])
        conn.commit()
    except mcon.Error as problem:
        conn.rollback()
        sys.exit(f"Could not build the showcase database: {problem}")
    finally:
        conn.close()

    print(f"Showcase database created: {DB_NAME}")
    print(f"  {len(SUBJECTS)} subjects, {len(TESTS)} tests, {len(sessions)} study sessions, {len(SCHEDULES)} schedules")
    print(f"  Log in as '{STUDENT}' with password '{STUDENT_PASSWORD}'")
    print(f"  In Entries/mysqlData.txt the second line must be:  {USER};<your password>;{DB_NAME}")


if __name__ == "__main__":
    main()
