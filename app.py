from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os
app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY','cambiar-clave')
DB=os.path.join(os.path.dirname(__file__),'autoflow.db')

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS vehicles(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,year INTEGER,km INTEGER,currency TEXT,cost REAL,published REAL,minimum REAL,status TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT,vehicle TEXT,stage TEXT,next_contact TEXT,seller TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS trips(id INTEGER PRIMARY KEY AUTOINCREMENT,truck TEXT,driver TEXT,client TEXT,origin TEXT,destination TEXT,tons REAL,km REAL,liters REAL,billing REAL,tolls REAL,other_cost REAL,due_date TEXT,collected INTEGER,trip_date TEXT);
    CREATE TABLE IF NOT EXISTS cash(id INTEGER PRIMARY KEY AUTOINCREMENT,area TEXT,kind TEXT,concept TEXT,amount REAL,movement_date TEXT);
    ''')
    if c.execute('SELECT COUNT(*) n FROM vehicles').fetchone()['n']==0:
        rows=[
('EcoSport 2.0 Titanium',2014,170000,'ARS',12000000,15000000,13500000,'Vender','1 año en stock'),
('Suran Trendline 1.6',2015,190000,'ARS',9900000,14500000,13000000,'Vender','2 años en stock'),
('Gol Trend Base 1.6',2016,None,'ARS',9000000,13000000,12000000,'Vender','2 años en stock'),
('Fiat Palio Attractive 1.4',2017,100000,'ARS',12500000,15500000,14500000,'Trabajar','3 meses'),
('Bora TDI 1.9',2011,200000,'ARS',11000000,13500000,12500000,'Acelerar','6 meses'),
('Focus 2.0 SE Automático',2016,115000,'ARS',15900000,18500000,17800000,'Mantener','2 meses'),
('Duster 1.6 Privilege',2014,170000,'ARS',12000000,15000000,14000000,'Trabajar','3 meses'),
('Partner HDI',2011,180000,'ARS',10000000,11000000,10500000,'Acelerar','3 meses'),
('Logan 1.6 Nafta/GNC',2012,240000,'ARS',5500000,8900000,8000000,'Fuerte','10 días'),
('Vento 2.5 Nafta/GNC',2007,220000,'ARS',10000000,14000000,12500000,'Trabajar','3 meses'),
('Amarok V6 Extreme',2021,123000,'USD',30000,40000,35000,'Uso particular',''),
('Golf Highline',2017,100000,'USD',19200,24000,22000,'Uso particular',''),
('Passat TSI',2011,180000,'ARS',10000000,13500000,12000000,'Lanzar','1 año en taller'),
('Honda Tornado 250',2020,None,'ARS',6000000,7500000,7000000,'Vender','2 años'),
('Yamaha 150cc',2024,None,'ARS',5000000,6500000,5700000,'Vender','6 meses'),
('Beta 110',2025,None,'ARS',1000000,1500000,1400000,'Mantener','2 meses')]
        c.executemany('INSERT INTO vehicles(name,year,km,currency,cost,published,minimum,status,notes) VALUES(?,?,?,?,?,?,?,?,?)',rows)
    c.commit(); c.close()

@app.before_request
def setup(): init_db()

def auth(): return session.get('user')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form.get('user')==os.environ.get('AUTOFLOW_USER','fede') and request.form.get('password')==os.environ.get('AUTOFLOW_PASS','bianchi2026'):
            session['user']=request.form.get('user'); return redirect(url_for('dashboard'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if not auth(): return redirect(url_for('login'))
    c=db(); cars=c.execute('SELECT COUNT(*) n FROM vehicles').fetchone()['n']; clients=c.execute("SELECT COUNT(*) n FROM clients WHERE COALESCE(stage,'')!='Vendido'").fetchone()['n']; trips=c.execute("SELECT COUNT(*) n FROM trips WHERE strftime('%Y-%m',trip_date)=strftime('%Y-%m','now')").fetchone()['n']; rec=c.execute('SELECT COALESCE(SUM(billing),0) s FROM trips WHERE COALESCE(collected,0)=0').fetchone()['s']; alerts=c.execute("SELECT * FROM vehicles WHERE status IN ('Vender','Acelerar')").fetchall(); return render_template('dashboard.html',cars=cars,clients=clients,trips=trips,rec=rec,alerts=alerts)

@app.route('/stock',methods=['GET','POST'])
def stock():
    if not auth(): return redirect(url_for('login'))
    c=db()
    if request.method=='POST':
        f=request.form; c.execute('INSERT INTO vehicles(name,year,km,currency,cost,published,minimum,status,notes) VALUES(?,?,?,?,?,?,?,?,?)',(f['name'],f.get('year') or None,f.get('km') or None,f.get('currency','ARS'),f.get('cost') or 0,f.get('published') or 0,f.get('minimum') or 0,f.get('status','Activo'),f.get('notes',''))); c.commit(); return redirect(url_for('stock'))
    return render_template('stock.html',items=c.execute('SELECT * FROM vehicles ORDER BY id DESC').fetchall())

@app.route('/clientes',methods=['GET','POST'])
def clientes():
    if not auth(): return redirect(url_for('login'))
    c=db()
    if request.method=='POST':
        f=request.form; c.execute('INSERT INTO clients(name,phone,vehicle,stage,next_contact,seller,notes) VALUES(?,?,?,?,?,?,?)',(f['name'],f.get('phone',''),f.get('vehicle',''),f.get('stage','Nuevo'),f.get('next_contact',''),f.get('seller','Federico'),f.get('notes',''))); c.commit(); return redirect(url_for('clientes'))
    return render_template('clientes.html',items=c.execute('SELECT * FROM clients ORDER BY id DESC').fetchall())

@app.route('/camiones',methods=['GET','POST'])
def camiones():
    if not auth(): return redirect(url_for('login'))
    c=db()
    if request.method=='POST':
        f=request.form; c.execute('INSERT INTO trips(truck,driver,client,origin,destination,tons,km,liters,billing,tolls,other_cost,due_date,collected,trip_date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(f.get('truck'),f.get('driver'),f.get('client'),f.get('origin'),f.get('destination'),f.get('tons') or 0,f.get('km') or 0,f.get('liters') or 0,f.get('billing') or 0,f.get('tolls') or 0,f.get('other_cost') or 0,f.get('due_date'),1 if f.get('collected')=='on' else 0,f.get('trip_date'))); c.commit(); return redirect(url_for('camiones'))
    return render_template('camiones.html',items=c.execute('SELECT * FROM trips ORDER BY id DESC').fetchall())

@app.route('/caja',methods=['GET','POST'])
def caja():
    if not auth(): return redirect(url_for('login'))
    c=db()
    if request.method=='POST':
        f=request.form; c.execute('INSERT INTO cash(area,kind,concept,amount,movement_date) VALUES(?,?,?,?,?)',(f.get('area'),f.get('kind'),f.get('concept'),f.get('amount') or 0,f.get('movement_date'))); c.commit(); return redirect(url_for('caja'))
    totals=c.execute("SELECT area,SUM(CASE WHEN kind='Ingreso' THEN amount ELSE -amount END) balance FROM cash GROUP BY area").fetchall(); items=c.execute('SELECT * FROM cash ORDER BY movement_date DESC,id DESC').fetchall(); return render_template('caja.html',totals=totals,items=items)

if __name__=='__main__':
    init_db(); app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=True)
