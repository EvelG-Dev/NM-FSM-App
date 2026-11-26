import pytest
from app import Students


def form_data():
    return dict(name="Alice Smith", city="Miami", addr="123 Main St", pin="33101", phone="305-555-1234")


def test_index_returns_200(client):
    assert client.get("/").status_code == 200


def test_new_form_returns_200(client):
    assert client.get("/new").status_code == 200


def test_add_student_redirects(client):
    assert client.post("/new", data=form_data()).status_code == 302


def test_student_appears_on_list(client):
    data = form_data()
    data["name"] = "Bob Jones"
    client.post("/new", data=data)
    assert b"Bob Jones" in client.get("/", follow_redirects=True).data


@pytest.mark.parametrize("missing", ["name", "city", "addr"])
def test_required_fields(client, missing):
    data = form_data()
    data[missing] = ""
    before = Students.query.count()
    response = client.post("/new", data=data)
    assert response.status_code == 200
    assert Students.query.count() == before



@pytest.mark.parametrize("flag", ["true", "false"])
def test_form_major_field(client, monkeypatch, flag):
    monkeypatch.setenv("ENABLE_MAJOR_FIELD", flag)
    r = client.get("/new")
    shown = b'name="major"' in r.data
    assert shown == (flag == "true")


@pytest.mark.parametrize("flag", ["true", "false"])
def test_list_major_column(client, monkeypatch, flag):
    monkeypatch.setenv("ENABLE_MAJOR_FIELD", flag)
    r = client.get("/")
    shown = b'<th>Major</th>' in r.data
    assert shown == (flag == "true")


@pytest.mark.parametrize("flag", ["true", "false"])
def test_post_major_persistence(client, monkeypatch, flag):
    monkeypatch.setenv("ENABLE_MAJOR_FIELD", flag)
    data = form_data()
    data["name"] = "Major Flag Student"
    data["major"] = "Information Technology"
    response = client.post("/new", data=data)
    assert response.status_code == 302
    student = Students.query.filter_by(name=data["name"]).one()
    expected = data["major"] if flag == "true" else None
    assert student.major == expected
