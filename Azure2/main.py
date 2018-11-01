import os
from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib as mp
mp.use('Agg')
import matplotlib.pyplot as plotter
#from matplotlib import cm
import sqlite3 as sql
"""
	Name : Balaji Paiyur Mohan
	UTA ID: 1001576836

"""
app = Flask(__name__)
port = int(os.getenv('PORT', 8000))

scaler = StandardScaler()
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set('xls')

#colors = np.random.rand(50)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'cloud_secret'

@app.route("/")
def home():
	return render_template('index.html')

# For render_template pass in name of template and any variables needed
@app.route("/upload", methods=['GET', 'POST'])
def upload():
	if request.method == 'POST':
		xlsfile = request.files['xlsfile']
		file_name = secure_filename(request.files['xlsfile'].filename)
		request.files['xlsfile'].save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
		conn = sql.connect('titanic.db')
		df = pd.read_csv(app.config['UPLOAD_FOLDER'] + file_name , na_values='NaN')
		df.to_sql('people', conn, if_exists='replace', index=True)
		conn.close()
		flash('file uploaded successfully')
	return render_template('upload.html') 
	
@app.route("/view_data")
def view_data():
	conn = sql.connect('titanic.db')
	curs = conn.cursor()
	curs.execute("Select * from people")
	rows = curs.fetchall()
	conn.close()
	return render_template('view_data.html', data=rows)	

@app.route('/cluster')
def cluster():
    return render_template('cluster.html')

@app.route('/cluster_success', methods=['GET', 'POST'])
def cluster_success():
	conn = sql.connect('titanic.db')
	curs = conn.cursor()
	curs.execute("SELECT age, fare price FROM people")
	rows = curs.fetchall()
	df_unscaled = pd.DataFrame(rows)
	df_unscaled = df_unscaled.dropna(axis=0, how='any')
	df = scaler.fit_transform(df_unscaled)
	df = pd.DataFrame(df)
	plotter.title('Clustering of people\n', fontsize=15)
	k_clusters = request.form['cluster']
	#count no of NaN isnull().sum()
	kmeans= KMeans(n_clusters=int(k_clusters)).fit(df)
	#plotter.figure(figsize=(900/150, 900/150), dpi=150)
	plotter.xlabel('Age', fontsize=14)
	plotter.ylabel('Fare price', fontsize=14)
	plotter.scatter(df.iloc[:,0], df.iloc[:,1], c=[i.astype(float) for i in kmeans.labels_])#, label = ["cluster"+str(i) for i in range(1,int(k_clusters))])
	centroids = kmeans.cluster_centers_
	centroid_pts = kmeans.labels_
	df2= pd.DataFrame(centroids)	
	count1 = df2.shape[0]
	count2 = df.dropna(axis=0, how='any').shape[0]
	plotter.scatter(df2.iloc[:,0], df2.iloc[:,1], c='r',marker = "^", label ='Centroids')
	#plotter.legend(loc="upper right")
	plotter.savefig('static\clusterplot.jpg')
	plotter.clf()
	count = 0
	#count clusters
	counter = {}
	for i in range(0,int(k_clusters)):
		for j in centroid_pts:
			if j == i:
				count=count+1
		counter[i] = count
		count=0
	#distance
	distance ={}
	for i in range(0,int(k_clusters)):
		for j in range(i,int(k_clusters)):
			if i != j:
				dist = np.linalg.norm(centroids[i]-centroids[j])
				key = '('+ str(i) +',' + str(j) +')'
				distance[str(key)] = dist
	#elbow
	distortions = {}
	c_range = range(2,10)
	#silhouette score
	score_stats = {}
	for i in c_range:
		clust = KMeans(i).fit(pd.DataFrame(rows).dropna(axis=0, how='any'))
		distortions[i] = clust.inertia_	
		k_means = KMeans(i).fit(pd.DataFrame(rows).dropna(axis=0, how='any'))
		silhouette_avg_score = silhouette_score(pd.DataFrame(rows).dropna(axis=0, how='any'), clust.labels_)
		score_stats[i] = "The average silhouette score value is : "+ str(silhouette_avg_score)
	plotter.plot(distortions.keys(),distortions.values())
	plotter.xlabel("Number of clusters")
	plotter.ylabel("Explained Variance")
	plotter.title("Elbow method results")
	plotter.savefig('static\elbow.jpg')
	plotter.clf()
	
	return render_template('cluster_success.html',zip = zip(centroids, centroid_pts), count1 = count1, count2 = count2,counter = counter,score_stats = score_stats, distance = distance)
	
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=port)


