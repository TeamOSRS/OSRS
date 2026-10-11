import pytest
from src.modules.robots.humanoid import HumanoidRobot
from src.modules.robots.leap_hand import LeapHandRobot
from src.modules.robots.omx import OMXRobot
from src.modules.robots.rover import RoverRobot
from src.core.robot_manager import RobotManager
from src.core.event_bus import EventBus

def test_humanoid_robot_initialization():
    bot = HumanoidRobot()
    assert bot.name == "Humanoid Bot"
    assert bot.version == "Humanoid V1"
    layout = bot.get_joint_layout()
    assert len(layout) >= 1
    # Motor ID 21 is L1P
    assert 21 in bot.limits
    l1p = bot.limits[21]
    assert l1p["name"] == "L1P"
    assert l1p["min"] < l1p["max"]

def test_leap_hand_initialization():
    hand = LeapHandRobot(version="V1")
    assert hand.name == "LEAP Hand"
    assert hand.version == "V1"
    assert len(hand.limits) >= 16

def test_omx_robot_initialization():
    omx = OMXRobot()
    assert omx.name == "Open Manipulator X"
    assert len(omx.limits) >= 5

def test_rover_robot_initialization():
    rover = RoverRobot()
    assert rover.name == "Rover Bot"
    assert len(rover.limits) >= 6

def test_robot_manager_robot_switching():
    bus = EventBus()
    manager = RobotManager(bus)
    bot = HumanoidRobot()
    manager.set_robot(bot)
    assert manager.active_robot is not None
    assert manager.active_robot.version == "Humanoid V1"
