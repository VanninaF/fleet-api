"""Tests du module de télémétrie.

Deux tests vous sont fournis en exemple : ils montrent le style attendu.
Tout le reste est à écrire — voir le TD 1.
"""

import pytest

from fleet_api.models import Position, Reading, RobotState
from fleet_api.telemetry import (
    average_speed_mps,
    battery_percentage,
    detect_voltage_dropouts,
    distance_m,
    estimate_runtime_minutes,
    fleet_summary,
    is_low_battery,
    median_voltage_mv,
    path_length_m,
    robot_state,
)

# ---------------------------------------------------------------------------
# Exemple 1 — un test simple, avec un cas nominal et les deux bornes.
# ---------------------------------------------------------------------------


def test_battery_percentage_bornes_et_cas_nominal():
    """La conversion est linéaire et bornée à [0, 100]."""
    assert battery_percentage(12_600) == 100.0
    assert battery_percentage(10_500) == 0.0
    assert battery_percentage(11_550) == 50.0
    # Hors bornes : on sature, on ne dépasse pas.
    assert battery_percentage(13_000) == 100.0
    assert battery_percentage(9_000) == 0.0


# ---------------------------------------------------------------------------
# Exemple 2 — le même test écrit en paramétré, quand les cas se ressemblent.
# On teste aussi que l'erreur attendue est bien levée.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "attendu"),
    [
        (Position(0, 0), Position(3, 4), 5.0),  # triplet pythagoricien
        (Position(0, 0), Position(0, 0), 0.0),  # distance à soi-même
        (Position(1, 1), Position(-2, -3), 5.0),  # coordonnées négatives
        (Position(3, 4), Position(0, 0), 5.0),  # symétrie
    ],
)
def test_distance_m(a, b, attendu):
    """La distance est euclidienne, positive et symétrique."""
    assert distance_m(a, b) == pytest.approx(attendu)


def test_battery_percentage_rejette_des_bornes_incoherentes():
    """Une plage de tension invalide lève une ValueError."""
    with pytest.raises(ValueError, match="strictement supérieur"):
        battery_percentage(11_000, empty_mv=12_000, full_mv=11_000)


# ---------------------------------------------------------------------------
# À vous. Huit fonctions de fleet_api.telemetry n'ont aucun test :
#
#   is_low_battery, path_length_m, average_speed_mps, estimate_runtime_minutes,
#   median_voltage_mv, robot_state, detect_voltage_dropouts, fleet_summary
#
# Écrivez-les en vous appuyant sur les docstrings, qui font foi.
# Trois de ces fonctions ne respectent pas leur spécification.
# ---------------------------------------------------------------------------

def test_is_low_battery():
    """Test de la fonction is_low_battery."""

    # Cas nominal : batterie faible
    assert is_low_battery(15) is True
    # Cas nominal : batterie suffisante
    assert is_low_battery(60) is False
    # Cas limite : batterie exactement au seuil
    assert is_low_battery(20) is True
    
def test_path_length_m():
    """Test de la fonction path_length_m."""
    
    # Cas nominal : chemin avec deux positions 
    positions = [Position(1, 1), Position(4, 5)]
    assert path_length_m(positions) == pytest.approx(5.0)
    # Cas nominal : chemin avec plusieurs positions
    positions = [Position(0, 0), Position(3, 4), Position(6, 8)]
    assert path_length_m(positions) == pytest.approx(10.0)
    # Cas nominal : chemin avec plusieurs positions dans l'ordre non chronologique
    positions = [Position(1, 1), Position(4, 5), Position(7, 1)]
    assert path_length_m(positions) == pytest.approx(10.0)
    # Cas limite : chemin avec une seule position
    positions = [Position(0, 0)]
    assert path_length_m(positions) == 0.0
    # Cas limite : chemin vide
    positions = []
    assert path_length_m(positions) == 0.0
    
def test_average_speed_mps():
    """Test de la fonction average_speed_mps."""
    
    # Cas nominal : vitesse moyenne avec deux positions et un temps positif
    assert average_speed_mps(10.0, 5.0) == pytest.approx(2.0)
    # Cas limite : temps nul
    assert average_speed_mps(10.0, 0.0) is None
    # Cas limite : temps négatif
    assert average_speed_mps(10.0, -5.0) is None

def test_estimate_runtime_minutes():
    """Test de la fonction estimate_runtime_minutes."""
    
    # Cas nominal : batterie à 50% et consommation de 5% par minute
    assert estimate_runtime_minutes(50.0, 5.0) == pytest.approx(10.0)
    # Cas limite : batterie à 0%
    assert estimate_runtime_minutes(0.0, 5.0) == 0.0
    # Cas limite : consommation nulle
    assert estimate_runtime_minutes(50.0, 0.0) is None
    # Cas limite : consommation négative
    assert estimate_runtime_minutes(50.0, -5.0) is None
    
    
def _reading(
    voltage_mv: int, timestamp_s: float = 0.0, is_charging: bool = False
) -> Reading:
    """Construit un Reading minimal ; seuls les champs passés varient."""
    return Reading(
        robot_id="r1",
        timestamp_s=timestamp_s,
        voltage_mv=voltage_mv,
        position=Position(0, 0),
        is_charging=is_charging,
    )

def test_median_voltage_mv():
    """Test de la fonction median_voltage_mv."""
    
    # Cas nominal : liste avec un nombre impair d'éléments
    readings = [_reading(12000), _reading(11000), _reading(13000)]
    assert median_voltage_mv(readings) == 12000
    # Cas nominal : liste avec un nombre pair d'éléments
    readings = [_reading(12000), _reading(11000), _reading(13000), _reading(12500)]
    assert median_voltage_mv(readings) == pytest.approx(12250.0)
    # Cas limite : liste vide
    assert median_voltage_mv([]) is None
    
def test_robot_state():
    """Test de la fonction robot_state."""
    
    # 1. Cas nominal : rien à signaler
    reading = _reading(voltage_mv=12000, timestamp_s=0.0, is_charging=False)
    assert robot_state(reading, now_s=50.0) == RobotState.OPERATIONAL

    # 2. OFFLINE simple
    reading = _reading(voltage_mv=12000, timestamp_s=0.0, is_charging=False)
    assert robot_state(reading, now_s=200.0) == RobotState.OFFLINE

    # 3. OFFLINE prioritaire sur CHARGING
    reading = _reading(voltage_mv=12000, timestamp_s=0.0, is_charging=True)
    assert robot_state(reading, now_s=200.0) == RobotState.OFFLINE

    # 4. OFFLINE prioritaire sur LOW_BATTERY
    reading = _reading(voltage_mv=10800, timestamp_s=0.0, is_charging=False)
    assert robot_state(reading, now_s=200.0) == RobotState.OFFLINE

    # 5. CHARGING simple
    reading = _reading(voltage_mv=12000, timestamp_s=0.0, is_charging=True)
    assert robot_state(reading, now_s=50.0) == RobotState.CHARGING

    # 6. CHARGING prioritaire sur LOW_BATTERY
    reading = _reading(voltage_mv=10800, timestamp_s=0.0, is_charging=True)
    assert robot_state(reading, now_s=50.0) == RobotState.CHARGING

    # 7. LOW_BATTERY simple
    reading = _reading(voltage_mv=10800, timestamp_s=0.0, is_charging=False)
    assert robot_state(reading, now_s=50.0) == RobotState.LOW_BATTERY

    # 8. Borne : écart exactement égal à grace_s → pas encore OFFLINE
    reading = _reading(voltage_mv=12000, timestamp_s=0.0, is_charging=False)
    assert robot_state(reading, now_s=120.0) == RobotState.OPERATIONAL

def test_detect_voltage_dropouts():
    """Test de la fonction detect_voltage_dropouts."""
    
    # Cas nominal : détection de deux chutes de tension
    readings = [
        _reading(voltage_mv=12000),
        _reading(voltage_mv=11000),
        _reading(voltage_mv=13000),
        _reading(voltage_mv=10000),
        _reading(voltage_mv=12000),
    ]
    assert detect_voltage_dropouts(readings, max_drop_mv=1500) == [3]
    
    # Cas limite : aucune chute de tension
    readings = [
        _reading(voltage_mv=12000),
        _reading(voltage_mv=11900),
        _reading(voltage_mv=11800),
    ]
    assert detect_voltage_dropouts(readings, max_drop_mv=1500) == []
    
    # Cas limite : liste vide
    assert detect_voltage_dropouts([], max_drop_mv=1500) == []
    
def test_fleet_summary():
    """Test de la fonction fleet_summary."""

    # Cas limite : flotte vide
    assert fleet_summary([]) == {
        "robot_count": 0,
        "average_battery_pct": 0.0,
        "low_battery_count": 0,
    }

    # Cas nominal : plusieurs robots, seuil par défaut (20 %)
    readings = [
        _reading(voltage_mv=12000),
        _reading(voltage_mv=10800),
        _reading(voltage_mv=11000),
    ]
    summary = fleet_summary(readings)
    assert summary["robot_count"] == 3
    assert summary["average_battery_pct"] == pytest.approx(36.5)
    assert summary["low_battery_count"] == 1

    # Cas : un seuil personnalisé change le nombre de robots en alerte
    summary_custom = fleet_summary(readings, threshold_pct=30.0)
    assert summary_custom["low_battery_count"] == 2