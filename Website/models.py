

from extensions import db
from sqlalchemy import func 
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Student(db.Model):

    __tablename__ = 'compare_student' 
    

    id = db.Column('id_student', db.Integer, primary_key=True)
    full_name = db.Column(db.String(80), nullable=False)
    student_class = db.Column('class', db.String(20))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    qr_hash = db.Column(db.String(128), unique = True, nullable=True)
    
    
    timeline_entries = relationship('Timeline', backref='student', lazy=True, cascade="all, delete-orphan")

    
    def __init__(self, full_name, present=True, student_class=None):
        self.full_name = full_name

        self.present = present 
        self.student_class = student_class

    def __repr__(self):
        return f'<Student {self.full_name}, Present: {self.present}>'


class Timeline(db.Model):
    __tablename__ = "student_timeline"

    id = db.Column(db.Integer, primary_key = True)

    id_student = db.Column(db.Integer, db.ForeignKey('compare_student.id_student'), nullable = False, index=True)

    rssi_dbm = db.Column(db.Integer, nullable = False)
    timestamp = db.Column(db.DateTime, default=func.now(), index=True)
    
    def __repr__(self):
        return f'<Timeline Entry {self.id} (Student {self.id_student})>'


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)