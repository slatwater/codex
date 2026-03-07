# Contributing

Thank you for your interest in contributing!

## Prerequisites

- [Git](https://git-scm.com/) 2.30+
- [Node.js](https://nodejs.org/) 18+ (LTS recommended)
- npm 9+ (bundled with Node.js)

## Getting Started

1. **Clone the repository**

   ```bash
   git clone https://github.com/slatwater/codex.git
   cd codex
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Run the project**

   ```bash
   npm start
   ```

   For development with live reload:

   ```bash
   npm run dev
   ```

## Code Style

- Follow the existing code style in each file.
- Run `npm run lint` before committing to catch style issues.
- Keep functions small and focused; add comments only when intent is non-obvious.
- Prefer clarity over cleverness.

## Submitting a Pull Request

1. Fork the repo and create a branch from `main`:

   ```bash
   git checkout -b your-feature-name
   ```

2. Make your changes and ensure linting passes (`npm run lint`).

3. Commit with a clear message describing *what* and *why*:

   ```bash
   git commit -m "feat: add X to solve Y"
   ```

4. Push your branch and open a PR against `main`:

   ```bash
   git push origin your-feature-name
   ```

5. Fill in the PR description, link any related issues, and request a review.

> PRs are typically reviewed within a few business days. Address feedback
> promptly to keep things moving.
