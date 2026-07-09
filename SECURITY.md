<!-- SPDX-FileCopyrightText: 2024 - GitHub user: fredericks1982
SPDX-License-Identifier: Apache-2.0 -->

# Security policy

## Network security model

CAME ETI/Domo servers expose their API over **plain HTTP only**. All traffic exchanged
by this library with the server — including the username and password sent at login —
travels **unencrypted** on the local network. This is a limitation of the CAME hardware
and its proprietary protocol, **not of this library**: the official CAME clients
communicate the same way, and the server offers no TLS/HTTPS endpoint.

The resulting threat model is: anyone able to observe traffic on the network segment
where the CAME server lives can capture the credentials and control the plant. We
therefore recommend to:

- Keep the CAME server on a **trusted local network** (ideally a dedicated VLAN or an
  isolated IoT network segment).
- **Never expose** the CAME server's HTTP port directly to the internet (no port
  forwarding). For remote access, use a **VPN** into the home network.
- Use a **dedicated CAME user** with a password not reused for any other service.

What the library does on its side:

- Credentials are **never persisted to disk** and are kept **encrypted in memory**
  (runtime-generated key), cleared on disposal.
- Passwords, client IDs, and other sensitive values are **automatically redacted**
  from debug and traffic logs, so logs can be shared safely for troubleshooting.

## Supported versions

This section to tell users about which versions of this project are currently being
supported with security updates.

| Version | Supported |
| ------- | --------- |
| 1.0.x   | ✅         |
| 1.0.x   | ❌         |
| 0.x.    | ❌         |

## Reporting a vulnerability

The security of our project is a top priority. If you discover a security vulnerability
within our project, we kindly ask you to follow these steps:

1. **Do Not publicly disclose**: Please do not open issues for vulnerabilities on
    GitHub or discuss them in public forums. Instead, contact us directly.
2. **Contact**: Send an email to the maintainers with a detailed description of the
   issue. Include steps to reproduce the vulnerability, its impact, and any other
   information that may help us understand the severity and urgency.
3. **Response time**: We aim to respond to security reports as soon as possible,
    acknowledging receipt of your report, and will provide a timeline for the fix and
    disclosure process after initial investigation.

## Security measures

Our project undergoes continuous integration and deployment (CI/CD), incorporating various security and code quality tools to ensure the safety and reliability of our codebase. Here are some of the measures and tools we use:

- **Static code analysis**: We use `mypy`, `pylint`, `flake8`, and `black` to enforce coding standards and identify potential issues.
- **Security scanning**: `bandit` and `gitguardian` scan our code for security vulnerabilities and secrets, respectively.
- **Dependencies security**: `Dependabot` scans our dependencies for known vulnerabilities and automatically creates pull requests to update them.
- **Automated testing**: `pytest` ensures that our code behaves as expected and that new changes do not introduce regressions.

## External audit

While we do our best to secure our project, we also believe in the power of community and external verification. We encourage security researchers and experts to audit our code and welcome any feedback or recommendations for improving our security posture.

## Acknowledgements

We appreciate the time and effort the community spends on helping us ensure the security of our project. Contributors who report vulnerabilities and help us improve our security will be acknowledged in our project's documentation (unless they prefer to remain anonymous).

Thank you for helping us keep our project safe.
