
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

@home_bp.route('/', methods=['GET'])
def home(): 

    all_klasses_query = db.session.query(distinct(Student.student_class)).all()
    all_klasses = [k[0] for k in all_klasses_query if k[0]]
    all_klasses.sort()

    all_students_query = db.session.query(Student.full_name).all()
    all_students = [s[0] for s in all_students_query if s[0]]
    all_students.sort()

    selected_klass = request.args.get('class_filter', default=None)

    
    if selected_klass:
        students = markStudents()
        students = [s for s in students if s.student_class == selected_klass]
    else:
        students = markStudents()
    return render_template('homepage.html', students=students, selected_klass=selected_klass, all_klasses=all_klasses)


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

                            student_class = row[1].strip()
                            
                            if full_name:
                                
                                new_student = Student(
                                    full_name=full_name, 
                                    present=present,
                                    student_class=student_class
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
        student_class= request.form.get('student_class')
        
        if full_name:
            new_student = Student(full_name = full_name, present = present, student_class = student_class) 
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
        
        date_filter = request.args.get('date_filter')

        try:
            hours = int(request.args.get('hours',12))
        except ValueError:
            hours = 12

        selected_date = ""

        current_range = hours

        if date_filter:
            selected_date = date_filter
            current_range = None
            students = timeline_data(hours=None, specific_date=date_filter)
        else:
            students = timeline_data(hours=hours, specific_date=None)
        
        return render_template('history.html', students=students, selected_date=selected_date, current_range=current_range) 

@home_bp.route('/settings/<int:student_id>', methods=['GET', 'POST'])
def settings(student_id):
    student = Student.query.get_or_404(student_id)  
    if request.method == 'POST':
        neuer_name = request.form.get('input_name')
        neue_klasse = request.form.get('input_class')
        student.full_name = neuer_name
        student.student_class = neue_klasse
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Fehler")
            
    return render_template('settings.html', student=student) 



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

    return students