"""Tests d'intégration contre une vraie base PostgreSQL.

Nécessitent `DATABASE_URL` (voir `compose.yaml` / `.github/workflows/image.yml`) :

    docker compose up -d db
    DATABASE_URL=postgresql://app:app@localhost:5432/fleet \
        uv run pytest -m integration -v

Sans `DATABASE_URL`, ces tests sont ignorés (skip) plutôt que d'échouer : on
ne veut pas casser `uv run pytest` pour qui n'a pas de base sous la main.
"""

from __future__ import annotations

import os
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from fleet_api.models import Position, Reading
from fleet_api.store import PostgresStore

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL non définie"),
]


def _robot_id() -> str:
    """Un identifiant unique par test pour ne pas se marcher sur les pieds."""
    return f"test-{uuid.uuid4().hex[:8]}"


def _reading(robot_id: str, timestamp_s: float, voltage_mv: int = 12_000) -> Reading:
    return Reading(
        robot_id=robot_id,
        timestamp_s=timestamp_s,
        voltage_mv=voltage_mv,
        position=Position(x=1.0, y=2.0),
        is_charging=False,
    )


# ---------------------------------------------------------------------------
# PostgresStore directement
# ---------------------------------------------------------------------------


@pytest.fixture
def store() -> PostgresStore:
    assert DATABASE_URL is not None  # garanti par le skipif du module
    return PostgresStore(DATABASE_URL)


def test_ping_reussit_contre_une_base_vivante(store: PostgresStore):
    assert store.ping() is True


def test_add_puis_latest_renvoie_la_derniere_mesure(store: PostgresStore):
    robot_id = _robot_id()
    store.add(_reading(robot_id, timestamp_s=1.0, voltage_mv=11_000))
    store.add(_reading(robot_id, timestamp_s=2.0, voltage_mv=12_000))

    derniere = store.latest(robot_id)

    assert derniere is not None
    assert derniere.timestamp_s == 2.0
    assert derniere.voltage_mv == 12_000


def test_latest_renvoie_none_pour_un_robot_inconnu(store: PostgresStore):
    assert store.latest(_robot_id()) is None


def test_history_est_triee_de_la_plus_recente_a_la_plus_ancienne(
    store: PostgresStore,
):
    robot_id = _robot_id()
    for t in (1.0, 3.0, 2.0):
        store.add(_reading(robot_id, timestamp_s=t))

    historique = store.history(robot_id)

    assert [r.timestamp_s for r in historique] == [3.0, 2.0, 1.0]


def test_history_respecte_la_limite(store: PostgresStore):
    robot_id = _robot_id()
    for t in range(5):
        store.add(_reading(robot_id, timestamp_s=float(t)))

    assert len(store.history(robot_id, limit=2)) == 2


def test_latest_all_renvoie_une_mesure_par_robot(store: PostgresStore):
    robot_a, robot_b = _robot_id(), _robot_id()
    store.add(_reading(robot_a, timestamp_s=1.0))
    store.add(_reading(robot_b, timestamp_s=1.0))
    store.add(_reading(robot_a, timestamp_s=2.0))

    par_robot = {r.robot_id: r for r in store.latest_all()}

    assert par_robot[robot_a].timestamp_s == 2.0
    assert robot_b in par_robot


# ---------------------------------------------------------------------------
# L'API, bout en bout, contre la même base
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    from fleet_api.api import app  # import tardif : lit DATABASE_URL à l'import

    return TestClient(app)


def test_health_est_ok_contre_une_vraie_base(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "storage": "ok"}


def test_ingest_puis_lecture_du_robot_aller_retour(client: TestClient):
    robot_id = _robot_id()

    reponse_ingest = client.post(
        f"/robots/{robot_id}/telemetry",
        json={
            "timestamp_s": time.time(),
            "voltage_mv": 12_000,
            "x": 0.0,
            "y": 0.0,
            "is_charging": False,
        },
    )
    assert reponse_ingest.status_code == 201

    reponse_robot = client.get(f"/robots/{robot_id}")

    assert reponse_robot.status_code == 200
    corps = reponse_robot.json()
    assert corps["robot_id"] == robot_id
    assert corps["state"] == "operational"
