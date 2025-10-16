import pytest
from app import app, db, Employee

@pytest.fixture
def client():
    # Use in-memory SQLite DB for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()
        # Pre-populate with a sample employee
        emp = Employee(name="John Doe", department="HR")
        db.session.add(emp)
        db.session.commit()

    # Flask test client
    with app.test_client() as client:
        yield client

    # Clean up DB
    with app.app_context():
        db.drop_all()


def test_index_page(client):
    """Test if index page returns 200 and contains employee name"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"John Doe" in response.data


def test_add_employee(client):
    """Test adding a new employee via POST"""
    response = client.post('/add', data={'name': 'Jane Doe', 'department': 'IT'}, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        emp = Employee.query.filter_by(name="Jane Doe").first()
        assert emp is not None
        assert emp.department == "IT"


def test_delete_employee(client):
    """Test deleting an employee"""
    with app.app_context():
        emp = Employee.query.filter_by(name="John Doe").first()
        emp_id = emp.id

    response = client.get(f'/delete/{emp_id}', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        emp = Employee.query.get(emp_id)
        assert emp is None
