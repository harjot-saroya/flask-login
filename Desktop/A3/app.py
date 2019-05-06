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
        print('instructor')
        return render_template('homepage.html')
    user = session['username']
    db = get_db()
    db.row_factory = make_dicts
    items = []
    query = query_db('select * from marks where username = ?',[user], one = True)
    items.append(query)
    db.close()
    return render_template('marks.html',query = items)

@app.route('/remark',methods = ['GET','POST'])
def remark():
    feedback = request.form
    db = get_db()
    db.row_factory = make_dicts
    cur = db.cursor()
    stuid = query_db('select id from user where username = ?',[session['username']],one = True)
    cur.execute('insert into remark (id,username,reason,evaluation) values (?,?,?,?)',[stuid['id'],session['username'],feedback['reason'],feedback['evaluation']])
    db.commit()
    cur.close()
    flash('Remark request submitted!')
    return redirect(url_for('marks'))

@app.route('/feedback', methods = ['GET','POST'])
def feedback():
    if (session['type'] == 'student'):
        db = get_db()
        db.row_factory = make_dicts
        items = []
        query = query_db('select id,username from user where user_type = ?',['instructor'])
        items = query
        return render_template('instructor_select.html',items = items)
    return redirect(url_for('homepage'))
@app.route('/create-feedback', methods = ['GET','POST'])
def create():
        db = get_db()
        db.row_factory = make_dicts
        query = query_db('select username from user where user_type = ?', ['instructor'])
        cur = db.cursor()
        feedback = request.form
        for item in query:
            if (feedback['user'] == item['username']):
                print(feedback)
                cur.execute('insert into feedback (username,comment) values (?,?)',[feedback['user'],feedback['comment']])
                db.commit()
                cur.close()
                flash('Feedback sucessfully created!')
                return redirect(url_for('feedback'))
        
        flash('This instructor does not exist!')
        return redirect(url_for('feedback'))


# run the app when app.py is run
if __name__ == '__main__':
    app.run(debug=True)
