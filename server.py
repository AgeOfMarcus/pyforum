#!/usr/bin/python3

from flask import Flask, jsonify, request, redirect
import uuid, sqlite3, os, hashlib, base64

##### CHANGEME #####

salt = "saltyboi" # This is the salt used to hash passwords

##### CHANGEME #####

# Required functions
def cursor(cmd,db="pyforum.db"):
	with sqlite3.connect(db) as db:
		res = db.cursor().execute(cmd).fetchall()
		db.commit()
	return res
def comp_lst(lst):
	res = []
	for i in lst: res.append(i[0])
	return res
def select(cmd): return comp_lst(cursor(cmd))
def sha256(string): return hashlib.sha256(string.encode()).hexdigest()
def bencode(string): return base64.b64encode(string.encode()).decode()
def bdecode(string): return base64.b64decode(string).decode()
def passencode(passwd): return sha256(bencode(sha256(passwd)+sha256(salt))) # Just blast it with stuff

# Setting up the db
cursor("CREATE TABLE IF NOT EXISTS keys \
	(ID INTEGER PRIMARY KEY AUTOINCREMENT, \
	USER TEXT NOT NULL, \
	KEY TEXT NOT NULL);")
cursor("CREATE TABLE IF NOT EXISTS posts \
	(ID INTEGER PRIMARY KEY AUTOINCREMENT, \
	USER TEXT NOT NULL, \
	TITLE TEXT NOT NULL, \
	BODY TEXT);")
cursor("CREATE TABLE IF NOT EXISTS comments \
	(ID INTEGER PRIMARY KEY AUTOINCREMENT, \
	POST INTEGER NOT NULL, \
	USER TEXT NOT NULL, \
	BODY TEXT NOT NULL);")

def register_user(username,passwd):
	if not cursor("SELECT ID FROM keys WHERE USER='%s'" % username) == []:
		return False
	passwd = passencode(passwd)
	cursor("INSERT INTO keys (USER,KEY) VALUES ('%s','%s');" % (username,passwd))
	return True

def create_post(user,key,title,body):
	key = passencode(key)
	if cursor("SELECT ID FROM keys WHERE USER='%s' AND KEY='%s'" % (user,key)) == []:
		return False
	cursor("INSERT INTO posts (USER, TITLE, BODY) VALUES ('%s','%s','%s');" % (user,title,body))
	return True

def create_comment(user,key,post_id,body):
	key = passencode(key)
	if cursor("SELECT ID FROM keys WHERE USER='%s' AND KEY='%s'" % (user,key)) == []:
		return False
	if cursor("SELECT TITLE FROM posts WHERE ID=%s" % post_id) == []:
		return False
	cursor("INSERT INTO comments (POST,USER,BODY) VALUES (%s,'%s','%s');" % (post_id,user,body))
	return True

#TODO: Create functions for deleting posts/comments and editing(copy text -> send text -> delete orig -> get new)

def get_posts():
	all_posts = cursor("SELECT ID,USER,TITLE,BODY FROM posts")
	posts = {}
	for i in all_posts:
		posts[i[0]] = {'user':i[1],'title':i[2],'body':i[3],'comments':[]}
	comments = cursor("SELECT POST,USER,BODY FROM comments")
	for i in comments:
		posts[i[0]]['comments'].append({'user':i[1],'body':i[2]})
	return posts


app = Flask(__name__)

@app.route("/register",methods=['POST'])
def app_register():
	try:
		user = request.form['username']
		passwd = request.form['password']
		res = register_user(user,passwd)
		if res == False:
			return jsonify({"error":"user already exists"}), 200
		return jsonify({"ok":True}), 200
	except Exception as e:
		print(e)
		return "", 400

@app.route("/post",methods=['POST'])
def app_post():
	try:
		user = request.form['username']
		key = request.form['password']
		title = request.form['title']
		body = request.form['body']
		res = create_post(user,key,title,body)
		if res:
			return jsonify({"ok":True}), 200
		return jsonify({"ok":False,"error":"invalid key"}), 200
	except Exception as e:
		print(e)
		return "", 400

@app.route("/comment",methods=['POST'])
def app_comment():
	user = request.form['username']
	key = request.form['password']
	post_id = request['form.post_id']
	body = request.form['body']
	res = create_comment(user,key,post_id,body)
	if res == False:
		return jsonify({"ok":False,"error":"invalid key or post_id"}), 200
	return jsonoify({"ok":True}), 200

@app.route("/get/posts/<sort>",methods=['GET'])
def app_get_posts(sort):
	posts = get_posts()
	res = {}
	for i in posts:
		if posts[i]['user'] == sort or sort == "all":
			res[i] = posts[i]
	return jsonify({'posts':res}), 200

def main(args={'host':"0.0.0.0",'port':5000}):
	app.run(host=args['host'],port=args['port'])
if __name__ == "__main__":
	main() # implement args later