import pytest
from fastapi.testclient import TestClient
from src.core.server import app

client = TestClient(app)

def test_status_endpoint():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "connected" in data
    assert "mock_mode" in data

def test_simulation_list_endpoint():
    res = client.get("/api/simulation/list")
    assert res.status_code == 200
    data = res.json()
    assert "simulations" in data
    assert len(data["simulations"]) >= 1

def test_simulation_status_endpoint():
    res = client.get("/api/simulation/status")
    assert res.status_code == 200
    data = res.json()
    assert "active" in data

def test_research_paper_info_endpoint():
    res = client.get("/api/docs/paper/info")
    assert res.status_code == 200
    data = res.json()
    assert "title" in data
    assert "Tactile Robotic Perception" in data["title"]

def test_balancer_calibration_endpoint():
    res = client.get("/api/research/balancer/calibration")
    assert res.status_code == 200
    data = res.json()
    assert "calib_left" in data
    assert "calib_right" in data
