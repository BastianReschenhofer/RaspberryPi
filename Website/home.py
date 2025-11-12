
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Student, Timeline
import csv
import io
from sqlalchemy import distinct
from datetime import datetime, timedelta
import os

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home(): 
    return render_template('homepage.html', students=markStudents())


@home_bp.route('/add_student', methods = ['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        if 'csv_file' in request.files:
            file = request.files['csv_file']
            
            if file and file.filename.endswith('.csv'):

                stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
                csv_reader = csv.reader(stream)
                

                db.session.begin()
                
                try:
                    for row in csv_reader:
                        if len(row) >= 1: 
                           
                            full_name = row[0].strip()
                            
                           
                            present = False
                            
                            if full_name:
                                
                                new_student = Student(
                                    full_name=full_name, 
                                    present=present
                                )
                                db.session.add(new_student)
                    
                    db.session.commit()
                    
                    return redirect(url_for('home.home'))
                except Exception as e:
                    db.session.rollback() 
                    print(f"Fehler beim CSV-Import: {e}")
                    return render_template('add_student.html', error=f'Fehler beim Import: {e}. Bitte CSV-Format prüfen.')
            
            return render_template('add_student.html', error='Ungültige Datei. Bitte eine .csv-Datei hochladen.')
        
        full_name = request.form.get('full_name')
        present = False
        
        if full_name:
            new_student = Student(full_name = full_name, present = present) 
            db.session.add(new_student)
            db.session.commit()
        
            return redirect(url_for('home.home'))
        else:
            return render_template('add_student.html', error='Bitte Felder ausfüllen')


    return render_template('add_student.html')

@home_bp.route('/delete_student/<int:student_id>', methods=['POST', 'GET'])
def delete_student(student_id):
    
    student_delete = Student.query.get_or_404(student_id)
    db.session.delete(student_delete)
    db.session.commit()

    return redirect(url_for('home.home'))


######################################Basti Workspace##########################################################


@home_bp.route('/testpage', methods=['POST', 'GET']) 
def testpage():
        return render_template('testpage.html', students=markStudents(is_testpage=True)) 
    
@home_bp.route('/testdata')
def testdata():
    students = markStudents(is_testpage=True)

    student_data = []
    for student in students:
        if student.present: 
            student_data.append({
                'id': student.id,
                'full_name': student.full_name,
                'signal_strength': getattr(student, 'signal_strength', 'N/A'),
                'signal_color': getattr(student, 'signal_color', 'no-signal')
            })
    return jsonify(student_data)
    



def markStudents(is_testpage=False): 

    from flask import current_app

    pastdatetime = datetime.now()- timedelta(minutes=1)

    present_student_ids = db.session.query(distinct(Timeline.id_student)).filter(
        Timeline.timestamp >= pastdatetime
    ).all()

    present_student_ids = [id_tuple[0] for id_tuple in present_student_ids]

    
    students = Student.query.all()
    
    latest_rssi = {}
    if is_testpage:
        
        subquery = db.session.query(
            Timeline.id_student, 
            db.func.max(Timeline.timestamp).label('max_timestamp')
        ).filter(
            Timeline.id_student.in_(present_student_ids) 
        ).group_by(Timeline.id_student).subquery()

        latest_entries = db.session.query(
            Timeline.id_student, 
            Timeline.rssi_dbm
        ).join(
            subquery,
            (Timeline.id_student == subquery.c.id_student) & 
            (Timeline.timestamp == subquery.c.max_timestamp)
        ).all()
        
        latest_rssi = {entry[0]: str(entry[1]) for entry in latest_entries}


    for student in students:
       
        if student.id in present_student_ids:
            student.present = True
            
            if is_testpage:
                student.signal_strength = latest_rssi.get(student.id, 'N/A')
        else:
            student.present = False
            if is_testpage:
                student.signal_strength = 'N/A' 
        
        base_filename = student.full_name.lower() + '.jpg' 
        

        
        image_path = os.path.join(current_app.root_path, 'static', 'images', base_filename)
        
        if os.path.exists(image_path):
            student.image_url = url_for('static', filename=f'images/{base_filename}')
        else:

            student.image_url = url_for('static', filename='images/placeholder.jpg') 
            
    return students



