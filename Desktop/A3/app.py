
from flask import Flask, render_template, request,flash,redirect,url_for,g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3
engine = create_engine('sqlite:///user_info.db', echo = True)

app = Flask(__name__,)
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///user_info.db'
app.config['SECRET_KEY']='test'
DATABASE = './user_info.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin,db.Model):
	id = db.Column(db.Integer, primary_key=True)
	#30 character username/passwords where username is unqiue but passwords are not
	username = db.Column(db.String(30),unique = True)
	password = db.Column(db.String(30),unique = False)
	user_type = db.Column(db.String(10),unique = False)

	def __init__(self,usern,passw,inp_type):
		# Pass in username/password variables into user object
		self.username = usern
		self.password = passw
		self.user_type = inp_type

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

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


@app.route('/')
def index():

	if current_user.is_authenticated:
		return render_template('homepage.html')
	return render_template('login.html')

@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/homepage')
def homepage():
	if current_user.is_authenticated:
		return render_template('homepage.html')
	return render_template('login.html')

@app.route('/loginuser',methods = ['POST'])
def loginuser():
	username = request.form['username']
	password = request.form['password']
	user = User.query.filter_by(username=username).first()
	if not user:
		return '<h1>User not found!</h1>'
	password = User.query.filter_by(password=password).first()
	if not password:
		flash('Incorrect password')
		return render_template('login.html')
	login_user(user)
	if current_user.user_type =='student':
		return render_template('homepage.html')
	
	return render_template('instruct_login.html')


@app.route('/createuser', methods = ['GET','POST'])
def createuser():
	# Retrieve input information
	info = request.form
	# Get database
	db = get_db()
	# Create database entires into dictionaries
	db.row_factory = make_dicts
	# Create cursor for database selection
	cur = db.cursor()
	# Using our information in info, insert this into their appropriate places in the table User
	cur.execute('insert into user (username,password,user_type) values (?,?,?)',[info['username'],info['password'],info['user_type']])
	db.commit()
	cur.close()
	# Display message of succesful account creation
	flash('User was sucessfully created!')
	flash('Please login')
	return redirect(url_for('index'))
@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
	return 'The current user is:' + current_user.username

@app.route('/marks', methods = ['GET'])
@login_required
def marks():
	curr = "'" + str(current_user.username) + "'" 
	conn = sqlite3.connect('user_info.db')
	queryString = "SELECT * from marks WHERE username = " + curr
	col = conn.execute("PRAGMA table_info(marks)").fetchall()
	query = conn.execute(queryString).fetchall()
	conn.close()


	return render_template('marks.html',query=query,name = curr,columns=col)

@app.route('/instruct_marks', methods = ['GET','POST'])
@login_required
def instruct_marks():
	curr = "'" + str(current_user.username) + "'" 
	conn = sqlite3.connect('user_info.db')
	queryString = "SELECT * from marks"
	col = conn.execute("PRAGMA table_info(marks)").fetchall()
	query = conn.execute(queryString).fetchall()
	conn.close()


	return render_template('marks.html',query=query,name = curr,columns=col)

@app.route('/feedback',methods = ['GET','POST'])
@login_required
def create_post():
	info = request.form['feedback_1']
	conn = sqlite.connect('user_info.db')
	queryString = c.execute("INSERT INTO {feedback} ({feedback1}) VALUES (info)")
	return render_template('feedback.html')


if __name__ == '__main__':
	app.run(debug=True)