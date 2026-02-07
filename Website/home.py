from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from extensions import db
from models import Student, Timeline
import csv
import io
from sqlalchemy import distinct
from datetime import datetime, timedelta
import statistics
from collections import defaultdict
import os
import time
import hashlib

home_bp = Blueprint('home', __name__)

###########################################

@home_bp.route('/', methods=['GET'])
def home(): 
    return render_template('homepage.html')

@home_bp.route('/history', methods=['POST', 'GET']) 
def history():
    return render_template('history.html')

@home_bp.route('/timeline', methods=['POST', 'GET']) 
def timeline():
    return render_template('timeline.html')

@home_bp.route('/testpage', methods=['POST', 'GET']) 
def testpage():
    return render_template('testpage.html')


###########################################

@home_bp.route('/api/data', methods=['GET'])
def get_data_for_homepage():  
    
    search_text = request.args.get('name_search')
    class_filter = request.args.get('class_filter')

    all_classes = get_all_classes()

    students = calculate_presence_only()

    filtered_students = filter_student_list(students, search_text, class_filter)

    json_student_list = []
    for s in filtered_students:
        student_data = {
            'id': s.id,
            'full_name': s.full_name,
            'present': s.present,
            'student_class': s.student_class,
            'urls': {
                'image': url_for('static', filename='images/' + s.full_name + '.png'),
                'settings': url_for('home.settings', student_id=s.id),
                'history': url_for('home.history', name_search=s.full_name),
                'placeholder': url_for('static', filename='images/PlatzhalterWeiß.png')
            }
        }
        json_student_list.append(student_data)
    
    return jsonify({'classes': all_classes, 'students': json_student_list})


@home_bp.route('/api/history_data', methods=['GET'])
def get_data_for_history():
    
    search_text = request.args.get('name_search')
    class_filter = request.args.get('class_filter')
    date_filter = request.args.get('date_filter')
    
    try:
        hours = int(request.args.get('hours', 12))
    except:
        hours = 12

    all_classes = get_all_classes()
    
    if date_filter:
        students = calculate_history_charts(specific_date=date_filter, hours=None)
    else:
        students = calculate_history_charts(specific_date=None, hours=hours)

    filtered_students = filter_student_list(students, search_text, class_filter)

    json_student_list = []
    for s in filtered_students:
        student_data = {
            'id': s.id,
            'full_name': s.full_name,
            'present': s.present,
            'signal_history': s.signal_history, 
            'time_labels': s.time_labels,       
            'urls': {
                'image': url_for('static', filename='images/' + s.full_name + '.png'),
                'settings': url_for('home.settings', student_id=s.id),
                'placeholder': url_for('static', filename='images/PlatzhalterWeiß.png')
            }
        }
        json_student_list.append(student_data)

    return jsonify({'classes': all_classes, 'students': json_student_list})


@home_bp.route('/api/test_data', methods=['GET'])
def get_data_for_testmode():
    
    class_filter = request.args.get('class_filter')
    
    all_classes = get_all_classes()
    students = calculate_test_mode_data()

    filtered_students = []
    present_count = 0
    total_count = len(students)
    
    for s in students:
        if s.present:
            if class_filter and s.student_class != class_filter:
                continue
            filtered_students.append(s)
            present_count += 1

    json_student_list = []
    for s in filtered_students:
        student_data = {
            'id': s.id,
            'full_name': s.full_name,
            'present': s.present,
            'signal_strength': s.signal_strength,
            'signal_class': s.signal_class,       
            'signal_history': s.signal_history,   
            'urls': {
                'image': url_for('static', filename='images/' + s.full_name + '.png'),
                'placeholder': url_for('static', filename='images/PlatzhalterWeiß.png')
            }
        }
        json_student_list.append(student_data)

    return jsonify({
        'classes': all_classes, 
        'students': json_student_list,
        'meta': {'present_count': present_count, 'total_count': total_count}
    })


###########################################

def get_all_classes():
 
    raw_list = db.session.query(distinct(Student.student_class)).all()
    clean_list = []
    for item in raw_list:
        if item[0]: 
            clean_list.append(item[0])
    clean_list.sort()
    return clean_list

def filter_student_list(students, search_text, class_filter):
 
    result = []
    for s in students:
        if search_text and search_text.lower() not in s.full_name.lower():
            continue
        if class_filter and s.student_class != class_filter:
            continue
        result.append(s)
    return result

def calculate_presence_only():

    limit = datetime.now() - timedelta(minutes=2)
    recent_logs = db.session.query(Timeline.id_student).filter(Timeline.timestamp >= limit).distinct().all()
    
    present_ids = []
    for row in recent_logs:
        present_ids.append(row.id_student)
    
    all_students = Student.query.all()
    for student in all_students:
        if student.id in present_ids:
            student.present = True
        else:
            student.present = False
    return all_students

def calculate_history_charts(specific_date=None, hours=12):
   
    now = datetime.now()
    
    if specific_date:
        start_time = datetime.strptime(specific_date, "%Y-%m-%d")
        end_time = start_time + timedelta(days=1)
    else:
        end_time = now
        start_time = now - timedelta(hours=hours)

    limit_now = now - timedelta(minutes=2)
    recent_logs = db.session.query(Timeline.id_student).filter(Timeline.timestamp >= limit_now).all()
    present_ids = [row.id_student for row in recent_logs]

    all_students = Student.query.all()

    for student in all_students:
        student.present = (student.id in present_ids)

        logs = db.session.query(Timeline)\
            .filter(Timeline.id_student == student.id)\
            .filter(Timeline.timestamp >= start_time)\
            .filter(Timeline.timestamp <= end_time)\
            .order_by(Timeline.timestamp).all()

        log_dict = {}
        for log in logs:
            time_str = log.timestamp.strftime("%H:%M")
            log_dict[time_str] = log.rssi_dbm

        labels = []
        values = []
        current_step = start_time
        loop_end = end_time if specific_date else min(end_time, now)

        while current_step < loop_end:
            time_str = current_step.strftime("%H:%M")
            labels.append(time_str)
            values.append(log_dict.get(time_str, -100))
            current_step += timedelta(minutes=1)

        student.time_labels = labels
        student.signal_history = values

    return all_students

def calculate_test_mode_data():

    limit = datetime.now() - timedelta(minutes=1)
    recent_logs = db.session.query(Timeline.id_student).filter(Timeline.timestamp >= limit).distinct().all()
    present_ids = [row.id_student for row in recent_logs]

    students = Student.query.all()

    for student in students:
        if student.id in present_ids:
            student.present = True
        else:
            student.present = False
        
        last_entries = db.session.query(Timeline.rssi_dbm, Timeline.timestamp)\
            .filter(Timeline.id_student == student.id)\
            .order_by(Timeline.timestamp.desc()).limit(500).all()

        if last_entries:
            student.signal_strength = str(last_entries[0].rssi_dbm)

            values_per_minute = defaultdict(list)
            for entry in last_entries:
                m = entry.timestamp.replace(second=0, microsecond=0)
                values_per_minute[m].append(entry.rssi_dbm)
            
            history_values = []
            for t in sorted(values_per_minute.keys()):
                history_values.append(statistics.median(values_per_minute[t]))
            
            student.signal_history = history_values

            try:
                val = int(float(student.signal_strength))
                if val >= -55: student.signal_class = 'range1'
                elif val >= -65: student.signal_class = 'range2'
                else: student.signal_class = 'range3'
            except:
                student.signal_class = ''
        else:
            student.signal_strength = 'N/A'
            student.signal_history = []
            student.signal_class = ''

    return students


###########################################

@home_bp.route('/add_student', methods = ['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        
        if 'csv_file' in request.files:
            file = request.files['csv_file']
            if file and file.filename.endswith('.csv'):
                stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
                csv_reader = csv.reader(stream)
                try:
                    for row in csv_reader:
                        if len(row) >= 1:
                            name = row[0].strip()
                            cls = row[1].strip() if len(row) > 1 else ""
                            if name:
                                db.session.add(Student(full_name=name, present=False, student_class=cls))
                    db.session.commit()
                    return redirect(url_for('home.home'))
                except Exception as e:
                    db.session.rollback()
                    return render_template('add_student.html', error=f'Fehler: {e}')
       
        name = request.form.get('full_name')
        cls = request.form.get('student_class')
        if name:
            hash_basis = f"{name}{time.time()}".encode('utf-8')
            qr_hash = hashlib.sha256(hash_basis).hexdigest()[:8]

            img = request.files.get('student_image')
            if img and img.filename.endswith('.png'):
                img.save(f"static/images/{name}.png")

            new_student = Student(full_name=name, present=False, student_class=cls)
            new_student.qr_hash = qr_hash
            db.session.add(new_student)
            db.session.commit()

            return redirect(url_for('home.home'))

    return render_template('add_student.html')

@home_bp.route('/delete_student/<int:student_id>', methods=['POST', 'GET'])
def delete_student(student_id):
   
    s = Student.query.get_or_404(student_id)
    db.session.delete(s)
    db.session.commit()
    filename = (f"static/images/{s.full_name}.png")
    os.remove(filename)
    return redirect(url_for('home.home'))

@home_bp.route('/settings/<int:student_id>', methods=['GET', 'POST'])
def settings(student_id):
    
    s = Student.query.get_or_404(student_id)
    if request.method == 'POST':

        old_name = s.full_name
        new_name = request.form.get('input_name')

        old_path = os.path.join('static', 'images', f"{old_name}.png")
        new_path = os.path.join('static', 'images', f"{new_name}.png")

        
        s.full_name = request.form.get('input_name')
        img = request.files.get('student_image')
        s.student_class = request.form.get('input_class')

        if img and img.filename != '':
            if os.path.exists(old_path):
                os.remove(old_path)
            img.save(new_path)

        if old_name != new_name:
            if os.path.exists(old_path):
                os.rename(old_path, new_path)

      


        try: db.session.commit()
        except: db.session.rollback()
    
            
    return render_template('settings.html', student=s)