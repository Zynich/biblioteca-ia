"""Fixtures compartilhadas: banco SQLite em memória, recriado a cada teste, e um
TestClient com a dependency `get_db` sobrescrita para usar esse banco."""

import os
from collections.abc import Generator

# Precisa ser setado antes de importar app.main: o lifespan da aplicação cria as
# tabelas usando o engine construído a partir de settings.database_url, e não
# queremos que os testes toquem em um arquivo SQLite real em disco.
os.environ.setdefault("BOOKS_DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    # StaticPool: mantém uma única conexão compartilhada entre threads. Sem isso, cada
    # nova conexão a um SQLite ":memory:" cria um banco vazio à parte — e o TestClient
    # do FastAPI executa as rotas síncronas em outra thread (threadpool do Starlette).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
