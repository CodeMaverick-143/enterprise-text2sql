import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Ensure data directory exists
os.makedirs("./data", exist_ok=True)

db_url = os.getenv("DATABASE_URL", "sqlite:///./data/enterprise.db")
engine = create_engine(db_url)
Base = declarative_base()

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    budget = Column(Float, nullable=False)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)
    salary = Column(Float, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))

def init_db():
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if data already exists
    if session.query(Department).count() == 0:
        hr = Department(name="Human Resources", budget=250000.0)
        eng = Department(name="Engineering", budget=1200000.0)
        sales = Department(name="Sales", budget=500000.0)
        
        session.add_all([hr, eng, sales])
        session.commit()
        
        emp1 = Employee(name="Alice Smith", role="Software Engineer", salary=110000.0, department_id=eng.id)
        emp2 = Employee(name="Bob Jones", role="QA Engineer", salary=85000.0, department_id=eng.id)
        emp3 = Employee(name="Charlie Brown", role="HR Specialist", salary=65000.0, department_id=hr.id)
        emp4 = Employee(name="Diana Prince", role="VP Engineering", salary=180000.0, department_id=eng.id)
        emp5 = Employee(name="Evan Wright", role="Sales Executive", salary=95000.0, department_id=sales.id)
        
        session.add_all([emp1, emp2, emp3, emp4, emp5])
        session.commit()
        print("Database initialized with sample data successfully!")
    else:
        print("Database already initialized.")
    
    session.close()

if __name__ == "__main__":
    init_db()
