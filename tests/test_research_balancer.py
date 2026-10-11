import pytest
from src.core.event_bus import EventBus
from src.modules.research.ball_balancer import BallBalancer

def test_ball_balancer_initialization():
    bus = EventBus()
    balancer = BallBalancer(bus)
    assert balancer.name == "Ball Balancer"
    assert balancer.kp > 0
    assert balancer.kd >= 0
    assert balancer.est_a is not None
    assert balancer.est_b is not None

def test_ball_balancer_gains_update():
    bus = EventBus()
    balancer = BallBalancer(bus)
    balancer.update_gains(kp=1.2, ki=0.05, kd=0.8)
    assert balancer.kp == 1.2
    assert balancer.ki == 0.05
    assert balancer.kd == 0.8

def test_ball_balancer_tilt_limits():
    bus = EventBus()
    balancer = BallBalancer(bus)
    balancer.set_tilt_limits(25.0, 20.0)
    assert balancer.max_tilt_positive == 25.0
    assert balancer.max_tilt_negative == 20.0
