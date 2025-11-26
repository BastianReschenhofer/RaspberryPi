
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Student, Timeline
import csv
import io
from sqlalchemy import distinct
from datetime import datetime, timedelta
from collections import defaultdict
import statistics



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


################################################################################################


@home_bp.route('/testpage', methods=['POST', 'GET']) 
def testpage():
        return render_template('testpage.html', students=markStudents(is_testpage=True)) 

@home_bp.route('/timeline', methods=['POST', 'GET']) 
def timeline():
        return render_template('timeline.html', students=markStudents(is_testpage=True)) 

@home_bp.route('/history', methods=['POST', 'GET']) 
def history():
        return render_template('history.html', students=timeline_data()) 

    



from datetime import datetime, timedelta

def markStudents(is_testpage=False): 
    limit_now = datetime.now() - timedelta(minutes=1) 
    
    present_ids = [r.id_student for r in db.session.query(Timeline.id_student)
                   .filter(Timeline.timestamp >= limit_now).distinct()]

    students = Student.query.all()

    for student in students:
        student.present = (student.id in present_ids)
        if is_testpage:
            last_entries = db.session.query(Timeline.rssi_dbm, Timeline.timestamp)\
                .filter(Timeline.id_student == student.id)\
                .order_by(Timeline.timestamp.desc())\
                .limit(500)\
                .all()
            if last_entries:
                student.signal_strength = str(last_entries[0].rssi_dbm)

                values_minute = defaultdict(list)
                for entry in last_entries:
                    minute_n = entry.timestamp.replace(second = 0, microsecond = 0)
                    values_minute[minute_n].append(entry.rssi_dbm)
                sort_minutes = sorted(values_minute.keys())

                student.signal_history = [statistics.median(values_minute[t]) for t in sort_minutes]

                try: 
                    rssi_val = int(float(student.signal_strength))
                    if rssi_val >= -55:
                        student.signal_class = 'range1'
                    elif rssi_val >= -65:
                        student.signal_class = 'range2'
                    else:
                        student.signal_class = 'range3'
                except:
                    student.signal_class = ' '

            else:
                student.signal_strength = 'N/A'
                student.signal_history = []
        else:
            student.signal_strength = 'N/A'

    return students



def timeline_data():
    now = datetime.now()
    limit_history = now - timedelta(hours=6)
    limit_present = now - timedelta(minutes=1)

    present_ids = [r.id_student for r in db.session.query(Timeline.id_student)
                   .filter(Timeline.timestamp >= limit_present).distinct()]

    students = Student.query.all()

    for student in students:
        student.present = (student.id in present_ids)
        
        history_entries = db.session.query(Timeline.rssi_dbm, Timeline.timestamp)\
            .filter(Timeline.id_student == student.id)\
            .filter(Timeline.timestamp >= limit_history)\
            .order_by(Timeline.timestamp.asc())\
            .all()

        values_minute = defaultdict(list)
        for entry in history_entries:
            minute_n = entry.timestamp.replace(second=0, microsecond=0)
            values_minute[minute_n].append(entry.rssi_dbm)

        if history_entries:
            student.signal_strength = str(history_entries[-1].rssi_dbm)
        else:
            student.signal_strength = 'N/A'

        current_pointer = limit_history.replace(second=0, microsecond=0)
        end_pointer = now.replace(second=0, microsecond=0)
        
        temp_history = []
        temp_labels = []
        
        while current_pointer <= end_pointer:
            
            time_str = current_pointer.strftime("%H:%M")
            temp_labels.append(time_str)

            if current_pointer in values_minute:
                val = statistics.median(values_minute[current_pointer])
                temp_history.append(val)
            else:
                temp_history.append(-100)
            
            current_pointer += timedelta(minutes=1)
        
        student.signal_history = temp_history
        student.time_labels = temp_labels

    return students