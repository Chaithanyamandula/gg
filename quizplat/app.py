import mysql.connector
import random
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for, session
from mysql.connector import Error as MySQL_Error # Import specific error type

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Change this to a strong, random key

# --- MySQL Database Configuration ---
DB_CONFIG = {
    'host': 'localhost', # Your MySQL host (usually localhost)
    'user': 'root',      # Your MySQL username
    'password': 'tiger', # !! IMPORTANT: Replace with your actual MySQL root/user password
    'database': 'quiz_db', # The database name you created in MySQL Workbench
    'auth_plugin': 'mysql_native_password'  # Add this line
    # 'port': 3306         # Default MySQL port
}

# --- Database Functions ---
def get_db():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # MySQL connector does not have row_factory like sqlite3.Row by default.
        # We will fetch results as dictionaries manually or iterate through tuples.
        # For simplicity, we'll iterate through tuples; if you need dicts, you'll need
        # to process cursor.fetchall() into a list of dicts.
    except MySQL_Error as e:
        print(f"Error connecting to MySQL database: {e}")
        # In a real application, you'd handle this more gracefully,
        # e.g., show an error page, log the error.
        return None
    return conn

def init_db():
    # Connect without specifying database first to create it if it doesn't exist
    temp_config = DB_CONFIG.copy()
    db_name = temp_config.pop('database') # Temporarily remove database name
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.close()
        conn.close() # Close the connection used to create the database

        # Now connect to the specific database and create tables
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contestants (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    contestant_id INT,
                    language VARCHAR(50) NOT NULL,
                    score INT NOT NULL,
                    total_questions INT NOT NULL,
                    FOREIGN KEY (contestant_id) REFERENCES contestants(id)
                )
            ''')
            conn.commit()
            print("MySQL tables checked/created successfully.")
        else:
            print("Failed to get database connection for table creation.")
    except MySQL_Error as e:
        print(f"Error during MySQL database initialization: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Call this once to initialize the database
init_db()

# --- Quiz Questions Data (remains the same) ---
# Structure: {'language': [{'question': '...', 'options': [], 'answer': '...'}, ...]}
QUIZ_QUESTIONS = {
    'C': [
        {'question': 'What is the entry point of a C program?', 'options': ['start()', 'main()', 'run()', 'begin()'], 'answer': 'main()'},
        {'question': 'Which header file is used for input/output operations in C?', 'options': ['stdio.h', 'stdlib.h', 'math.h', 'string.h'], 'answer': 'stdio.h'},
        {'question': 'What is the size of an int in C (typically)?', 'options': ['1 byte', '2 bytes', '4 bytes', '8 bytes'], 'answer': '4 bytes'},
        {'question': 'Which of the following is a logical operator in C?', 'options': ['+', '*', '&&', '/'], 'answer': '&&'},
        {'question': 'What is a pointer in C?', 'options': ['A variable that stores an integer', 'A variable that stores a memory address', 'A function', 'A data type'], 'answer': 'A variable that stores a memory address'},
        {'question': 'How do you declare a constant in C?', 'options': ['const int x = 10;', '#define X 10', 'both a and b', 'None of the above'], 'answer': 'both a and b'},
        {'question': 'Which function is used to allocate dynamic memory in C?', 'options': ['malloc()', 'calloc()', 'realloc()', 'all of the above'], 'answer': 'all of the above'},
        {'question': 'What is the purpose of the `break` statement?', 'options': ['To exit a loop or switch statement', 'To skip an iteration', 'To continue to the next iteration', 'To define a new function'], 'answer': 'To exit a loop or switch statement'},
        {'question': 'Which of the following is not a data type in C?', 'options': ['int', 'float', 'boolean', 'char'], 'answer': 'boolean'},
        {'question': 'What is the operator for logical NOT?', 'options': ['&', '!', '|', '~'], 'answer': '!'},
        {'question': 'What does `NULL` represent in C?', 'options': ['Zero', 'An empty string', 'A null pointer', 'An error'], 'answer': 'A null pointer'},
        {'question': 'Which loop executes at least once?', 'options': ['for', 'while', 'do-while', 'if'], 'answer': 'do-while'},
        {'question': 'What is the format specifier for printing a float?', 'options': ['%d', '%f', '%c', '%s'], 'answer': '%f'},
        {'question': 'Which of these is a valid identifier?', 'options': ['1name', '_name', 'name-1', 'name 1'], 'answer': '_name'},
        {'question': 'What is the default value of a global variable in C?', 'options': ['Garbage value', '0', 'NULL', 'Undefined'], 'answer': '0'},
        {'question': 'Which keyword is used to return from a function?', 'options': ['exit', 'quit', 'return', 'break'], 'answer': 'return'},
        {'question': 'What is the function of `sizeof` operator?', 'options': ['Calculates memory address', 'Returns size of a variable or type', 'Compares two values', 'Performs bitwise operation'], 'answer': 'Returns size of a variable or type'},
        {'question': 'What is the purpose of `goto` statement?', 'options': ['To jump to a labeled statement', 'To exit the program', 'To call a function', 'To include a header file'], 'answer': 'To jump to a labeled statement'},
        {'question': 'Which operator is used for modulus?', 'options': ['/', '%', '*', '+'], 'answer': '%'},
        {'question': 'How many keywords are there in C?', 'options': ['24', '32', '48', '64'], 'answer': '32'},
    ],
    'Python': [
        {'question': 'Which of the following is mutable in Python?', 'options': ['tuple', 'string', 'list', 'int'], 'answer': 'list'},
        {'question': 'How do you comment a single line in Python?', 'options': ['// comment', '# comment', '/* comment */', '-- comment'], 'answer': '# comment'},
        {'question': 'Which keyword is used to define a function in Python?', 'options': ['func', 'def', 'function', 'define'], 'answer': 'def'},
        {'question': 'What is the output of `type([])`?', 'options': ['<class \'list\'>', '<class \'tuple\'>', '<class \'dict\'>', '<class \'set\'>'], 'answer': '<class \'list\'>'},
        {'question': 'Which method is used to add an item to the end of a list?', 'options': ['insert()', 'append()', 'add()', 'put()'], 'answer': 'append()'},
        {'question': 'What is PEP 8?', 'options': ['A Python error code', 'A style guide for Python code', 'A Python package manager', 'A type of Python loop'], 'answer': 'A style guide for Python code'},
        {'question': 'Which of these is an immutable data type?', 'options': ['list', 'dictionary', 'set', 'string'], 'answer': 'string'},
        {'question': 'What is the purpose of `__init__` method?', 'options': ['To destroy an object', 'To initialize an object\'s attributes', 'To print an object', 'To define a class'], 'answer': 'To initialize an object\'s attributes'},
        {'question': 'How do you open a file in read mode in Python?', 'options': ['open("file.txt", "w")', 'open("file.txt", "r")', 'open("file.txt", "a")', 'open("file.txt", "x")'], 'answer': 'open("file.txt", "r")'},
        {'question': 'What is the output of `2 ** 3`?', 'options': ['6', '8', '9', '5'], 'answer': '8'},
        {'question': 'Which module is used for regular expressions?', 'options': ['os', 'sys', 're', 'math'], 'answer': 're'},
        {'question': 'What is a virtual environment in Python?', 'options': ['A cloud server', 'An isolated Python environment', 'A debugging tool', 'A web framework'], 'answer': 'An isolated Python environment'},
        {'question': 'How do you remove an element from a set?', 'options': ['delete()', 'remove()', 'pop()', 'discard()'], 'answer': 'remove()'},
        {'question': 'What is the purpose of `pass` statement?', 'options': ['To skip a block of code', 'To indicate an empty block', 'To terminate the program', 'To define a variable'], 'answer': 'To indicate an empty block'},
        {'question': 'Which operator is used for string concatenation?', 'options': ['-', '*', '+', '/'], 'answer': '+'},
        {'question': 'What is `pip` in Python?', 'options': ['A standard library', 'A package installer', 'A type of data structure', 'A built-in function'], 'answer': 'A package installer'},
        {'question': 'What is the correct way to import a module named `my_module`?', 'options': ['include my_module', 'import my_module', 'require my_module', 'use my_module'], 'answer': 'import my_module'},
        {'question': 'What is slicing in Python?', 'options': ['Dividing a number', 'Extracting a portion of a sequence', 'Cutting a string', 'Rounding a float'], 'answer': 'Extracting a portion of a sequence'},
        {'question': 'What is the output of `len("hello")`?', 'options': ['4', '5', '6', 'Error'], 'answer': '5'},
        {'question': 'Which of these is used for exception handling?', 'options': ['if/else', 'try/except', 'for/in', 'while/break'], 'answer': 'try/except'},
    ],
    'Java': [
        {'question': 'What is the entry point of a Java application?', 'options': ['start()', 'main()', 'run()', 'begin()'], 'answer': 'main()'},
        {'question': 'Which keyword is used to inherit a class in Java?', 'options': ['implements', 'extends', 'inherits', 'uses'], 'answer': 'extends'},
        {'question': 'Which of the following is not a primitive data type in Java?', 'options': ['int', 'float', 'String', 'boolean'], 'answer': 'String'},
        {'question': 'What is the default value of an instance variable of type `int` in Java?', 'options': ['null', '0', 'undefined', 'garbage value'], 'answer': '0'},
        {'question': 'Which of the following is used to handle exceptions in Java?', 'options': ['try-catch', 'if-else', 'for-loop', 'switch-case'], 'answer': 'try-catch'},
        {'question': 'What is JVM?', 'options': ['Java Virtual Machine', 'Java Vector Model', 'Java Validation Method', 'Java Visual Manager'], 'answer': 'Java Virtual Machine'},
        {'question': 'Which access modifier makes a member accessible only within the same class?', 'options': ['public', 'protected', 'private', 'default'], 'answer': 'private'},
        {'question': 'How do you create an object of a class `MyClass`?', 'options': ['MyClass obj;', 'new MyClass();', 'MyClass obj = new MyClass();', 'create MyClass obj;'], 'answer': 'MyClass obj = new MyClass();'},
        {'question': 'Which interface is used to create a thread?', 'options': ['Runnable', 'Serializable', 'Cloneable', 'Comparable'], 'answer': 'Runnable'},
        {'question': 'What is the superclass of all classes in Java?', 'options': ['Class', 'Object', 'System', 'Main'], 'answer': 'Object'},
        {'question': 'Which keyword is used to prevent method overriding?', 'options': ['static', 'final', 'abstract', 'void'], 'answer': 'final'},
        {'question': 'What is the purpose of `static` keyword?', 'options': ['To make a variable constant', 'To associate a member with the class itself', 'To create a new instance', 'To hide implementation details'], 'answer': 'To associate a member with the class itself'},
        {'question': 'Which package contains the `ArrayList` class?', 'options': ['java.io', 'java.util', 'java.lang', 'java.net'], 'answer': 'java.util'},
        {'question': 'What is the concept of `Polymorphism`?', 'options': ['Ability of an object to take on many forms', 'Encapsulation of data', 'Hiding implementation details', 'Creating multiple threads'], 'answer': 'Ability of an object to take on many forms'},
        {'question': 'Which method is used to compare two strings for equality in Java?', 'options': ['==', 'equals()', 'compare()', 'match()'], 'answer': 'equals()'},
        {'question': 'What is the purpose of `this` keyword?', 'options': ['Refers to the superclass', 'Refers to the current object instance', 'Refers to a static variable', 'Refers to an outer class'], 'answer': 'Refers to the current object instance'},
        {'question': 'Which statement is used to terminate a loop or switch statement?', 'options': ['continue', 'exit', 'break', 'return'], 'answer': 'break'},
        {'question': 'What is the default access modifier for a class in Java?', 'options': ['public', 'private', 'protected', 'default (package-private)'], 'answer': 'default (package-private)'},
        {'question': 'What is an `abstract` class?', 'options': ['A class that cannot be instantiated', 'A class that contains only abstract methods', 'A class with no methods', 'A class that is final'], 'answer': 'A class that cannot be instantiated'},
        {'question': 'Which of these is a checked exception?', 'options': ['NullPointerException', 'ArrayIndexOutOfBoundsException', 'IOException', 'ClassCastException'], 'answer': 'IOException'},
    ]
}

# --- SMTP Configuration (Replace with your actual details) ---
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'nexoraquiz@gmail.com' # Your Gmail address
SMTP_PASSWORD = 'mpus sryr ohtt nobs'  # Generate an app password for Gmail

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    contestant_name = request.form['name']
    contestant_email = request.form['email']
    selected_language = request.form['language'] # Get selected language from form

    if not contestant_name or not contestant_email or not selected_language:
        return "Please fill in all fields and select a language.", 400

    # Store contestant details in the database
    db = get_db()
    if not db:
        return "Database connection error. Please try again later.", 500

    cursor = db.cursor()
    contestant_id = None
    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM contestants WHERE email = %s", (contestant_email,))
        existing_contestant = cursor.fetchone()

        if existing_contestant:
            contestant_id = existing_contestant[0]
            print(f"Contestant with email {contestant_email} already exists. Using existing ID: {contestant_id}")
        else:
            cursor.execute("INSERT INTO contestants (name, email) VALUES (%s, %s)",
                           (contestant_name, contestant_email))
            db.commit()
            contestant_id = cursor.lastrowid
            print(f"New contestant added with ID: {contestant_id}")

    except MySQL_Error as e:
        db.rollback()
        print(f"Error inserting contestant: {e}")
        return "Database error while registering. Please try again.", 500
    finally:
        cursor.close()
        db.close()

    session['contestant_id'] = contestant_id
    session['contestant_name'] = contestant_name
    session['contestant_email'] = contestant_email
    session['selected_language'] = selected_language

    # Randomly select 5 questions for the chosen language
    all_questions_for_lang = QUIZ_QUESTIONS.get(selected_language, [])
    if len(all_questions_for_lang) < 5:
        return f"Not enough questions available for {selected_language}. Please choose another.", 400
    session['quiz_questions'] = random.sample(all_questions_for_lang, 5)
    session['current_question_index'] = 0
    session['score'] = 0

    return redirect(url_for('quiz'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'quiz_questions' not in session or 'current_question_index' not in session:
        return redirect(url_for('index'))

    quiz_questions = session['quiz_questions']
    current_question_index = session['current_question_index']

    if request.method == 'POST':
        user_answer = request.form.get('answer')
        correct_answer = quiz_questions[current_question_index]['answer']

        if user_answer == correct_answer:
            session['score'] += 1

        session['current_question_index'] += 1
        current_question_index = session['current_question_index'] # Update for next check

    if current_question_index < len(quiz_questions):
        question_data = quiz_questions[current_question_index]
        return render_template('quiz.html',
                               question=question_data['question'],
                               options=question_data['options'],
                               question_number=current_question_index + 1,
                               total_questions=len(quiz_questions))
    else:
        # Quiz finished
        contestant_id = session.get('contestant_id')
        score = session['score']
        total_questions = len(quiz_questions)
        language = session['selected_language']

        # Store quiz results in the database
        db = get_db()
        if db and contestant_id is not None:
            cursor = db.cursor()
            try:
                cursor.execute("INSERT INTO quiz_results (contestant_id, language, score, total_questions) VALUES (%s, %s, %s, %s)",
                               (contestant_id, language, score, total_questions))
                db.commit()
            except MySQL_Error as e:
                db.rollback()
                print(f"Error storing quiz result: {e}")
            finally:
                cursor.close()
                db.close()
        else:
            print("Failed to store quiz results due to database connection or missing contestant ID.")


        # Send email with results
        send_quiz_result_email(session['contestant_email'], session['contestant_name'], language, score, total_questions)

        return redirect(url_for('result'))

@app.route('/result')
def result():
    if 'score' not in session or 'contestant_name' not in session:
        return redirect(url_for('index'))

    score = session['score']
    total_questions = len(session['quiz_questions'])
    contestant_name = session['contestant_name']
    language = session['selected_language']

    # Clear session data after displaying results
    session.pop('quiz_questions', None)
    session.pop('current_question_index', None)
    session.pop('score', None)
    session.pop('contestant_id', None)
    session.pop('contestant_name', None)
    session.pop('contestant_email', None)
    session.pop('selected_language', None)

    return render_template('result.html',
                           name=contestant_name,
                           score=score,
                           total=total_questions,
                           language=language)

# --- Email Sending Function (remains the same) ---
def send_quiz_result_email(to_email, contestant_name, language, score, total_questions):
    subject = f"Your Quiz Results: {language} Programming Language"
    body = f"""
    Dear {contestant_name},

    Thank you for participating in our programming language quiz!

    Here are your results for the {language} quiz:
    Your Score: {score} out of {total_questions}

    Keep practicing and improving your skills!

    Best regards,
    The Nexora Quiz Team
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

if __name__ == '__main__':
    app.run(debug=True) # Set debug=False in production