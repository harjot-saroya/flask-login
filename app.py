# required imports
# the sqlite3 library allows us to communicate with the sqlite database
import sqlite3
# we are adding the import 'g' which will be used for the database
from flask import Flask, flash, render_template, redirect, url_for, request, g, session

# the database file we are going to communicate with
DATABASE = './user_info.db'

# connects to the database
def get_db():
    # if there is a database, use it
    db = getattr(g, '_database', None)
    if db is None:
        # otherwise, create a database to use
        db = g._database = sqlite3.connect(DATABASE)
    return db

# converts the tuples from get_db() into dictionaries
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# given a SELECT query, executes and returns the result
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# tells Flask that "this" is the current running app
app = Flask(__name__)
app.config['SECRET_KEY']='test'

# this function gets called when the Flask app shuts down
# tears down the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # close the database if we are connected to it
        db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/homepage')
def homepage():
    return render_template('homepage.html')

# Login
@app.route('/login', methods = ['GET','POST'])
def login():
    # Get the database
    db = get_db()
    # Make database entries into dictionaries
    db.row_factory = make_dicts
    # Get login information from user
    info = request.form
    # Query the database for the user based on username and password
    query = query_db('select * from user where username = ? and password = ?', [info['username'],info['password']], one = True)
    # Declare a variable to detect when we've found the user
    found = False
    # Close database
    db.close()
    # If our query is not none ie. we've found our user, set found to true
    if (query):
        found = True
    else:
        # Otherwise flash that the credentials are not valid
        flash('Incorrect credentials')
        flash('Please try again')
        # Return to index
        return redirect(url_for('index'))
    # If we have found our user
    if (found == True):
        # Check if the username exists
        if (query['username'] != None):
            # Check if the password is correct
            if (query['password'] == info['password']):
                # Set the session username to our current user's username
                session['username'] = info['username']
                # Set the session type to our current user's user type
                session['type'] = query['user_type']
                # Enter the homepage and pass user information to homepage
                return render_template('homepage.html',query = query)
            # If the password is wrong flash incorrect credentials and return
            # To the login page
            else:
                flash('Incorrect credentials')
                return redirect(url_for('login'))
    return redirect(url_for('login'))

# New user creation
@app.route('/create-user', methods = ['GET','POST'])
def newUser():
    db = get_db()
    db.row_factory = make_dicts
    # Define a cursor to traverse our queries
    cur = db.cursor()
    # Get new user information
    info = request.form
    # Insert new user information into our user database
    cur.execute('insert into user (username,password,user_type) values (?,?,?)', [info['username'],info['password'],info['user_type']])
    # Commit changes
    db.commit()
    cur.close()
    # Flash that a new user was created and prompt login
    flash('User was sucessfully created!')
    flash('Please login')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    # Pop user's username
    session.pop('username', None)
    # Pop user's user type
    session.pop('type', None)
    # If we have created a session for student (as an instructor) then pop it
    if (session['student']):
        session.pop('student',None)
    return redirect(url_for('index'))

@app.route('/marks')
def marks():
    # If our current user is an instructor allow mark editing
    if(session['type'] == 'instructor'):
        db = get_db()
        db.row_factory = make_dicts
        # Query all students in the database to show instructor which students are
        # Presently in his class
        query = query_db('select id,username from user where user_type = ?',['student'])
        db.close()
        return render_template('studentlist.html',items = query)
    # If our current user is a student then get their username from session
    user = session['username']
    db = get_db()
    db.row_factory = make_dicts
    items = []
    # Retrieve marks from the database for our current user
    query = query_db('select * from marks where username = ?',[user], one = True)
    items.append(query)
    db.close()
    return render_template('marks.html',query = items)

# This is for the instructor to view marks for a specific student
@app.route('/viewmark', methods = ['GET','POST'])
def viewmark():
    db = get_db()
    db.row_factory = make_dicts
    # Get information from instructor on desired student
    student = request.form
    # Create a new session variable called student which has the name of the student
    session['student'] = student['user']
    # Query the marks for this student
    query = query_db('select * from marks where username = ?',[student['user']])
    return render_template('editmarks.html',items = query,name = student['user'])

# This allows instructors to edit marks for a student
@app.route('/editmark', methods = ['GET','POST'])
def editmark():
    db = get_db()
    db.row_factory = make_dicts
    # Get information like grade and evaluation from instructor
    form = request.form
    cur = db.cursor()
    evaluation = form['evaluation']
    grade = form['grade']

    # Create cases for each evaluation and update them accordingly
    if (evaluation == 'quiz1'):
        cur.execute('update marks set quiz1 = ? where username = ?',(grade,session['student']))
        db.commit()
        flash('Mark sucessfully updated')
        return redirect(url_for('marks'))
    elif (evaluation == 'quiz2'):
        cur.execute('update marks set quiz2 = ? where username = ?',(grade,session['student']))
        flash('Mark sucessfully updated')
        db.commit()
        return redirect(url_for('marks'))
    elif( evaluation == 'quiz3'):
        cur.execute('update marks set quiz3 = ? where username = ?',(grade,session['student']))
        flash('Mark sucessfully updated')
        db.commit()
        return redirect(url_for('marks'))
    else:
        flash('ERROR: This evaluation does not exists')
        return redirect(url_for('marks'))
    db.close()
    cur.close()
    return redirect(url_for('marks'))

# Allows student to send in a remark request
@app.route('/remark',methods = ['GET','POST'])
def remark():
    # Get information from the student via form
    feedback = request.form
    db = get_db()
    db.row_factory = make_dicts
    cur = db.cursor()
    # Query the user database for the id of the student who is currently logged int
    stuid = query_db('select id from user where username = ?',[session['username']],one = True)
    # Create an entry in the remark
    cur.execute('insert into remark (id,username,reason,evaluation) values (?,?,?,?)',[stuid['id'],session['username'],feedback['reason'],feedback['evaluation']])
    db.commit()
    cur.close()
    # Flash that the remark request was submitted
    flash('Remark request submitted!')
    return redirect(url_for('marks'))

# Allows students to create feedback and instructors to view feedback
@app.route('/feedback', methods = ['GET','POST'])
def feedback():
    # Check if current user is a student
    if (session['type'] == 'student'):
        db = get_db()
        db.row_factory = make_dicts
        # Get id and username of all instructors in the database
        query = query_db('select id,username from user where user_type = ?',['instructor'])
        items = query
        # Send this info to our html file for display
        return render_template('instructor_select.html',items = items)
    # If our current user is an instructor
    db = get_db()
    db.row_factory = make_dicts
    # Get the username of the instructor currently on the session
    user = session['username']
    # Get the comments for the currently logged in instructor
    query = query_db('select comment from feedback where username = ?',[user])
    db.close()
    return render_template('instruct_comment.html',items = query)
@app.route('/create-feedback', methods = ['GET','POST'])
def create_feedback():
        db = get_db()
        db.row_factory = make_dicts
        # Get usernames of all instructors in the database
        query = query_db('select username from user where user_type = ?', ['instructor'])
        cur = db.cursor()
        # Get information about a specific instructor from student
        feedback = request.form
        print(feedback)

        # Loop through instructors to find the instructor the student specified
        for item in query:
            if (feedback['user'] == item['username']):
                # If this instructor exists, insert the user's comment and instructor they chose into the feedback sql table
                cur.execute('insert into feedback (username,comment) values (?,?)',[feedback['user'],feedback['comment']])
                db.commit()
                cur.close()
                flash('Feedback sucessfully created!')
                return redirect(url_for('feedback'))
        # If user does not exist, flash this and redirect to feedback screen
        flash('This instructor does not exist!')
        return redirect(url_for('feedback'))


# run the app when app.py is run
if __name__ == '__main__':
    app.run(debug=True)
