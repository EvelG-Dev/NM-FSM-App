from app import db, Students


def student(name="Jane Doe"):
    return Students(name=name, city="Miami", addr="123 Main St", pin="33101", phone="305-555-1234")


def test_student_instantiation(flask_app):
    s = student()
    assert s.name == "Jane Doe"
    assert s.city == "Miami"
    assert s.phone == "305-555-1234"


def test_student_saved_to_db(flask_app):
    db.session.add(student("Alice Test"))
    db.session.commit()
    result = Students.query.filter_by(name="Alice Test").first()
    assert result is not None
    assert result.city == "Miami"


def test_all_fields_persisted(flask_app):
    db.session.add(Students(name="Bob Test", city="Hialeah", addr="2 Oak Ave", pin="33012", phone="305-555-0002"))
    db.session.commit()
    r = Students.query.filter_by(name="Bob Test").first()
    assert (r.city, r.addr, r.pin, r.phone) == ("Hialeah", "2 Oak Ave", "33012", "305-555-0002")


def test_student_count_increases(flask_app):
    before = Students.query.count()
    db.session.add(student("Carol Test"))
    db.session.commit()
    assert Students.query.count() == before + 1


def test_student_delete(flask_app):
    s = student("Dave Test")
    db.session.add(s)
    db.session.commit()
    db.session.delete(s)
    db.session.commit()
    assert Students.query.filter_by(name="Dave Test").first() is None
