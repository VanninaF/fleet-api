"""Fonctions de calcul sur la télémétrie d'une flotte de robots.

Toutes les fonctions de ce module sont *pures* : elles ne lisent ni n'écrivent
aucun état global, ne font pas d'entrée-sortie, et retournent toujours le même
résultat pour les mêmes arguments. C'est ce qui les rend faciles à tester.

⚠️  Ce module est le support du TD 1. La spécification de chaque fonction est
    dans sa docstring : c'est **elle** qui fait foi, pas le code.
"""

from __future__ import annotations

import math
from statistics import median

from fleet_api.models import Position, Reading, RobotState

#: Tension d'une batterie considérée comme vide, en millivolts.
EMPTY_MV = 10_500

#: Tension d'une batterie considérée comme pleine, en millivolts.
FULL_MV = 12_600

#: Seuil d'alerte batterie par défaut, en pourcentage.
LOW_BATTERY_PCT = 20.0

#: Délai au-delà duquel un robot silencieux est déclaré hors ligne, en secondes.
OFFLINE_GRACE_S = 120.0


def battery_percentage(
    voltage_mv: int, empty_mv: int = EMPTY_MV, full_mv: int = FULL_MV
) -> float:
    """Convertit une tension batterie en pourcentage de charge.

    La conversion est linéaire entre `empty_mv` (0 %) et `full_mv` (100 %).
    Le résultat est **borné à l'intervalle [0, 100]** : une tension inférieure à
    `empty_mv` donne 0.0, une tension supérieure à `full_mv` donne 100.0.
    Le résultat est arrondi à une décimale.

    Args:
        voltage_mv: Tension mesurée, en millivolts.
        empty_mv: Tension correspondant à 0 %.
        full_mv: Tension correspondant à 100 %.

    Returns:
        Pourcentage de charge, entre 0.0 et 100.0 inclus.

    Raises:
        ValueError: Si `full_mv` n'est pas strictement supérieur à `empty_mv`.

    Examples:
        >>> battery_percentage(12600)
        100.0
        >>> battery_percentage(10500)
        0.0
        >>> battery_percentage(9000)
        0.0
    """
    if full_mv <= empty_mv:
        raise ValueError("full_mv doit être strictement supérieur à empty_mv")
    ratio = (voltage_mv - empty_mv) / (full_mv - empty_mv)
    return round(max(0.0, min(1.0, ratio)) * 100, 1)


def is_low_battery(battery_pct: float, threshold_pct: float = LOW_BATTERY_PCT) -> bool:
    """Indique si le niveau de batterie déclenche l'alerte.

    L'alerte est déclenchée lorsque le niveau est **inférieur ou égal** au
    seuil. Un robot exactement au seuil est donc en alerte.

    Args:
        battery_pct: Niveau de charge, en pourcentage.
        threshold_pct: Seuil d'alerte, en pourcentage.

    Returns:
        Vrai si `battery_pct` est inférieur ou égal à `threshold_pct`.

    Examples:
        >>> is_low_battery(15.0)
        True
        >>> is_low_battery(50.0)
        False
    """
    # TODO: à tester
    return battery_pct <= threshold_pct


def distance_m(a: Position, b: Position) -> float:
    """Distance euclidienne entre deux positions, en mètres.

    Args:
        a: Première position.
        b: Seconde position.

    Returns:
        Distance en mètres, toujours positive ou nulle.

    Examples:
        >>> distance_m(Position(0, 0), Position(3, 4))
        5.0
    """
    return math.hypot(b.x - a.x, b.y - a.y)


def path_length_m(positions: list[Position]) -> float:
    """Longueur totale du trajet passant par toutes les positions, dans l'ordre.

    La longueur est la somme des distances entre positions consécutives. Un
    trajet de moins de deux positions a une longueur nulle.

    Args:
        positions: Positions successives du robot, dans l'ordre chronologique.

    Returns:
        Longueur du trajet en mètres.

    Examples:
        >>> path_length_m([Position(0, 0), Position(3, 4)])
        5.0
        >>> path_length_m([Position(0, 0)])
        0.0
        >>> path_length_m([])
        0.0
    """
    # TODO: à tester
    total = 0.0
    for i in range(len(positions) - 1):
        total += distance_m(positions[i], positions[i + 1])
    return total


def average_speed_mps(path_length_m: float, elapsed_s: float) -> float | None:
    """Vitesse moyenne sur un trajet, en mètres par seconde.

    Args:
        path_length_m: Longueur du trajet parcouru, en mètres.
        elapsed_s: Durée du trajet, en secondes.

    Returns:
        La vitesse moyenne, ou `None` si `elapsed_s` est nul ou négatif — une
        durée non positive ne permet aucun calcul de vitesse.

    Examples:
        >>> average_speed_mps(10.0, 5.0)
        2.0
        >>> average_speed_mps(10.0, 0.0) is None
        True
    """
    # TODO: à tester
    if elapsed_s <= 0:
        return None
    return path_length_m / elapsed_s


def estimate_runtime_minutes(
    battery_pct: float, drain_pct_per_min: float
) -> float | None:
    """Estime l'autonomie restante, en minutes.

    L'estimation suppose une consommation constante.

    Args:
        battery_pct: Niveau de charge actuel, en pourcentage.
        drain_pct_per_min: Consommation, en points de pourcentage par minute.

    Returns:
        L'autonomie restante en minutes, arrondie à une décimale, ou `None` si
        `drain_pct_per_min` est nul ou négatif — le robot ne se décharge pas,
        l'autonomie n'est pas calculable.

    Examples:
        >>> estimate_runtime_minutes(50.0, 2.0)
        25.0
        >>> estimate_runtime_minutes(50.0, 0.0) is None
        True
    """
    # TODO: à tester
    if drain_pct_per_min <= 0:
        return None
    return round(battery_pct / drain_pct_per_min, 1)


def median_voltage_mv(readings: list[Reading]) -> float | None:
    """Tension médiane d'un ensemble de mesures, en millivolts.

    Sur un nombre pair de mesures, la médiane est la moyenne des deux valeurs
    centrales.

    Args:
        readings: Mesures à agréger. L'ordre n'a pas d'importance.

    Returns:
        La tension médiane, ou `None` si la liste est vide.
    """
    # TODO: à tester
    if not readings:
        return None
    return median(r.voltage_mv for r in readings)


def robot_state(
    reading: Reading,
    now_s: float,
    threshold_pct: float = LOW_BATTERY_PCT,
    grace_s: float = OFFLINE_GRACE_S,
) -> RobotState:
    """Détermine l'état d'un robot à partir de sa dernière mesure.

    Les règles sont évaluées **dans cet ordre**, la première qui s'applique
    l'emporte :

    1. `OFFLINE` — la mesure date de plus de `grace_s` secondes. Un robot
       silencieux est hors ligne même si sa dernière batterie était basse.
    2. `CHARGING` — le robot est branché sur sa base.
    3. `LOW_BATTERY` — la batterie est sous le seuil d'alerte.
    4. `OPERATIONAL` — aucun des cas précédents.

    Args:
        reading: Dernière mesure connue du robot.
        now_s: Instant courant, en secondes depuis l'époque Unix.
        threshold_pct: Seuil d'alerte batterie.
        grace_s: Délai de grâce avant de déclarer le robot hors ligne.

    Returns:
        L'état du robot.
    """
    # TODO: à tester
    if now_s - reading.timestamp_s > grace_s:
        return RobotState.OFFLINE
    if reading.is_charging:
        return RobotState.CHARGING
    if is_low_battery(battery_percentage(reading.voltage_mv), threshold_pct):
        return RobotState.LOW_BATTERY
    return RobotState.OPERATIONAL


def detect_voltage_dropouts(readings: list[Reading], max_drop_mv: int) -> list[int]:
    """Repère les chutes de tension anormales entre mesures consécutives.

    Une chute est anormale lorsque la tension perd **strictement plus** de
    `max_drop_mv` millivolts d'une mesure à la suivante. Une remontée de tension
    n'est jamais une chute.

    Args:
        readings: Mesures d'un même robot, dans l'ordre chronologique.
        max_drop_mv: Chute tolérée entre deux mesures, en millivolts.

    Returns:
        Les indices des mesures où la chute est constatée, c'est-à-dire l'indice
        de la mesure **d'arrivée** de chaque chute anormale. Liste vide si aucune
        chute.
    """
    # TODO: à tester
    dropouts = []
    for i in range(1, len(readings)):
        drop = readings[i - 1].voltage_mv - readings[i].voltage_mv
        if drop > max_drop_mv:
            dropouts.append(i)
    return dropouts


def fleet_summary(
    readings: list[Reading], threshold_pct: float = LOW_BATTERY_PCT
) -> dict[str, float | int]:
    """Agrège l'état d'une flotte à partir d'une mesure par robot.

    Args:
        readings: Une mesure par robot. Une flotte vide est un cas valide.
        threshold_pct: Seuil d'alerte batterie.

    Returns:
        Un dictionnaire à trois clés :

        - `robot_count` : nombre de robots (`int`) ;
        - `average_battery_pct` : charge moyenne, arrondie à une décimale
          (`float`). Vaut `0.0` pour une flotte vide ;
        - `low_battery_count` : nombre de robots en alerte batterie (`int`).

    Examples:
        >>> fleet_summary([])
        {'robot_count': 0, 'average_battery_pct': 0.0, 'low_battery_count': 0}
    """
    levels = [battery_percentage(r.voltage_mv) for r in readings]
    return {
        "robot_count": len(readings),
        "average_battery_pct": round(sum(levels) / len(levels), 1) if levels else 0.0,
        "low_battery_count": sum(
            1 for lvl in levels if is_low_battery(lvl, threshold_pct)
        ),
    }


def badly_formatted(x, y):
    return x + y
