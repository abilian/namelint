# CI and pre-commit

## GitHub Actions

`--output-format github` turns each finding into an annotation on the pull request's diff:

```yaml
- run: uvx namelint check --output-format github
```

namelint exits 1 when it reports findings, which fails the step. To annotate without failing, add `--exit-zero`.

## Other CI systems

With `--output-format concise`, each finding is one `path:line:col: CODE message` line, which most CI annotators and editors parse:

```sh
namelint check --output-format concise
```

## pre-commit

Add the hook to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/abilian/namelinter
  rev: v0.3.0
  hooks:
    - id: namelint
```

The hook runs `namelint check --force-exclude`. pre-commit names each file it passes, and `--force-exclude` keeps the `exclude` patterns in force for named files.
