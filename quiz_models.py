from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
from sqlalchemy import func

db = SQLAlchemy()

class User(db.Model):

    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50),nullable=False,unique=True)
    email =  db.Column(db.String(100),nullable=False,unique=True)
    password = db.Column(db.String(200),nullable=False)
    full_name = db.Column(db.String(30),nullable=False)
    qualifications = db.Column(db.String(100),nullable=True)
    date_of_birth = db.Column(db.String(100),nullable=True)
    role = db.Column(db.String(100),nullable=False,default='user')
    scores = db.relationship('Score',backref='user',lazy=True)


class Subject(db.Model):

    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False)
    chapters = db.relationship('Chapter',backref='subject',lazy=True, cascade='all, delete-orphan')


class Chapter(db.Model):
    
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    quizzes = db.relationship('Quiz',backref='chapter',lazy=True, cascade='all, delete-orphan')  
    
class Quiz(db.Model):
    
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    title = db.Column(db.String(100), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    date_of_quiz = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    time_duration = db.Column(db.String(10), nullable=False)  # Example: "01:30" (1 hour, 30 minutes)
    
    #relationship 
    questions = db.relationship('Question',backref='quiz',lazy=True,cascade='all, delete-orphan')
    

class Question(db.Model):
    
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_statement = db.Column(db.String(200), nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  

class Score(db.Model):
    
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    total_scores = db.Column(db.Integer, nullable=False)
    #relationship
    quiz = db.relationship('Quiz', backref='scores', lazy=True)