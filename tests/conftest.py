import pytest
from app import app, db


@pytest.fixture(scope="function")
def flask_app():
    app.config.update(TESTING=True)
    with app.app_context():
        assert db.engine.url.get_backend_name() == "sqlite", "Unit/HTTP tests require SQLite"
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(flask_app):
    return flask_app.test_client()
