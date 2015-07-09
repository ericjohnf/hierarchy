from app import app
from sqlalchemy.sql import text
from flask import render_template, request, redirect, url_for, session, jsonify, flash

from flask_wtf import Form
from wtforms.validators import DataRequired
from wtforms.fields import TextField, TextAreaField, PasswordField, BooleanField, RadioField, HiddenField, SelectField

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash("error", error)

def reports_to(node,accu):
    query = "SELECT * from nodes where reports_to=:nid"
    row = app.engine.execute(text(query),nid=node['id'])
    # accu[node['name']] = []
    accu[node['name']] = {'job_title':node['job_title'],'id':node['id'],'children':[]}
    
    if not row:
        pass
    else:
        for child in row:
            # accu[node['name']].append(reports_to(child,{}))
            accu[node['name']]['children'].append(reports_to(child,{}))

    return accu

def reports_to_ids(node,accu):
    accu.append(node['id'])
  
    query = "SELECT * from nodes where reports_to=:nid"
    row = app.engine.execute(text(query),nid=node['id'])

    if not row:
        pass
    else:
        for child in row:
            accu.extend(reports_to_ids(child,[]))

    return accu
    
@app.route('/',methods=['GET'])
@app.route('/index',methods=['GET'])
def hierarchy():
    # the root answers to no one
    query = "SELECT * FROM nodes where reports_to is NULL;"
    row = app.engine.execute(query).fetchone()
    
    if row == None:
        flash('error','You must have a CEO')
        return redirect(url_for('add'))
        
    node = dict(row)
    hierarchy = reports_to(node,{})  
    
    query = """SELECT * from nodes"""
    nodes = app.engine.execute(text(query))
    choices = [(g['id'], g['name'],g['job_title']) for g in nodes]
    
    return render_template('hierarchy.html',hierarchy=hierarchy,choices=choices)

@app.route('/add',methods=['GET'])
def add():
    form = AddUserForm()
    
    query = """SELECT * from nodes"""
    nodes = app.engine.execute(text(query))
    choices = [(g['id'], g['name']) for g in nodes]
    choices.insert(0, (0,'No one'))
    
    return render_template('add.html',form=form,choices=choices)

@app.route('/new',methods=['POST'])
def new():
    form = AddUserForm()
    if not form.validate_on_submit():
        flash_errors(form)
        return redirect(url_for('add'))
        
    if form.reports_to.data == 0:
        # Is there a CEO yet?
        query = "SELECT * FROM nodes where reports_to IS NULL";
        ceo = app.engine.execute(query).fetchone()
        if ceo:
            # Find former root
            query = """SELECT id FROM nodes WHERE reports_to IS NULL"""
            result = app.engine.execute(text(query))
            former_ceo = result.fetchone()['id']

            # Promote new                               
            query = """INSERT INTO nodes (name, job_title, reports_to) 
                       VALUES (:name,'CEO',NULL)
                       RETURNING id;"""
            result = app.engine.execute(text(query),name=form.name.data)
            new_ceo = result.fetchone()['id']
            # Demote old
            query = """UPDATE nodes SET reports_to=:reports_to, job_title='Former CEO' WHERE id=:former_ceo"""
            app.engine.execute(text(query),reports_to=new_ceo,former_ceo=former_ceo)
        else:
          # We're creating the first CEO!
          query = """INSERT INTO nodes (name, job_title, reports_to) 
                     VALUES (:name,'CEO',NULL)"""
          app.engine.execute(text(query),name=form.name.data)           
                                         
    else:
        # Regular new employee
        query = """INSERT INTO nodes (name, job_title, reports_to) 
                   VALUES (:name,:job_title,:reports_to)
                   RETURNING id;"""
                   
        reslt = app.engine.execute(text(query),name=form.name.data,
                                       job_title=form.job_title.data,
                                       reports_to=form.reports_to.data)
                                       
    flash('info','Added new node')                                   
    return redirect(url_for('hierarchy'))

@app.route('/edit/<id>',methods=['GET'])
def edit(id=None):
    form = EditUserForm()
  
    query = "SELECT * FROM nodes where id=:id";
    row = app.engine.execute(text(query),id=id).fetchone()
    
    if not row:
        flash('error',"User ID doesn't exist")
        return redirect(url_for('hierarchy'))
    user = dict(row)
    
    ids = reports_to_ids(user,[])
    exclude = ', '.join(str(i) for i in ids)

    hierarchy = reports_to(user,{})
    
    query = """SELECT * from nodes where id NOT IN ({0});""".format(exclude)
    nodes = app.engine.execute(text(query))
    
    choices = [(g['id'], g['name'],g['job_title']) for g in nodes]
    choices.insert(0, (0,'No one'))

    return render_template('edit.html', user=user, hierarchy=hierarchy, form=form,choices=choices)    

@app.route('/update',methods=['POST'])
def update():
    form = EditUserForm()

    if not form.validate_on_submit():
        flash_errors(form)
        return redirect(url_for('edit',id=form.userid.data))
    
    if form.reports_to.data == 0:
        form.reports_to.data = None
        
        query = "SELECT * FROM nodes where reports_to IS NULL";
        ceo = app.engine.execute(query).fetchone()
        
        if form.userid.data != ceo['id']:
            # This means we're promoting a new ceo!                               
            query = """UPDATE nodes SET reports_to=NULL, job_title='CEO' WHERE id=:id"""
            app.engine.execute(text(query),id=form.userid.data)  
            
            query = """UPDATE nodes SET reports_to=:reports_to, job_title='Former CEO' WHERE id=:former_ceo"""
            app.engine.execute(text(query),reports_to=form.userid.data,former_ceo=ceo['id'])
            
        
    query = """UPDATE nodes SET name =:name, job_title=:job_title,reports_to=:reports_to WHERE id=:id;"""
    app.engine.execute(text(query),name=form.name.data,
                                   job_title=form.job_title.data,
                                   reports_to=form.reports_to.data,
                                   id=form.userid.data)
    flash('info','Updated node.')
    return redirect(url_for('hierarchy'))
    
@app.errorhandler(404)
def page_not_found(e):
    flash('error','Page not found')
    return redirect(url_for('hierarchy'))

class SelectUserForm(Form):    
    query = """SELECT * from nodes"""
    nodes = app.engine.execute(text(query))
    choices = [(g['id'], g['name']) for g in nodes]

    choices.insert(0, (0,'No one'))
    reports_to = SelectField("node",choices=choices,default=0,coerce=int)

# Having some trouble creating dynamic SelectFields, had to forgo the wtforms validation
class NonValidatingSelectField(SelectField):
    def pre_validate(self, form):
        pass

# Add user form
class AddUserForm(Form):
    name = TextField("name", [DataRequired("Name required.")])
    job_title = TextField("job_title")
    reports_to = NonValidatingSelectField("node",choices=[],coerce=int)    

# Edit user form
class EditUserForm(Form):
    userid = TextField("userid",[DataRequired("ID required")])
    name = TextField("name", [DataRequired("Name required.")])
    job_title = TextField("job_title", [DataRequired("Job title required.")])
    reports_to = NonValidatingSelectField("node",choices=[],default=0,coerce=int)
    


     