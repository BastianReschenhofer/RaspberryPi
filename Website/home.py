
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

@home_bp.route('/timeline', methods=['POST', 'GET']) 
def timeline():
        return render_template('timeline.html', students=markStudents(is_testpage=True)) 

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
    



"""
def markStudents(is_testpage=False): 

    from flask import current_app

    pastdatetime = datetime.now()- timedelta(minutes=1)

    present_student_ids = db.session.query(distinct(Timeline.id_student)).filter(
        Timeline.timestamp >= pastdatetime
    ).all()

    present_student_ids = [id_tuple[0] for id_tuple in present_student_ids]

    


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




def timeline_data(hours=12, specific_date=None):
    now = datetime.now()

    if specific_date:
        start_time = datetime.strptime(specific_date, "%Y-%m-%d")
        end_time = start_time + timedelta(days=1)
    else:
        hours = hours or 12 
        end_time = now
        start_time = now - timedelta(hours=hours)

    recent_limit = now - timedelta(minutes=2)
    present_students = db.session.query(Timeline.id_student)\
        .filter(Timeline.timestamp >= recent_limit).all()
    
    present_ids = [x[0] for x in present_students]

    students = Student.query.all()

    for student in students:
        student.present = (student.id in present_ids)

        # alle Eintröge im Zeitraum
        logs = db.session.query(Timeline)\
            .filter(Timeline.id_student == student.id)\
            .filter(Timeline.timestamp >= start_time)\
            .filter(Timeline.timestamp <= end_time)\
            .order_by(Timeline.timestamp).all()

        log_dict = { log.timestamp.strftime("%H:%M") : log.rssi_dbm for log in logs }

        labels = []
        values = []

        current = start_time
        while current < end_time and current <= now:
            time_str = current.strftime("%H:%M")
            labels.append(time_str)

            rssi = log_dict.get(time_str, -100)
            values.append(rssi)

            current += timedelta(minutes=1)

        student.time_labels = labels
        student.signal_history = values
        
        if logs:
            student.signal_strength = str(logs[-1].rssi_dbm)
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
