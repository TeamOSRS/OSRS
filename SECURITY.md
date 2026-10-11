# Security Policy

The OSRS team takes software and robotics security seriously. As a physical cyber-physical system, vulnerabilities can pose both computational and physical safety risks.

---

## Supported Versions

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 1.2.x   | :white_check_mark: | Current Active Release |
| 1.1.x   | :white_check_mark: | Maintenance |
| < 1.0   | :x:                | Deprecated |

---

## Reporting a Vulnerability

If you discover a security vulnerability (such as unauthorized remote command execution, buffer overflows in serial drivers, or denial-of-service in real-time loops):

1. **Do NOT open a public GitHub issue.**
2. Send an email to the project maintainer: **bilal.07.04.07@gmail.com** or open a [Private Security Advisory](https://github.com/BilalSabugar/OSRS/security/advisories/new) on GitHub.
3. Include in your report:
   - Detailed description of the vulnerability.
   - Proof-of-concept script or reproduction steps.
   - Affected components (backend API, WebSocket daemon, serial bus handler).
   - Potential impact on physical hardware safety.

---

## Response Timeline

- **Acknowledgment**: Within 48 hours of report submission.
- **Triage & Assessment**: Within 5 business days.
- **Fix & Coordinated Disclosure**: Security patches will be released as high-priority patch versions.

---

## Physical Network Security Best Practices

OSRS binds by default to `http://0.0.0.0:8000` to allow local network laboratory access. If operating in an untrusted or public Wi-Fi network:
- Bind FastAPI exclusively to `127.0.0.1` in production or use an authenticated reverse proxy (e.g., NGINX / Caddy with HTTPS and basic auth).
- Never expose the hardware control port (`POST /api/motors/torque`, `POST /api/command`) directly to the public internet.
