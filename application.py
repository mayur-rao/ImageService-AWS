import flask
from flask import Flask
from werkzeug.utils import secure_filename
from flask import Flask, flash, redirect, render_template, url_for, send_from_directory, request, jsonify, session, abort, make_response
import subprocess
import gc
import os
from subprocess import PIPE, Popen
import re
import random, struct
from flask import Markup
import os.path
import config
from datetime import timedelta
from flask import Flask
from flask_s3 import FlaskS3
import boto
import boto.s3.connection
from boto.s3.key import Key
from boto.s3.connection import S3Connection
import botocore
from datetime import datetime
import datetime
from boto.s3.key import Key
import MySQLdb
from MySQLdb import escape_string as thwart
from PIL import Image


application = flask.Flask(__name__, static_url_path='/static')

#Security Feature: Max Password attempts counter
login_failed = 0
application.secret_key = config.secret_key_file

#Security Feature: Regex for username and password
userreg = config.user_reg
passreg = config.user_passv

#Database Connection. Security Feature: Getting secrets from different file
db = MySQLdb.connect(config.host,  
                     config.user,        
                     config.passwd,  
                     config.db)        
cur = db.cursor()

#S3 connection
conn = S3Connection(config.access_key, config.secret_key)


@application.errorhandler(400)
def not_found(error):
    return flask.make_response(flask.jsonify( { 'error': 'Bad request' } ), 400)

@application.errorhandler(404)
def not_found(error):
    return flask.make_response(flask.jsonify( { 'error': 'Not found' } ), 404)

#Welcome Screen	   
@application.route('/')
def home():
    return render_template('welcome.html')

#Registration page
@application.route('/register', methods=["GET","POST"])
def register_page():
    error = ''
    file_contents = ''
    try:
            username = request.form['user']
            if (re.match(userreg,username)):
                bucket = conn.get_bucket(config.buck_name, validate=True)
                k = Key(bucket)
                k.key = 'auth_user.txt'
                k.open()
                file_contents = k.read()
                file_contents+=username
                key = bucket.new_key('auth_users.txt')
                key.set_contents_from_string(file_contents)
                key.set_acl('public-read')
                return 'Successfully Registered. Login.'
            else:
		return 'UserName:3-15 charecters consisting of letter or digits and optional -or_.'
    except Exception as e:
        return(str(e))

#Secure Login Function with max attempts, regex and session. 
#Storing hashed passwords on database. 
@application.route('/login', methods=["GET","POST"])
def login():
  error = ''
  file_contents = ''
  global login_failed
  keys = []
  if(login_failed < 2):
    if request.method == 'POST':
        username_form  = request.form['username']
        bucket = conn.get_bucket(config.buck_name, validate=True)
        k = Key(bucket)
        k.key = 'auth_users.txt'
        k.open()
        file_contents = k.read()
        if username_form in file_contents:
            session['logged_in'] = True
            session['username'] = username_form
            #session.permanent = True
            #app.permanent_session_lifetime = timedelta(seconds=300)
            return render_template('upload_db.html', username = session['username'])
        else:
            login_failed = login_failed+1
            error+= "Invalid Username. Login Again"
            return render_template('welcome.html', error = error)
  else:
	login_failed = 0
	error = 'You have exceeded maximum attempts for failed login. Locked Out. Try agin after 30 mins'
        return render_template('welcome.html', error = error)
	
    
#Secure filename of flask used.	
@application.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
 error = ''
 count = 0
 file_list = []
 f_list = ''
 if('username' in session):
    #encryptor = AES.new(key, AES.MODE_CBC, IV)
    if request.method == 'POST':
        file = request.files['userfile']
        comment  = request.form['comment1']
        if file and allowed_file(file.filename):
            #bucket = conn.get_bucket(config.buck_name, validate=True)
            filename = secure_filename(file.filename)
            folder1 = session['username'] + '/'
            for bucket in conn.get_all_buckets():
                for key in bucket.list(prefix = folder1):
                    a,b = key.name.split("/")
                    file_list.append(b)
            a,b = filename.split(".")
            if b == 'jpg' or b == 'jpeg' or b == 'png' or b == 'gif':
                img = Image.open(file)
                width, height = img.size
            if b == 'jpg' or b == 'jpeg' or b == 'png' or b == 'gif' or b == 'mp4':
                bucket = conn.get_bucket(config.buck_name, validate=True)
            else:
                bucket = conn.get_bucket(config.buck_name_other, validate=True)
            file_contents = file.read()
            file.seek(0)
            for key in bucket.list(prefix = folder1):
                count+=1
            if len(file_contents) == 0:
                return 'Empty File'
            elif len(file_contents) > 1000000:
                return 'Please select a file less than or equal to 1 MB'
            elif count>3:
                return 'You have used up all your space. Buy more space.'
            elif filename in file_list:
                folder = session['username'] + '/' + filename
                key = bucket.new_key(folder)
                if comment!= "":
                    key.set_metadata('meta1', comment)
                key.set_contents_from_file(file)
                key.set_acl('public-read')
                return 'File already exists. Overwrite successfully'
            if b == 'jpg' or b == 'jpeg' or b == 'png' or b == 'gif':
                if width>1000 or height>1000:
                    return 'Accepted resolution should be less than 1000 * 1000. Try again.'
            folder = session['username'] + '/' + filename
            key = bucket.new_key(folder)
            if comment!= "":
                key.set_metadata('meta1', comment)
            key.set_contents_from_file(file)
            key.content_type = 'image/jpeg'
            key.set_acl('public-read')
            return 'Uploaded successfully'
        else:
	       return 'File Type not supported. Please try again!'
 else:
     error = 'Session Time Out. Please login again.'
     return render_template('welcome.html', error = error)

#####Overwrite function###############
@application.route('/overwrite/<file_contents><filename>')
def overwrite_file(file_contents, filename):
 error = ''
 file_contents = ''
 comm = ''
 if('username' in session):
     bucket = conn.get_bucket(config.buck_name_other, validate=True)
     folder = session['username'] + '/' + filename
     k = Key(bucket)
     k.key = filename
     k.set_contents_from_string(file_contents)
     return 'Overwrite Upload successfully'
 else:
     error = 'Session Time Out. Please login again.'
     return render_template('welcome.html', error = error)
     

#Secure Viewing function for img.
@application.route('/viewer', methods = ['GET', 'POST'])
def view_file():
 error = ''
 file_contents = ''
 comm = ''
 if('username' in session):
    f_list = ''
    folder = session['username'] + '/'
    bucket = conn.get_bucket(config.buck_name, validate=True)
    for key in bucket.list(prefix = folder):
        if key.name == folder:
            continue
        else:
            a,b = key.name.split("/")
            #print '****HERE****' + b
            key.open()
            file_contents = key.read()
            path = 'https://s3-us-west-2.amazonaws.com/mrs3test/' + key.name
            print path
            akey = bucket.get_key(key.name)
            comm = akey.get_metadata('meta1')
            if not comm:
                comm = '<No Comment Found>'
            f_list+= 'filename: ' + b + ' ' + ' || size: ' + str(key.size) + ' ' +  ' || last_modified: ' + str(key.last_modified) + ' || comment: ' + comm
            f_list+="<ul><li><a href = '/download_file/" + b + " " "'>Download</a></li><li><a href = '/delete_file/" + b + " " "'>Delete</a></li><li><a href = '/view_file/" + b + " " "'>Check it Out!!!</a></li><li><a href = '/move_file/" + b + " " "'>Move FIle to Other Bucket</a></li></ul>"
            f_list+='<a href = /view_file/' + b + ' ><img src="' + path + '"' +  'class="img-responsive" alt="Preview" width="50" height="50"></a>'
            f_list+="<br>"
    return Markup('''<!DOCTYPE html><html><head><!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

    <!-- Latest compiled and minified JavaScript -->
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script></head>
    <body>
    <h1>FileSpace</h1>
    <div id="latest_div" class="animate form">
    <form  action="viewer" method="POST">
    <input class ="btn btn-success" type="submit" value="Latest Upload First">
    </form>
    </div>
    <br>
    <div id="oldest_div" class="animate form">
    <form  action="view_old" method="POST">
    <input class ="btn btn-success" type="submit" value="Oldest Upload First">
    </form>
    </div>
    <br>
    <div id="exit_div" class="animate form">
    <form  action="exit" method="POST">
    <input class ="btn btn-success" type="submit" value="Dashboard">
    </form>
    </div>
    <div class="row">
    <div class="col-lg-6">
    <div class="input-group"><br><br><br><br><table><td>''' + f_list + '''</td></table></div></div></div></body></html>''')
 else:
     error = 'Session Time Out. Please login again.'
     return render_template('welcome.html', error = error)



##################Oldest Upload First#############################
@application.route('/view_old', methods = ['GET', 'POST'])
def view_old_file():
 error = ''
 file_contents = ''
 comm = ''
 if('username' in session):
    f_list = ''
    folder = session['username'] + '/'
    bucket = conn.get_bucket(config.buck_name, validate=True)
    for key in sorted(bucket.list(prefix = folder), key=lambda k: k.last_modified):
        if key.name == folder:
            continue
        else:
            a,b = key.name.split("/")
            #print '****HERE****' + b
            key.open()
            file_contents = key.read()
            path = 'https://s3-us-west-2.amazonaws.com/mrs3test/' + key.name
            akey = bucket.get_key(key.name)
            comm = akey.get_metadata('meta1')
            if not comm:
                comm = '<No Comment Found>'
            f_list+= 'filename: ' + b + ' ' + ' || size: ' + str(key.size) + ' ' +  ' || last_modified: ' + str(key.last_modified) + ' || comment: ' + comm
            f_list+="<ul><li><a href = '/download_file/" + b + " " "'>Download</a></li><li><a href = '/delete_file/" + b + " " "'>Delete</a></li><li><a href = '/view_file/" + b + " " "'>Check it Out!!!</a></li></ul>"
            f_list+='<a href = /view_file/' + b + ' ><img src="' + path + '"' +  'class="img-responsive" alt="Preview" width="50" height="50"></a>'
            f_list+="<br>"
    return Markup('''<!DOCTYPE html><html><head><!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

    <!-- Latest compiled and minified JavaScript -->
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script></head>
    <body>
    <h1>FileSpace</h1>
    <div id="latest_div" class="animate form">
    <form  action="viewer" method="POST">
    <input class ="btn btn-success" type="submit" value="Latest Upload First">
    </form>
    </div>
    <br>
    <div id="oldest_div" class="animate form">
    <form  action="view_old" method="POST">
    <input class ="btn btn-success" type="submit" value="Oldest Upload First">
    </form>
    </div>
    <br>
    <div id="exit_div" class="animate form">
    <form  action="exit" method="POST">
    <input class ="btn btn-success" type="submit" value="Dashboard">
    </form>
    </div>
    <div class="row">
    <div class="col-lg-6">
    <div class="input-group"><br><br><br><br><table><td>''' + f_list + '''</td></table></div></div></div></body></html>''')
 else:
     error = 'Session Time Out. Please login again.'
     return render_template('welcome.html', error = error)


##################################Secure Viewing function for other files. Fetching results of analysis.###################################################################
@application.route('/viewer_other', methods = ['GET', 'POST'])
def view_file_other():
 error = ''
 file_contents = ''
 comm = ''
 if('username' in session):
    f_list = ''
    folder = session['username'] + '/'
    bucket = conn.get_bucket(config.buck_name_other, validate=True)
    for key in bucket.list(prefix = folder):
        if key.name == folder:
            continue
        else:
            a,b = key.name.split("/")
            #print '****HERE****' + b
            key.open()
            file_contents = key.read()
            path = 'https://s3-us-west-2.amazonaws.com/mrs3test/' + key.name
            akey = bucket.get_key(key.name)
            comm = akey.get_metadata('meta1')
            if not comm:
                comm = '<No Comment Found>'
            f_list+= 'filename: ' + b + ' ' + ' || size: ' + str(key.size) + ' ' +  ' || last_modified: ' + str(key.last_modified) + ' || comment: ' + comm
            f_list+="<ul><li><a href = '/download_file/" + b + " " "'>Download</a></li><li><a href = '/delete_file/" + b + " " "'>Delete</a></li><li><a href = '/view_file/" + b + " " "'>Check it Out!!!</a></li></ul>"
            f_list+='<a href = /view_file/' + b + ' ><img src="' + path + '"' +  'class="img-responsive" alt="Preview" width="50" height="50"></a>'
            f_list+="<br>"
    return Markup('''<!DOCTYPE html><html><head><!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

    <!-- Latest compiled and minified JavaScript -->
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script></head>
    <body>
    <h1>FileSpace</h1>
    <div id="latest_div" class="animate form">
    <form  action="viewer_other" method="POST">
    <input class ="btn btn-success" type="submit" value="Latest Upload First">
    </form>
    </div>
    <br>
    <div id="oldest_div" class="animate form">
    <form  action="view_old_other" method="POST">
    <input class ="btn btn-success" type="submit" value="Oldest Upload First">
    </form>
    </div>
    <br>
    <div id="exit_div" class="animate form">
    <form  action="exit" method="POST">
    <input class ="btn btn-success" type="submit" value="Dashboard">
    </form>
    </div>
    <div class="row">
    <div class="col-lg-6">
    <div class="input-group"><br><br><br><br><table><td>''' + f_list + '''</td></table></div></div></div></body></html>''')
 else:
     error = 'Session Time Out. Please login again.'
     return render_template('welcome.html', error = error)



##################Oldest Upload First for other files###############################################################################################################################
@application.route('/view_old_other', methods = ['GET', 'POST'])
def view_old_file_other():
 error = ''
 file_contents = ''
 comm = ''
 if('username' in session):
    f_list = ''
    folder = session['username'] + '/'
    bucket = conn.get_bucket(config.buck_name_other, validate=True)
    for key in sorted(bucket.list(prefix = folder), key=lambda k: k.last_modified, reverse=True):
        if key.name == folder:
            continue
        else:
            a,b = key.name.split("/")
            #print '****HERE****' + b
            key.open()
            file_contents = key.read()
            path = 'https://s3-us-west-2.amazonaws.com/mrs3test/' + key.name
            akey = bucket.get_key(key.name)
            comm = akey.get_metadata('meta1')
            if not comm:
                comm = '<No Comment Found>'
            f_list+= 'filename: ' + b + ' ' + ' || size: ' + str(key.size) + ' ' +  ' || last_modified: ' + str(key.last_modified) + ' || comment: ' + comm
            f_list+="<ul><li><a href = '/download_file/" + b + " " "'>Download</a></li><li><a href = '/delete_file/" + b + " " "'>Delete</a></li><li><a href = '/view_file/" + b + " " "'>Check it Out!!!</a></li></ul>"
            f_list+='<a href = /view_file/' + b + ' ><img src="' + path + '"' +  'class="img-responsive" alt="Preview" width="50" height="50"></a>'
            f_list+="<br>"
    return Markup('''<!DOCTYPE html><html><head><!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

    <!-- Latest compiled and minified JavaScript -->
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script></head>
    <body>
    <h1>FileSpace</h1>
    <div id="latest_div_1" class="animate form">
    <form  action="viewer_other" method="POST">
    <input class ="btn btn-success" type="submit" value="Latest Upload First">
    </form>
    </div>
    <br>
    <div id="oldest_div_1" class="animate form">
    <form  action="view_old_other" method="POST">
    <input class ="btn btn-success" type="submit" value="Oldest Upload First">
    </form>
    </div>
    <br>
    <div id="exit_div" class="animate form">
    <form  action="exit" method="POST">
    <input class ="btn btn-success" type="submit" value="Dashboard">
    </form>
    </div>
    <div class="row">
    <div class="col-lg-6">
    <div class="input-group"><br><br><br><br><table><td>''' + f_list + '''</td></table></div></div></div></body></html>''')
 else:
     error = 'Session Time Out. Please login again.'
     return render_template('welcome.html', error = error)


@application.route('/download_file/<file_name>')
def download(file_name):
    error = ''
    file_contents = ''
    file_list = []
    version_list = []
    if('username' in session):
        folder = session['username'] + '/' + file_name
        a,b = file_name.split(".")
        if b == 'jpg' or b == 'jpeg' or b == 'png' or b == 'gif' or b == 'mp4':
            bucket = conn.get_bucket(config.buck_name, validate=True)
        else:
            bucket = conn.get_bucket(config.buck_name_other, validate=True)
        key = bucket.get_key(folder)
        key.open()
        file_contents = key.read()
        headers = {"Content-Disposition": "attachment; filename=%s" % file_name}
        return make_response((file_contents, headers))
    else:
        error = 'Session Time Out. Please login again.'
        return render_template('welcome.html', error = error)


@application.route('/delete_file/<file_name>')
def delete(file_name):
    error = ''
    file_contents = ''
    file_list = []
    version_list = []
    if('username' in session):
        folder = session['username'] + '/' + file_name
        a,b = file_name.split(".")
        if b == 'jpg' or b == 'jpeg' or b == 'png' or b == 'gif' or b == 'mp4':
            bucket = conn.get_bucket(config.buck_name, validate=True)
        else:
            bucket = conn.get_bucket(config.buck_name_other, validate=True)
        bucket.delete_key(folder)
        return 'Deleted selected file successfully.'
    else:
        error = 'Session Time Out. Please login again.'
        return render_template('welcome.html', error = error)


@application.route('/view_file/<file_name>')
def view(file_name):
    error = ''
    file_contents = ''
    file_list = []
    version_list = []
    if('username' in session):
        folder = session['username'] + '/' + file_name
        a,b = file_name.split(".")
        if b == 'jpg' or b == 'jpeg' or b == 'png' or b == 'gif' or b == 'mp4':
            bucket = conn.get_bucket(config.buck_name, validate=True)
            key = bucket.get_key(folder)
            key.open()
            path = 'https://s3-us-west-2.amazonaws.com/mrs3test/' + key.name
            file_contents = key.read()
            return render_template('view_img.html', image = path)
        else:
            bucket = conn.get_bucket(config.buck_name_other, validate=True)
            key = bucket.get_key(folder)
            key.open()
            file_contents = key.read()
            return render_template('render_results.html', result = (file_contents.decode('utf-8')))
            
    else:
        error = 'Session Time Out. Please login again.'
        return render_template('welcome.html', error = error)


####################Search on Comment###################
@application.route('/search_comment', methods=["GET","POST"])
def search_download():
    error = ''
    file_contents = ''
    file_list = []
    keys = []
    if('username' in session):
        if request.method == 'POST':
            comment  = request.form['com_search1']
        folder = session['username'] + '/'
        bucket = conn.get_bucket(config.buck_name, validate=True)
        for key in bucket.list(prefix = folder):
            akey = bucket.get_key(key.name)
            comm = akey.get_metadata('meta1')
            if comm:
                keys.append(akey.get_metadata('meta1'))
            else:
                keys.append('Not Present')
        print 'here************' + str(keys)
        #any(comment in s for s in keys)
        if comment in keys:
            for key in bucket.list(prefix = folder):
                bkey = bucket.get_key(key.name)
                if (comment == bkey.get_metadata('meta1')):
                    key.open()
                    file_contents = key.read()
                    a,b = key.name.split("/")
                    path = 'https://s3-us-west-2.amazonaws.com/mrs3test/' + key.name
                    return render_template('view_img.html', image = path
                else:
                    continue
        else:
            return 'No Image associated with the comment you entered. Try again.'
    else:
        error = 'Session Time Out. Please login again.'
        return render_template('welcome.html', error = error)

####################Add Comment###################
@application.route('/add_comment', methods=["GET","POST"])
def add_comment():
    error = ''
    file_contents = ''
    file_list = []
    keys = []
    if('username' in session):
        if request.method == 'POST':
            comment  = request.form['comment1']
            file_name  = request.form['file1']
        folder = session['username'] + '/'
        a,b = file_name.split(".")
        if b == 'jpg' or b == 'jpeg' or b == 'png' or b == 'gif' or b == 'mp4':
            bucket = conn.get_bucket(config.buck_name, validate=True)
        else:
            bucket = conn.get_bucket(config.buck_name_other, validate=True)
        for key in bucket.list(prefix = folder):
            a,b = key.name.split("/")
            file_list.append(b)
            akey = bucket.get_key(key.name)
            comm = akey.get_metadata('meta1')
            if comm:
                keys.append(akey.get_metadata('meta1'))
            else:
                keys.append('Not Present')
        print file_list
        print keys
        if (file_name in file_list):
            for key in bucket.list(prefix = folder):
                a,b = key.name.split("/")
                if b == file_name:
                    akey = bucket.get_key(key.name)
                    metadata = {'meta1':comment}
                    akey.copy(bucket, key.name, metadata, preserve_acl=True)
                    return 'Comment posted Successfully'
                else:
                    continue
        else:
            return 'File does not exist. Try again.'
    else:
        error = 'Session Time Out. Please login again.'
        return render_template('welcome.html', error = error)


##############DELETION BASED ON DATE##################
@application.route('/delete_time_date', methods=['GET', 'POST'])
def delete_time_date():
    error = ''
    now = datetime.datetime.now()
    count = 0
    if('username' in session):
        cont_name = session['username']
        if request.method == 'POST':
            deltime = request.form['delete1']
            del_uni = datetime.datetime.strptime((deltime.decode("utf-8")), '%Y %m %d')
        #bucket = conn.get_bucket(config.buck_name, validate=True)
        folder = session['username'] + '/'
        for bucket in conn.get_all_buckets():
            for key in bucket.list(prefix = folder):
                a,b = key.name.split("/")
                folder1 = session['username'] + '/' + b
                upload = datetime.datetime.strptime((key.last_modified.decode("utf-8")), '%Y-%m-%dT%H:%M:%S.%fZ')
                diff = now-upload
                if upload < del_uni:
                    bucket.delete_key(folder1)
                    count+=1
                else:
                    continue
        if count == 1 or count > 1:
            return 'All Files uploaded before' + ' ' + deltime + ' '  + ' deleted successfully.'
        else:
            return 'No Files before the entered time found. Try again'
    else:
        error = 'Session Time Out. Please login again.'
        return render_template('welcome.html', error = error)


##############DELETION BASED ON TIME##################
@application.route('/delete_time', methods=['GET', 'POST'])
def delete_time():
    error = ''
    count = 0
    now = datetime.datetime.now()
    if('username' in session):
        cont_name = session['username']
        if request.method == 'POST':
            deltime = request.form['delete1']
            del_uni = datetime.datetime.strptime((deltime.decode("utf-8")), '%M')
        #bucket = conn.get_bucket(config.buck_name, validate=True)
        folder = session['username'] + '/'
        for bucket in conn.get_all_buckets():
            for key in bucket.list(prefix = folder):
                a,b = key.name.split("/")
                folder1 = session['username'] + '/' + b
                upload = datetime.datetime.strptime((key.last_modified.decode("utf-8")), '%Y-%m-%dT%H:%M:%S.%fZ')
                diff = now-upload
                if diff > datetime.timedelta(minutes=int(deltime)):
                    bucket.delete_key(folder1)
                    count+=1
                    return 'All Files uploaded before' + ' ' + deltime + ' '  + ' minutes deleted successfully.'
                else:
                    continue
        if count == 1 or count > 1:
            return 'All Files uploaded before' + ' ' + deltime + ' '  + ' minutes deleted successfully.'
        else:
            return 'No Files before the entered time found. Try again'
    else:
        error = 'Session Time Out. Please login again.'
        return render_template('welcome.html', error = error)

##############Move around files to other folders##################
@application.route('/move_file/<file_name>')
def move_file(file_name):
    error = ''
    count = 0
    now = datetime.datetime.now()
    if('username' in session):
        a,b = file_name.split(".")
        folder = session['username'] + '/'
        if b == 'jpg' or b == 'jpeg' or b == 'png' or b == 'gif' or b == 'mp4':
            src = conn.get_bucket(config.buck_name, validate=True)
            dst = conn.get_bucket('cloud3test', validate=True)
            for k in src.list(prefix = folder):
                a,b = k.name.split("/")
                if(b == file_name):
                    dst.copy_key(k.key, src.name, k.key)
                    k.delete()
                    return 'Selected File moved from Image Bucket to Other Bucket'
                else:
                    continue
        else:
            src = conn.get_bucket(config.buck_name_other, validate=True)
            dst = conn.get_bucket(config.buck_name, validate=True)
            for k in src.list(prefix = folder):
                a,b = k.name.split("/")
                if(b == file_name):
                    dst.copy_key(k.key, src.name, k.key)
                    k.delete()
                    return 'Selected File moved from Image Bucket to Other Bucket'
                else:
                    continue  
    else:
        error = 'Session Time Out. Please login again.'
        return render_template('welcome.html', error = error)


##############Exit from view##################
@application.route('/exit', methods=['GET', 'POST'])
def exit_view():
    error = ''
    count = 0
    now = datetime.datetime.now()
    if('username' in session):
        return render_template('upload_db.html', username = session['username'])
    else:
        error = 'Session Time Out. Please login again.'
        return render_template('welcome.html', error = error)
            
#Logout function with cache clearance. 
@application.route('/logout', methods=['GET', 'POST'])
def logout():
 if 'username' in session:
    session.pop('username', None)
    session.clear()
    session["__invalidate__"] = True
    #print("****** logout" + session['username'])
    return redirect(url_for('home'))


if __name__ == '__main__':
    application.secret_key = config.secret_key_file
    application.run(host='0.0.0.0', debug=True)
