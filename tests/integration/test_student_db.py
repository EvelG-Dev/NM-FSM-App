import os
import uuid
import pytest
from app import app, db, Students


@pytest.fixture(scope="module")
def integration_app():
    if not os.environ.get("DATABASE_URL", "").startswith("mysql"):
        pytest.fail("Integration tests require a staging MySQL DATABASE_URL")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()


def cleanup(names):
    db.session.rollback()
    Students.query.filter(Students.name.in_(names)).delete(synchronize_session=False)
    db.session.commit()


def test_create_and_retrieve(integration_app):
    name = "Integ-" + uuid.uuid4().hex[:8]
    try:
        db.session.add(Students(name=name, city="Miami", addr="1 Main St", pin="33101", phone="305-555-0000"))
        db.session.commit()
        r = Students.query.filter_by(name=name).first()
        assert r is not None
        assert r.name == name
    finally:
        cleanup([name])


def test_multiple_students(integration_app):
    names = ["Integ-" + uuid.uuid4().hex[:8] for _ in range(3)]
    try:
        for name in names:
            db.session.add(Students(name=name, city="Miami", addr="1 St", pin="33101", phone="305-555-0000"))
        db.session.commit()
        for name in names:
            assert Students.query.filter_by(name=name).first() is not None
    finally:
        cleanup(names)
