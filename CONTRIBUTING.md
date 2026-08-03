# Contributing to OSRS

Thank you for your interest in contributing to the **Open Source Robotic System (OSRS)**! We welcome contributions from hardware enthusiasts, software developers, robotics researchers, and community members.

---

## How Can I Contribute?

### 1. Reporting Bugs
- Search existing [GitHub Issues](https://github.com/BilalSabugar/OSRS/issues) to ensure the bug hasn't already been reported.
- If not, open a new issue using the **Bug Report** template.
- Include detailed steps to reproduce, hardware specifications (servos, load cells, cameras), logs, and system information.

### 2. Suggesting Enhancements
- Open an issue using the **Feature Request** template.
- Explain the use case, motivation, and proposed implementation details.

### 3. Submitting Code (Pull Requests)
1. **Fork** the repository and create a feature branch off `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Make your code changes and verify existing functionality.
3. Test both hardware modules and frontend GUI (`cd frontend && npm test` or `npm run dev`).
4. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat(perception): add new vision tracking provider"
   ```
5. Push to your fork and submit a **Pull Request** targeting the `main` branch.

---

## Development Setup

### Backend (Python & MuJoCo)
```bash
pip install -r requirements.txt
python main.py
```

### Frontend (React & Vite)
```bash
cd frontend
npm install
npm run dev
```

---

## Code Style & Guidelines

- **Python**: Follow PEP 8 guidelines. Write clear docstrings for public module APIs.
- **JavaScript/React**: Use functional components and modern ES6+ syntax.
- **Hardware Integration**: Ensure hardware failure paths fail gracefully (e.g. fallback mock modes or emergency stops).

Thank you for helping improve OSRS!
