# Contributing to OSRS (Open Source Robotics System)

Thank you for your interest in contributing to the **Open Source Robotics System (OSRS)**! We welcome contributions from roboticists, control systems engineers, software developers, and open-source enthusiasts.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to **bilal.07.04.07@gmail.com**.

---

## How Can I Contribute?

### 1. Reporting Bugs
- Search existing [GitHub Issues](https://github.com/BilalSabugar/OSRS/issues) to ensure the bug hasn't already been reported.
- If not, open a new issue using our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).
- Provide hardware details (motor models, serial interface, camera hardware), logs, and reproduction steps.

### 2. Suggesting Enhancements & New Robots
- Open an issue using our [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).
- Describe the motivation, architectural implications, and whether physical or simulated testing is required.

### 3. Submitting Pull Requests
1. **Fork** the repository and create your feature branch:
   ```bash
   git checkout -b feat/my-robot-feature
   ```
2. Follow our [Safety Guidelines](DISCLAIMER.md) when writing motor control or kinematic routines.
3. Verify your changes pass all automated tests:
   ```bash
   python -m pytest tests/ -v
   cd frontend && npm run build
   ```
4. Commit your changes using conventional commit messages (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
5. Push your branch and open a Pull Request against `main`.

---

## Local Development Workflow

### 1. Backend Setup (FastAPI & MuJoCo)
```bash
# Clone the repository
git clone https://github.com/BilalSabugar/OSRS.git
cd OSRS

# Install Python dependencies (Python 3.10+)
pip install -r requirements.txt
pip install pytest httpx

# Start the OSRS backend server
python main.py
```

### 2. Frontend Setup (React & Vite)
```bash
cd frontend
npm install
npm run dev     # Starts local development server on http://localhost:5173
npm run build   # Verifies production bundle build into dist/
```

### 3. Running Physics Simulations (MuJoCo)
```bash
# Run the interactive humanoid MuJoCo simulation
python simulation_ref/simulate_humanoid.py --scene plate

# Test headless simulation benchmark
python simulation_ref/simulate_humanoid.py --headless --duration 10.0
```

### 4. Running the Test Suite
```bash
python -m pytest tests/ -v
```

---

## Code Standards & Style

- **Python**: Follow PEP 8 guidelines. Type hints are encouraged for public module functions.
- **React/JavaScript**: Use modular screen architecture (`src/screens/`), functional components, and TailwindCSS / Vanilla CSS tokens.
- **Hardware Fail-Safes**: All physical actuator routines must gracefully handle communication loss and respect configured travel limits.
- **AI-Assisted Contributions**: In accordance with our [AI Disclosure Policy](AI_DISCLOSURE.md), AI-assisted code contributions are welcome provided they are thoroughly verified, tested, and reviewed by a human contributor.

---

## Questions & Community

Have questions or need assistance? Join our [GitHub Discussions](https://github.com/BilalSabugar/OSRS/discussions) to connect with the team and community.
