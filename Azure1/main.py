import os
from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename
import pandas as pd
import sqlite3 as sql
import random
import bmemcached
from time import time
"""
	Name : Balaji Paiyur Mohan
	UTA ID: 1001576836

"""
app = Flask(__name__)
#port = int(os.getenv('PORT', 8000))

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set('csv')

TTL = 25
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'cloudydreams'
 
@app.route("/")
def home():
	return render_template('index.html')

# For render_template pass in name of template and any variables needed
@app.route("/upload", methods=['GET', 'POST'])
def upload():
	if request.method == 'POST':
		csvfile = request.files['csvfile']
		file_name = secure_filename(request.files['csvfile'].filename).strip()
		request.files['csvfile'].save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
		#conn = ibm_db.connect("DATABASE=BLUDB ;HOSTNAME=dashdb-txn-sbox-yp-dal09-04.services.dal.bluemix.net;PORT=50000;UID=nqf07957;PWD=wcg9ptq@c9kst5m0;","","")
		conn = sql.connect('earth.db')
		df = pd.read_csv(app.config['UPLOAD_FOLDER'] + file_name)
		df.to_sql('Data', conn, if_exists='replace', index=True)
		#ibm_db.close(conn)
		conn.close()
		#flash('file uploaded successfully')
	return render_template('upload.html') 
	
@app.route("/view_data")
def view_data():
	"""conn = ibm_db.connect("DATABASE=BLUDB ;HOSTNAME=dashdb-txn-sbox-yp-dal09-04.services.dal.bluemix.net;PORT=50000;UID=nqf07957;PWD=wcg9ptq@c9kst5m0;","","")
	query = "Select * from EQ"
	rows = []
	ibm_db.execute(query)
	res = ibm_db.fetch_assoc(query)
	while res is True:
		rows.append(result.copy())
		res = ibm_db.fetch_assoc(query)
	ibm_db.close(conn)"""
	conn = sql.connect('earth.db')
	curs = conn.cursor()
	curs.execute("Select * from Data")
	rows = curs.fetchall()
	conn.close()
	return render_template('view_data.html', data=rows)	
	
@app.route('/query_gen')
def query_gen():
	return render_template('query_gen.html')
	
@app.route('/query_gen_success', methods=['GET', 'POST'])
def query_gen_success():
	#conn = ibm_db.connect("DATABASE=BLUDB ;HOSTNAME=dashdb-txn-sbox-yp-dal09-04.services.dal.bluemix.net;PORT=50000;UID=nqf07957;PWD=wcg9ptq@c9kst5m0;","","")
	conn = sql.connect('earth.db')
	curs = conn.cursor()
	num = int(request.form['query'])
	start = time()
	par = 0
	rows = []
	for i in range(1,num):
		par = random.uniform(0.5,7.5)
		query = "Select * from Data where mag >= " + str(par)	
		curs.execute(query)
		rows = curs.fetchall()
		"""ibm_db.execute(query)
		res = ibm_db.fetch_assoc(query)
		while res is True:
			rows.append(result.copy())
			res = ibm_db.fetch_assoc(query)"""
	stop = time()
	exec_time = stop - start
	#ibm_db.close(conn)
	conn.close()
	return render_template('query_gen_success.html', data = rows, exe = exec_time)

@app.route('/cached_query')
def cached_query():
    return render_template('cached_query.html')
	
@app.route('/cached_query_success', methods=['GET', 'POST'])
def cached_query_success():
	#conn = ibm_db.connect("DATABASE=BLUDB ;HOSTNAME=dashdb-txn-sbox-yp-dal09-04.services.dal.bluemix.net;PORT=50000;UID=nqf07957;PWD=wcg9ptq@c9kst5m0;","","")
	conn = sql.connect('earth.db')
	curs = conn.cursor()
	num = int(request.form['query'])	
	par = 0
	#con = memcache.Client(['127.0.0.1:11211'],debug=0)
	con =  bmemcached.Client('memcached-10490.c15.us-east-1-2.ec2.cloud.redislabs.com:10490', 'mc-pPmcN', 'p5gtthU1jhq99z0Q2VmYN4HbUk3PwlXM')
	#print(num)
	data = []
	lists = []
	start1 = time()
	for i in range(1,num):
		par = round(random.uniform(0.5,7.5),1)
		query = "Select * from Data where mag >= " + str(par)
		key = str(par)
		r = con.get(key)
		if r:
			data.append('cached')
			lists.append(r)
		else:
			data.append('not cached')
			#start1 = time()
			#stop1 = time()
			#s = time()
			#ibm_db.execute(query)
			curs.execute(query)
			#print(time()-s,i)
			#s = time()
			rows = curs.fetchall()
			lists.append(rows)
			# res = ibm_db.fetch_assoc(query)
			# while res is True:
				# rows.append(result.copy())
				# res = ibm_db.fetch_assoc(query)
			#print(time()-s,i)
			#s = time()
			con.set(key,rows,TTL)
			#print(time()-s,i)
	#ibm_db.close(conn)
	stop1 = time()
	exec_time = stop1 - start1
	conn.close()
	return render_template('cached_query_success.html', zip= zip(data, lists), exe = exec_time)

@app.route('/restrict')
def restrict():
	return render_template('restrict.html')
	
@app.route('/restrict_success', methods=['GET', 'POST'])
def restrict_success():
	conn = sql.connect('earth.db')
	curs = conn.cursor()
	start2 = time()
	curs.execute("Select * from Data where ? = ?",(request.form['par'],request.form['value']))
	rows = curs.fetchall()
	stop2 = time()
	exec_time2 = stop2 - start2
	conn.close()
	count = len(rows)
	return render_template('restrict_success.html', data = rows, exe = exec_time2)

if __name__ == "__main__":
	app.run(debug=True)
    #app.run(host='0.0.0.0', port=port)
