import os
from datetime import datetime
from flask import Flask,render_template,request,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
from werkzeug.security import generate_password_hash,check_password_hash
app=Flask(__name__); app.config['SECRET_KEY']=os.getenv('SECRET_KEY','change-me'); app.config['SQLALCHEMY_DATABASE_URI']=os.getenv('DATABASE_URL','sqlite:///project_monitoring.db'); db=SQLAlchemy(app); lm=LoginManager(app); lm.login_view='login'
class User(UserMixin,db.Model):
 id=db.Column(db.Integer,primary_key=True); username=db.Column(db.String(80),unique=True); name=db.Column(db.String(120)); password=db.Column(db.String(255)); role=db.Column(db.String(30))
 def setpw(self,p): self.password=generate_password_hash(p)
 def check(self,p): return check_password_hash(self.password,p)
class Project(db.Model):
 id=db.Column(db.Integer,primary_key=True); code=db.Column(db.String(30),unique=True); name=db.Column(db.String(180)); manager=db.Column(db.String(120)); start=db.Column(db.Date); target=db.Column(db.Date); budget=db.Column(db.Float,default=0); planned=db.Column(db.Float,default=0); actual=db.Column(db.Float,default=0); status=db.Column(db.String(30),default='On Track'); owner_id=db.Column(db.Integer,db.ForeignKey('user.id'))
class PIC(db.Model):
 id=db.Column(db.Integer,primary_key=True); project_id=db.Column(db.Integer,db.ForeignKey('project.id')); user_id=db.Column(db.Integer,db.ForeignKey('user.id')); responsibility=db.Column(db.String(150)); user=db.relationship('User')
class Risk(db.Model):
 id=db.Column(db.Integer,primary_key=True); project_id=db.Column(db.Integer,db.ForeignKey('project.id')); description=db.Column(db.String(300)); owner=db.Column(db.String(120)); probability=db.Column(db.Integer,default=3); impact=db.Column(db.Integer,default=3); mitigation=db.Column(db.Text); due=db.Column(db.Date); status=db.Column(db.String(30),default='Open')
class Issue(db.Model):
 id=db.Column(db.Integer,primary_key=True); project_id=db.Column(db.Integer,db.ForeignKey('project.id')); description=db.Column(db.String(300)); owner=db.Column(db.String(120)); priority=db.Column(db.String(20),default='Medium'); due=db.Column(db.Date); status=db.Column(db.String(30),default='Open')
class Action(db.Model):
 id=db.Column(db.Integer,primary_key=True); project_id=db.Column(db.Integer,db.ForeignKey('project.id')); action=db.Column(db.String(300)); pic=db.Column(db.String(120)); due=db.Column(db.Date); progress=db.Column(db.Integer,default=0); status=db.Column(db.String(30),default='Open')
Project.risks=db.relationship('Risk',cascade='all,delete-orphan'); Project.issues=db.relationship('Issue',cascade='all,delete-orphan'); Project.actions=db.relationship('Action',cascade='all,delete-orphan'); Project.pics=db.relationship('PIC',cascade='all,delete-orphan')
@lm.user_loader
def load(uid): return db.session.get(User,int(uid))
@app.template_filter('idr')
def idr(v): return 'Rp {:,.0f}'.format(v or 0).replace(',','.')
def d(x): return datetime.strptime(x,'%Y-%m-%d').date() if x else None
def edit(p): return current_user.role in ('admin','project_user') or (current_user.role=='executor' and any(x.user_id==current_user.id for x in p.pics))
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  u=User.query.filter_by(username=request.form['username']).first()
  if u and u.check(request.form['password']): login_user(u); return redirect('/')
  flash('Login gagal','danger')
 return render_template('login.html')
@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect('/login')
@app.route('/')
@login_required
def dashboard(): return render_template('dashboard.html',projects=Project.query.all(),risks=Risk.query.filter_by(status='Open').count(),issues=Issue.query.filter_by(status='Open').count(),actions=Action.query.filter(Action.status!='Closed').count())
@app.route('/projects')
@login_required
def projects(): return render_template('projects.html',projects=Project.query.all())
@app.route('/projects/new',methods=['GET','POST'])
@login_required
def new():
 if current_user.role not in ('admin','project_user'): return 'Forbidden',403
 if request.method=='POST':
  p=Project(code=request.form['code'],name=request.form['name'],manager=request.form.get('manager'),start=d(request.form.get('start')),target=d(request.form.get('target')),budget=float(request.form.get('budget') or 0),planned=float(request.form.get('planned') or 0),actual=float(request.form.get('actual') or 0),status=request.form.get('status','On Track'),owner_id=current_user.id); db.session.add(p); db.session.commit(); return redirect(url_for('detail',pid=p.id))
 return render_template('new.html')
@app.route('/projects/<int:pid>')
@login_required
def detail(pid): return render_template('detail.html',p=db.get_or_404(Project,pid),users=User.query.all(),can=edit(db.get_or_404(Project,pid)))
@app.route('/projects/<int:pid>/update',methods=['POST'])
@login_required
def update(pid):
 p=db.get_or_404(Project,pid)
 if not edit(p): return 'Forbidden',403
 p.planned=float(request.form['planned']); p.actual=float(request.form['actual']); p.status=request.form['status']; db.session.commit(); return redirect(url_for('detail',pid=pid))
def add(model,pid,**kw):
 p=db.get_or_404(Project,pid)
 if not edit(p): return 'Forbidden',403
 db.session.add(model(project_id=pid,**kw)); db.session.commit(); return redirect(url_for('detail',pid=pid))
@app.route('/projects/<int:pid>/risk',methods=['POST'])
def risk(pid): return add(Risk,pid,description=request.form['description'],owner=request.form.get('owner'),probability=int(request.form.get('probability',3)),impact=int(request.form.get('impact',3)),mitigation=request.form.get('mitigation'),due=d(request.form.get('due')))
@app.route('/projects/<int:pid>/issue',methods=['POST'])
def issue(pid): return add(Issue,pid,description=request.form['description'],owner=request.form.get('owner'),priority=request.form.get('priority','Medium'),due=d(request.form.get('due')))
@app.route('/projects/<int:pid>/action',methods=['POST'])
def action(pid): return add(Action,pid,action=request.form['action'],pic=request.form.get('pic'),due=d(request.form.get('due')),progress=int(request.form.get('progress',0)))
@app.route('/projects/<int:pid>/pic',methods=['POST'])
def pic(pid): return add(PIC,pid,user_id=int(request.form['user_id']),responsibility=request.form.get('responsibility'))
@app.route('/action/<int:aid>',methods=['POST'])
def action_update(aid):
 a=db.get_or_404(Action,aid); p=db.get_or_404(Project,a.project_id)
 if not edit(p): return 'Forbidden',403
 a.progress=int(request.form['progress']); a.status=request.form['status']; db.session.commit(); return redirect(url_for('detail',pid=p.id))
@app.route('/admin/users',methods=['GET','POST'])
@login_required
def users():
 if current_user.role!='admin': return 'Forbidden',403
 if request.method=='POST': u=User(username=request.form['username'],name=request.form['name'],role=request.form['role']); u.setpw(request.form['password']); db.session.add(u); db.session.commit()
 return render_template('users.html',users=User.query.all())
with app.app_context():
 db.create_all()
 if not User.query.first():
  for un,n,r,pw in [('admin','Administrator','admin','Admin123!'),('project','Project User','project_user','Project123!'),('executor','Project Executor','executor','Executor123!')]:
   u=User(username=un,name=n,role=r); u.setpw(pw); db.session.add(u)
  db.session.commit()
  p=Project(code='PRJ-001',name='Facility Improvement Project',manager='Project Manager',target=d('2026-12-20'),budget=10000000000,planned=65,actual=58,status='At Risk',owner_id=2); db.session.add(p); db.session.commit(); db.session.add(PIC(project_id=p.id,user_id=3,responsibility='Execution')); db.session.add(Risk(project_id=p.id,description='Long lead equipment',owner='Procurement',probability=4,impact=5,mitigation='Expedite vendor')); db.session.add(Issue(project_id=p.id,description='Document approval delayed',owner='Engineering',priority='High')); db.session.add(Action(project_id=p.id,action='Finalize expediting plan',pic='Project Executor',progress=50)); db.session.commit()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)))
