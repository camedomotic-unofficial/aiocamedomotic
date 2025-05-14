<!-- Copyright 2024 - GitHub user: fredericks1982

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.  -->

# Security policy

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
2. **Contact**: Send an email to the mantainers with a detailed description of the
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
