# 🚀 Release Workflow

> How to release a new version of kimi-mem. **No direct pushes to `main`.**

---

## 📋 Checklist

- [ ] All changes are on a feature branch (`feat/`, `fix/`, `docs/`)
- [ ] CI passes (tests + linter) on the PR
- [ ] CHANGELOG.md updated with `[Unreleased]` → `[X.Y.Z]` section
- [ ] Version bumped in `kimi_mem/__init__.py` and `pyproject.toml`
- [ ] PR reviewed and merged to `main`
- [ ] Git tag `vX.Y.Z` created on the merge commit
- [ ] Tag pushed to GitHub (`git push origin vX.Y.Z`)
- [ ] Release workflow completes (CI → build → PyPI publish)

---

## 🔀 Step-by-Step

### 1. Create a feature branch

```bash
git checkout main
git pull origin main
git checkout -b feat/descriptive-name
```

### 2. Make changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add new Setup hook"
git commit -m "fix: correct uninstall logic"
git commit -m "test: add MCP server tests"
```

### 3. Push branch and open PR

```bash
git push origin feat/descriptive-name
gh pr create --title "feat: descriptive title" --body "What changed and why."
```

Wait for CI to pass ✅

### 4. Merge PR

```bash
gh pr merge --squash --delete-branch
```

**Never push directly to `main`.**

### 5. Tag the release

```bash
git checkout main
git pull origin main
git tag -a v0.2.2 -m "Release v0.2.2: what changed"
git push origin v0.2.2
```

### 6. Verify

- GitHub Actions: CI passes → Release builds → PyPI publishes
- Check: https://pypi.org/project/kimi-mem/

---

## ⚠️ Never Do This

| ❌ Bad | ✅ Good |
|--------|---------|
| `git push origin main` | Open PR → merge |
| Delete and recreate a tag | Tag once, correctly |
| Skip CHANGELOG | Always update CHANGELOG.md |
| Skip version bump | Bump `__init__.py` + `pyproject.toml` |

---

## 🔧 Emergency Hotfix

If a critical bug is found in a released version:

1. Branch from the tag: `git checkout -b hotfix/v0.2.2 v0.2.1`
2. Fix, commit, PR, merge to `main`
3. Tag new version: `v0.2.2`

---

## 🏷️ Versioning

We follow [SemVer](https://semver.org/):

- `MAJOR` — breaking changes (rare in alpha)
- `MINOR` — new features, backward compatible
- `PATCH` — bug fixes only

Pre-1.0: `0.MINOR.PATCH` — minor bumps are acceptable for new features.

---

*Last updated: 2026-05-15*
