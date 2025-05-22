# quiz-master
It is a multi-user app (one requires an administrator and other users) that acts as an exam preparation site for multiple courses.

## Project Overview

**Quiz Master** is a multi-user web application designed as an exam preparation platform for multiple courses. It supports two roles:  
- **Admin (Quiz Master):** The superuser who manages subjects, chapters, quizzes, questions, and users.  
- **User:** Registered users who can attempt quizzes, view scores, and track their progress.

This project is built using the following mandatory technologies:  
- **Backend:** Flask  
- **Frontend:** Jinja2 templating, HTML, CSS, Bootstrap  
- **Database:** SQLAlchemy 

---

## Features

### Admin (Quiz Master)  
- Single pre-existing admin account (no registration).  
- Login and access to an admin dashboard.  
- Create, edit, delete subjects.  
- Create, edit, delete chapters under subjects.  
- Create, edit, delete quizzes under chapters with date and time duration.  
- Add, edit, delete MCQ questions for quizzes (single correct option).  
- Search users, subjects, quizzes.  
- View summary charts and analytics.  

### User  
- User registration and login.  
- Browse and select subjects and chapters.  
- Attempt quizzes with optional timer.  
- View quiz scores and history of attempts.  
- View summary charts of performance.

---

## Technologies & Frameworks

- **Flask:** Backend web framework  
- **Jinja2:** Templating engine for rendering HTML  
- **HTML5, CSS3, Bootstrap:** Frontend styling and responsive design  
- **SQLite:** Lightweight relational database  
- **Optional:** Chart.js for analytics visualization  

---

## Database Design (ER Diagram Summary)

- **User:** id (PK), username (email), password, full_name, qualification, dob  
- **Admin:** single pre-existing user with root privileges  
- **Subject:** id (PK), name, description  
- **Chapter:** id (PK), subject_id (FK), name, description  
- **Quiz:** id (PK), chapter_id (FK), date_of_quiz, time_duration, remarks  
- **Question:** id (PK), quiz_id (FK), question_statement, option1, option2, option3, option4, correct_option  
- **Score:** id (PK), quiz_id (FK), user_id (FK), timestamp, total_score  

---

*Thank you for reviewing the Quiz Master project! Feel free to reach out for any questions or feedback.*

---
