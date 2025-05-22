from models.quiz_models import *
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import os
from io import BytesIO
import base64

from models.quiz_models import db, User, Quiz, Score, Subject, Chapter, Question
from werkzeug.security import generate_password_hash, check_password_hash
from  sqlalchemy.exc import IntegrityError
app = Flask(__name__ , template_folder="templates")

app.secret_key = "your-secret-key"
app.config['SESSION_TYPE'] = 'filesystem'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db1.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
app.app_context().push()

def setup_database():

    # Check if an admin already exists
    if not User.query.first():
        # Default admin credentials
        admin_username = "admin"
        admin_password = "admin123"
        admin_email = "admin@123"
        admin_full_name = "Admin User"
        admin_qualifications = "BSc Computer Science"
        admin_date_of_birth = "01/01/1990"
        admin_role = "admin"

        
        # Create and add the admin
        new_admin = User(username=admin_username, password=admin_password, email=admin_email, full_name=admin_full_name, qualifications=admin_qualifications, date_of_birth=admin_date_of_birth, role=admin_role)
        db.session.add(new_admin)
        db.session.commit()
        print(f"Admin user '{admin_username}' has been created.")


with app.app_context():
    db.create_all()

    setup_database()


#Route to render the home page
@app.route("/", methods=['GET','POST'])
def home_page():
    return render_template("home_page.html")

# Route for User Registration
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        qualifications = request.form['qualifications']
        date_of_birth = request.form['date_of_birth']

        # Convert date_of_birth to YYYY-MM-DD format
        
        try:
            date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format! Please use YYYY-MM-DD.", "danger")
            return redirect(url_for('register'))

        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or Email already exists!', 'danger')
            return redirect(url_for('register'))

        # Hash the password before storing
        hashed_password = generate_password_hash(password)

        # Create new user
        user_details = User(username=username, email=email, password=hashed_password,
                        full_name=full_name, qualifications=qualifications, date_of_birth=date_of_birth)

        db.session.add(user_details)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('user_login'))

    return render_template("user_register.html")

# Route for User Login
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        
        email = request.form.get('email')
        password = request.form.get('password')

        # Fetch user by email
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            # Store user details in session
            session['user_id'] = user.id
            session['username'] = user.username

            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))  # Redirect to dashboard

        else:
            flash('Invalid email or password!', 'danger')
            return render_template('user_login.html')
    return render_template('user_login.html')

# Route for User Dashboard

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('user_login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    quizzes = (
        db.session.query(Quiz, Chapter, Subject)
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
        .all()
    )

    quizzes_list = []
    for quiz, chapter, subject in quizzes:
        # Convert date_of_quiz from string to datetime object
        date_of_quiz = datetime.strptime(quiz.date_of_quiz, "%Y-%m-%d") if isinstance(quiz.date_of_quiz, str) else quiz.date_of_quiz

        quizzes_list.append({
            'id': quiz.id,
            'title': quiz.title,
            'subject_name': subject.name,
            'chapter_name': chapter.name,
            'num_questions': len(quiz.questions),
            'date_of_quiz': date_of_quiz,  # Now it's a datetime object
            'time_duration': quiz.time_duration
        })

    return render_template('user_dashboard.html', user=user, quizzes=quizzes_list)

# Route for viewing quiz details
@app.route('/view_quiz/<int:quiz_id>')
def view_quiz(quiz_id):
    quiz_details = Quiz.query.get_or_404(quiz_id)

    # Fetch related chapter safely
    chapter = Chapter.query.get(quiz_details.chapter_id) if quiz_details.chapter_id else None

    # Fetch related subject safely (now correctly checking chapter before accessing subject_id)
    subject = Subject.query.get(chapter.subject_id) if chapter else None

    # Fetch all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    return render_template(
        'view_quiz.html',
        quiz=quiz_details,
        subject=subject,
        chapter=chapter,
        questions=questions
    )

# Route for taking a quiz
@app.route('/attempt_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def attempt_quiz(quiz_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to attempt quizzes!", "danger")
        return redirect(url_for("user_login"))

    user = User.query.get(user_id)
    quiz = Quiz.query.get(quiz_id)
    questions = quiz.questions if quiz else []

    if request.method == "POST":
        total_score = 0
        for question in questions:
            selected_answer = request.form.get(f"question_{question.id}")  # Get selected answer
            if selected_answer and int(selected_answer) == question.correct_option:
                total_score += 1  # Increase score if correct

        # Save the score in the database
        new_score = Score(user_id=user.id, quiz_id=quiz.id, total_scores=total_score)
        db.session.add(new_score)
        db.session.commit()

        flash("Quiz submitted successfully!", "success")
        return redirect(url_for("view_result", quiz_id=quiz.id))

    return render_template("attempt_quiz.html", quiz=quiz, user=user, questions=questions)

# Route for submiting quiz
@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    user_id = session.get('user_id')  # Ensure user is logged in

    if not user_id:
        flash("You must be logged in to submit the quiz!", "danger")
        return redirect(url_for('login'))

    score = 0
    total_questions = len(questions)

    for question in questions:
        selected_option = request.form.get(f"q{question.id}")
        if selected_option and int(selected_option) == question.correct_option:
            score += 1  # Increase score if correct answer

    # Save score to database
    new_score = Score(quiz_id=quiz_id, user_id=user_id, total_scores=score)
    db.session.add(new_score)
    db.session.commit()

    flash(f'Quiz submitted successfully! Your Score: {score}/{total_questions}', 'success')
    return redirect(url_for('view_result', quiz_id=quiz_id))
@app.route('/view_result/<int:quiz_id>')
def view_result(quiz_id):
    user_id = session.get('user_id')

    if not user_id:
        flash("You must be logged in to view the result!", "danger")
        return redirect(url_for('user_login'))

    user = User.query.get(user_id)
    score = Score.query.filter_by(quiz_id=quiz_id, user_id=user_id).first()

    if not score:
        flash("No score found for this quiz!", "warning")
        return redirect(url_for('user_dashboard'))

    return render_template('view_result.html', quiz_id=quiz_id, score=score, user=user)

@app.route('/quiz_performance_chart/<int:quiz_id>')
def quiz_performance_chart(quiz_id):
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('user_login'))

    score = Score.query.filter_by(quiz_id=quiz_id, user_id=user_id).first()
    if not score:
        return redirect(url_for('user_dashboard'))

    # Data for bar chart
    labels = ['Correct', 'Incorrect']
    values = [score.total_scores, len(score.quiz.questions) - score.total_scores]

    # Create bar chart
    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color=['green', 'red'])
    plt.xlabel('Category')
    plt.ylabel('Count')
    plt.title('Quiz Performance')

    # Convert to PNG image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return Response(img.getvalue(), mimetype='image/png')

# Route to generate a pie chart for quiz results
@app.route('/quiz_pie_chart/<int:quiz_id>')
def quiz_pie_chart(quiz_id):
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('user_login'))

    score = Score.query.filter_by(quiz_id=quiz_id, user_id=user_id).first()
    if not score:
        return redirect(url_for('user_dashboard'))

    # Data for pie chart
    labels = ['Correct', 'Incorrect']
    sizes = [score.total_scores, len(score.quiz.questions) - score.total_scores]
    colors = ['green', 'red']

    # Create pie chart
    plt.figure(figsize=(6, 4))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('Correct vs Incorrect Answers')

    # Convert to PNG image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return Response(img.getvalue(), mimetype='image/png')


@app.route("/admin_login", methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    
        user = User.query.filter_by(username=username).first()

        print(user.password)

    # Validate user credentials
        if user and user.password == password and user.role == 'admin':
            # Redirect to user dashboard after successful login
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('admin_login.html', error='Invalid username or password.')
    
    return render_template("admin_login.html")

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home_page'))

# route for user profile
@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('user_login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.date_of_birth = request.form['date_of_birth']
        user.qualifications = request.form['qualifications']

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('user_profile.html', user=user)

@app.route("/admin_dashboard", methods=['GET','POST'])
def admin_dashboard():
    subjects = Subject.query.all()
    return render_template("admin_dashboard.html", subjects=subjects)

@app.route('/search_subjects', methods=['GET'])
def search_subjects():
    query = request.args.get('query', '').strip()

    if not query:
        return jsonify([])  # Return an empty list if no input

    # Search subjects (case-insensitive)
    subjects = Subject.query.filter(Subject.name.ilike(f"%{query}%")).all()

    # Convert subjects to JSON format
    results = [{"id": subject.id, "name": subject.name} for subject in subjects]

    return jsonify(results)



@app.route('/admin/quizzes')
def admin_quizzes():
    chapters = Chapter.query.all()
    quizzes = Quiz.query.all()  
    return render_template('admin_quizzes.html', chapters=chapters, quizzes=quizzes)

# Route to add subjects(CRUD --> Create)
@app.route('/add_subjects', methods=['GET', 'POST'])
def add_subjects():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        #check if subject already exists
        existing_subject = Subject.query.filter_by(name=name).first()
        if existing_subject:
            flash('Subject already exists!', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()

        flash("Subject added successfully!", "success")
        return redirect(url_for('admin_dashboard'))
    
    # Fetch all subjects and pass them to the template
    subjects = Subject.query.all()
    return render_template('add_subjects.html', subjects=subjects)
    
# Route to view subjects(CRUD --> Read)
@app.route('/view_subject/<int:subject_id>',methods=['GET','POST']) 
def view_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if subject:
        return render_template("view_subject.html", subject=subject)
    else:
        flash("Subject not found!", "danger")
        return redirect(url_for('admin_dashboard'))

# Route to edit subjects(CRUD --> Edit)
@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        subject.name = request.form['name']
        subject.description = request.form['description']
        db.session.commit()
        
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template("edit_subjects.html", subject=subject)

# Route to delete subjects(CRUD --> Delete)
@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    db.session.delete(subject)
    db.session.commit()
    
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/subject/<int:subject_id>/add-chapter', methods=['GET', 'POST'])
def add_chapter(subject_id):
    # Fetch subject
    subject = Subject.query.get_or_404(subject_id)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        new_chapter = Chapter(name=name, description=description, subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()

        flash('Chapter added successfully!', 'success')
        return redirect(url_for('view_chapters', subject_id=subject_id))

    return render_template('add_chapters.html', subject=subject)

# Route for viewing chapters
@app.route('/admin/subject/<int:subject_id>/chapters')
def view_chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('admin_chapters.html', subject=subject, chapters=chapters)

# Route to edit chapters(CRUD --> Edit)
@app.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)

    if request.method == 'POST':
        chapter.name = request.form['name']
        chapter.description = request.form['description']
        db.session.commit()
        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('view_chapters', subject_id=chapter.subject_id))

    return render_template('edit_chapters.html', chapter=chapter)

# Route to delete chapters(CRUD --> Delete)
@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully!', 'success')
    return redirect(url_for('view_chapters', subject_id=chapter.subject_id))

# View All Quizzes for a Chapter
@app.route('/chapter/<int:chapter_id>/quizzes')
def view_quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('admin_quizzes.html', chapter=chapter, quizzes=quizzes)

# Create a New Quiz
@app.route('/chapter/add_quiz/<int:chapter_id>', methods=['GET', 'POST'])
def add_quiz(chapter_id):
    # Fetch the chapter object to pass to the template
    chapter = Chapter.query.get_or_404(chapter_id)

    if request.method == 'POST':
        title = request.form.get('title')
        date_of_quiz_str = request.form.get('date_of_quiz')  # String input from form
        time_duration = request.form.get('time_duration')

        # Validate required fields
        if not title or not date_of_quiz_str or not time_duration:
            flash("All fields are required!", "danger")
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        try:
            # Convert date_of_quiz from string to date object
            date_of_quiz = datetime.strptime(date_of_quiz_str, '%Y-%m-%d').date()

            new_quiz = Quiz(
                title=title,
                chapter_id=chapter_id,  # Directly using chapter_id from URL
                date_of_quiz=date_of_quiz,  # Pass the date object
                time_duration=time_duration
            )
            db.session.add(new_quiz)
            db.session.commit()
            flash("Quiz added successfully!", "success")
            return redirect(url_for('view_quizzes', chapter_id=chapter_id))

        except ValueError:
            flash("Invalid date format! Please use YYYY-MM-DD.", "danger")

        except IntegrityError:
            db.session.rollback()
            flash("Error: Could not add quiz. Please check your data.", "danger")

    # If method is GET, show the add quiz form and pass the chapter object
    return render_template('add_quiz.html', chapter=chapter)

# Edit an Existing Quiz
@app.route('/edit_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        quiz.date_of_quiz = datetime.strptime(request.form['date_of_quiz'], '%Y-%m-%d').date()  # Convert string to date
        quiz.time_duration = int(request.form['time_duration'])  # Ensure integer conversion

        quiz.remarks = request.form.get('remarks', '')

        db.session.commit()
        flash("Quiz updated successfully!", "success")
        return redirect(url_for('view_quizzes', chapter_id=quiz.chapter_id))

    return render_template('edit_quiz.html', quiz=quiz)

# Delete a Quiz
@app.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter_id = quiz.chapter_id
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted successfully!", "danger")
    return redirect(url_for('view_quizzes', chapter_id=chapter_id))

# route for viewing questions
@app.route('/admin/quiz/<int:quiz_id>/questions')
def view_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template('admin_questions.html', quiz=quiz, questions=questions)

# route for adding questions
@app.route('/admin/quiz/<int:quiz_id>/add-question', methods=['GET', 'POST'])
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        question_statement = request.form['question_statement']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option = int(request.form['correct_option'])  # Ensure integer conversion

        new_question = Question(
            quiz_id=quiz_id,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option
        )

        db.session.add(new_question)
        db.session.commit()

        flash('Question added successfully!', 'success')
        return redirect(url_for('view_questions', quiz_id=quiz_id))

    return render_template('add_question.html', quiz=quiz)

# route for editing questions
@app.route('/admin/question/<int:question_id>/edit', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        question.question_statement = request.form['question_statement']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']

        # Handle missing correct_option gracefully
        correct_option = request.form.get('correct_option')
        if correct_option:
            question.correct_option = int(correct_option)
        else:
            flash("Please select the correct option.", "danger")
            return redirect(url_for('edit_question', question_id=question.id))

        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('view_questions', quiz_id=question.quiz_id))

    return render_template('edit_question.html', question=question)

# route for deleting questions
@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id  # Store quiz_id to redirect back
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('view_questions', quiz_id=quiz_id))

# Route to view scores
@app.route('/admin/summary')
def admin_summary():
    # Fetch quiz summary data
    quizzes = db.session.query(
        Quiz.id,
        Quiz.title.label("quiz_title"),
        func.count(Score.id).label("total_attempts"),
        func.avg(Score.total_scores).label("avg_score"),
        func.max(Score.total_scores).label("highest_score"),
        func.min(Score.total_scores).label("lowest_score"),
        db.session.query(func.count(Question.id)).filter(Question.quiz_id == Quiz.id).label("total_questions")
    ).outerjoin(Score, Quiz.id == Score.quiz_id)\
     .group_by(Quiz.id).all()

    # Convert data into a dictionary format
    summary_data = [
        {
            "quiz_title": quiz.quiz_title,
            "total_questions": quiz.total_questions or 0,
            "total_attempts": quiz.total_attempts or 0,
            "avg_score": round(quiz.avg_score, 2) if quiz.avg_score is not None else 0,
            "highest_score": quiz.highest_score or 0,
            "lowest_score": quiz.lowest_score or 0
        }
        for quiz in quizzes
    ]

    # Generate Matplotlib charts
    if summary_data:
        quiz_titles = [quiz["quiz_title"] for quiz in summary_data]
        total_attempts = [quiz["total_attempts"] for quiz in summary_data]
        avg_scores = [quiz["avg_score"] for quiz in summary_data]

        # Bar Chart for Quiz Attempts
        plt.figure(figsize=(8, 4))
        plt.bar(quiz_titles, total_attempts, color='skyblue')
        plt.xlabel("Quizzes")
        plt.ylabel("Total Attempts")
        plt.title("Total Attempts per Quiz")
        plt.xticks(rotation=45)
        plt.tight_layout()
        bar_chart_path = os.path.join("static", "bar_chart.png")
        plt.savefig(bar_chart_path)
        plt.close()

        # Pie Chart for Average Scores Distribution
        plt.figure(figsize=(6, 6))
        plt.pie(avg_scores, labels=quiz_titles, autopct='%1.1f%%', colors=['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0'])
        plt.title("Average Score Distribution")
        pie_chart_path = os.path.join("static", "pie_chart.png")
        plt.savefig(pie_chart_path)
        plt.close()

    else:
        bar_chart_path = None
        pie_chart_path = None

    return render_template('admin_summary.html', summary_data=summary_data, bar_chart_path=bar_chart_path, pie_chart_path=pie_chart_path)


if __name__ == "__main__":
    app.run(debug=True)
