"""Deterministic exact and bounded-heuristic revisit routing."""

from __future__ import annotations

import math
from dataclasses import dataclass

from markerwalk.audit import AuditReport
from markerwalk.model import Marker, Point, SurveyProject

_EXACT_LIMIT = 14
_EPSILON = 1e-12


@dataclass(frozen=True, slots=True)
class RouteStop:
    marker: Marker
    segment_distance: float
    cumulative_distance: float


@dataclass(frozen=True, slots=True)
class RoutePlan:
    stops: tuple[RouteStop, ...]
    total_distance: float
    optimal: bool
    strategy: str


def distance(left: Point, right: Point) -> float:
    return math.hypot(left.x - right.x, left.y - right.y)


def _prefer(
    candidate_cost: float,
    candidate_path: tuple[int, ...],
    current: tuple[float, tuple[int, ...]] | None,
) -> bool:
    if current is None or candidate_cost < current[0] - _EPSILON:
        return True
    return math.isclose(candidate_cost, current[0], abs_tol=_EPSILON) and (
        candidate_path < current[1]
    )


def _exact_order(markers: tuple[Marker, ...], start: Point, end: Point | None) -> tuple[int, ...]:
    count = len(markers)
    states: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {}
    for index, marker in enumerate(markers):
        states[(1 << index, index)] = (distance(start, marker.point), (index,))

    for mask in range(1, 1 << count):
        for last in range(count):
            state = states.get((mask, last))
            if state is None:
                continue
            for following in range(count):
                if mask & (1 << following):
                    continue
                following_mask = mask | (1 << following)
                candidate_path = (*state[1], following)
                candidate_cost = state[0] + distance(markers[last].point, markers[following].point)
                key = (following_mask, following)
                if _prefer(candidate_cost, candidate_path, states.get(key)):
                    states[key] = (candidate_cost, candidate_path)

    full_mask = (1 << count) - 1
    best: tuple[float, tuple[int, ...]] | None = None
    for last in range(count):
        cost, path = states[(full_mask, last)]
        if end is not None:
            cost += distance(markers[last].point, end)
        if _prefer(cost, path, best):
            best = (cost, path)
    assert best is not None
    return best[1]


def _route_distance(
    markers: tuple[Marker, ...], order: tuple[int, ...], start: Point, end: Point | None
) -> float:
    total = 0.0
    current = start
    for index in order:
        total += distance(current, markers[index].point)
        current = markers[index].point
    if end is not None:
        total += distance(current, end)
    return total


def _heuristic_order(
    markers: tuple[Marker, ...], start: Point, end: Point | None
) -> tuple[int, ...]:
    remaining = set(range(len(markers)))
    order: list[int] = []
    current = start
    while remaining:
        following = min(
            remaining,
            key=lambda index: (distance(current, markers[index].point), markers[index].id),
        )
        order.append(following)
        remaining.remove(following)
        current = markers[following].point

    best = tuple(order)
    best_cost = _route_distance(markers, best, start, end)
    improved = True
    while improved:
        improved = False
        candidate_best = best
        candidate_cost = best_cost
        for left in range(len(best) - 1):
            for right in range(left + 2, len(best) + 1):
                candidate = (*best[:left], *reversed(best[left:right]), *best[right:])
                cost = _route_distance(markers, candidate, start, end)
                if cost < candidate_cost - _EPSILON or (
                    math.isclose(cost, candidate_cost, abs_tol=_EPSILON)
                    and candidate < candidate_best
                ):
                    candidate_best = candidate
                    candidate_cost = cost
        if candidate_cost < best_cost - _EPSILON:
            best = candidate_best
            best_cost = candidate_cost
            improved = True
    return best


def _stops(
    markers: tuple[Marker, ...], order: tuple[int, ...], start: Point
) -> tuple[RouteStop, ...]:
    result: list[RouteStop] = []
    current = start
    cumulative = 0.0
    for index in order:
        marker = markers[index]
        segment = distance(current, marker.point)
        cumulative += segment
        result.append(RouteStop(marker, segment, cumulative))
        current = marker.point
    return tuple(result)


def plan_route(project: SurveyProject, report: AuditReport) -> RoutePlan:
    """Plan a route through markers with missing views or files."""
    incomplete_ids = set(report.incomplete_marker_ids)
    markers = tuple(
        sorted(
            (marker for marker in project.markers if marker.id in incomplete_ids),
            key=lambda marker: marker.id,
        )
    )
    if not markers:
        return RoutePlan((), 0.0, True, "empty")

    if len(markers) <= _EXACT_LIMIT:
        order = _exact_order(markers, project.start, project.end)
        strategy = "held-karp"
        optimal = True
    else:
        order = _heuristic_order(markers, project.start, project.end)
        strategy = "nearest-neighbour-2opt"
        optimal = False
    return RoutePlan(
        _stops(markers, order, project.start),
        _route_distance(markers, order, project.start, project.end),
        optimal,
        strategy,
    )
