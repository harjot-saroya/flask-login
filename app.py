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
# (don't worry if you don't understand this code)
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# given a SELECT query, executes and returns the result
# (don't worry if you don't understand this code)
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

@app.route('/login', methods = ['GET','POST'])
def login():
    db = get_db()
    db.row_factory = make_dicts
    info = request.form
    query = query_db('select * from user where username = ? and password = ?', [info['username'],info['password']], one = True)
    found = False
    db.close()
    if (query):
        found = True
    else:
        flash('Incorrect credentials')
        flash('Please try again')
        return redirect(url_for('index'))
    if (found == True):
        if (query['username'] != None):
            if (query['password'] == info['password']):
                session['username'] = info['username']
                session['type'] = query['user_type']
                return render_template('homepage.html',query = query)
            else:
                flash('Incorrect credentials')
                return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/create-user', methods = ['GET','POST'])
def newUser():
    db = get_db()
    db.row_factory = make_dicts
    cur = db.cursor()
    info = request.form
    cur.execute('insert into user (username,password,user_type) values (?,?,?)', [info['username'],info['password'],info['user_type']])
    db.commit()
    cur.close()
    flash('User was sucessfully created!')
    flash('Please login')
    return redirect(url_for('index'))


@app.route('/logout')
#@login_required
def logout():
    session.pop('username', None)
    session.pop('type', None)
    return redirect(url_for('index'))

@app.route('/marks')
def marks():
    if(session['type'] == 'instructor'):
        db = get_db()
        db.row_factory = make_dicts
        query = query_db('select id,username from user where user_type = ?',['student'])
        db.close()
        return render_template('studentlist.html',items = query)
    user = session['username']
    db = get_db()
    db.row_factory = make_dicts
    items = []
    query = query_db('select * from marks where username = ?',[user], one = True)
    items.append(query)
    db.close()
    return render_template('marks.html',query = items)

@app.route('/viewmark', methods = ['GET','POST'])
def viewmark():
    db = get_db()
    db.row_factory = make_dicts
    student = request.form
    session['student'] = student['user']
    query = query_db('select * from marks where username = ?',[student['user']])
    return render_template('editmarks.html',items = query,name = student['user'])

@app.route('/editmark', methods = ['GET','POST'])
def editmark():
    db = get_db()
    db.row_factory = make_dicts
    form = request.form
    print('1')
    print(form)
    cur = db.cursor()
    evaluation = form['evaluation']
    grade = form['grade']

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
