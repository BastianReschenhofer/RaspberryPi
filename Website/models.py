

from extensions import db
from sqlalchemy import func 
from sqlalchemy.orm import relationship

class Student(db.Model):

    __tablename__ = 'compare_stundent' 
    

    id = db.Column('id_student', db.Integer, primary_key=True)
    full_name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    timeline_entries = relationship('Timeline', 
                                   backref='student', 
                                   lazy=True, 
                                   cascade="all, delete-orphan")

    
    def __init__(self, full_name, present=True):
        self.full_name = full_name

        self.present = present 

    def __repr__(self):
        return f'<Student {self.full_name}, Present: {self.present}>'


class Timeline(db.Model):
    __tablename__ = "studend_timeline"

    id = db.Column(db.Integer, primary_key = True)

    id_student = db.Column(db.Integer, db.ForeignKey('compare_stundent.id_student'), nullable = False)

    rssi_dbm = db.Column(db.Integer, nullable = False)
    timestamp = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f'<Timeline Entry {self.id} (Student {self.id_student})>'

