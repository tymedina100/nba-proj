# Contributing to NBA-Proj

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, collaborative, and constructive. We're all here to build something useful together.

## Getting Started

### Development Setup

1. **Fork and clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/nba-proj.git
cd nba-proj
```

2. **Set up your development environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"  # Install with development dependencies
```

3. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Code Style

We follow Python best practices and PEP 8 conventions:

- **Formatting**: Use `black` for code formatting
  ```bash
  black src/ tests/
  ```

- **Linting**: Use `flake8` for style checks
  ```bash
  flake8 src/ tests/
  ```

- **Type Hints**: Use type annotations where appropriate
  ```python
  def simulate_player(player_id: str, date: str) -> Dict[str, Any]:
      ...
  ```

- **Docstrings**: Follow NumPy/Google style
  ```python
  def calculate_prior(stats: pd.DataFrame) -> GammaParams:
      """Calculate Gamma prior parameters from historical stats.
      
      Args:
          stats: DataFrame with player statistics
          
      Returns:
          GammaParams object with shape and rate
          
      Raises:
          ValueError: If stats DataFrame is empty
      """
  ```

### Testing

All new features and bug fixes should include tests.

**Running tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/nba_proj --cov-report=html

# Run specific test file
pytest tests/test_simulation.py

# Run tests matching a pattern
pytest -k "test_gamma_poisson"
```

**Writing tests:**
- Place tests in the `tests/` directory
- Mirror the structure of `src/`
- Use descriptive test names: `test_simulate_returns_valid_distribution`
- Include edge cases and error conditions

```python
def test_gamma_poisson_simulation():
    """Test that Gamma-Poisson simulation produces valid outputs."""
    shape, rate = 10.0, 2.0
    n_simulations = 1000
    
    results = simulate_gamma_poisson(shape, rate, n_simulations)
    
    assert len(results) == n_simulations
    assert all(r >= 0 for r in results)
    assert 4 < np.mean(results) < 6  # Expected value is shape/rate = 5
```

### Commits

**Commit messages should be clear and descriptive:**

```
Add Gamma-Poisson simulation for player stats

- Implement conjugate prior calculation
- Add posterior predictive sampling
- Include unit tests for edge cases
```

**Conventional Commits format (optional but recommended):**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

## Pull Request Process

1. **Update your branch with main**
```bash
git fetch origin
git rebase origin/main
```

2. **Run the full test suite**
```bash
pytest
black src/ tests/
flake8 src/ tests/
```

3. **Update documentation** if you've added features or changed behavior

4. **Submit your PR** with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to related issues (e.g., "Closes #123")
   - Screenshots/examples if applicable

5. **Respond to review feedback** promptly

### PR Checklist

- [ ] Tests pass locally
- [ ] Code is formatted with `black`
- [ ] No linting errors from `flake8`
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

## Project-Specific Guidelines

### Data Pipeline Contributions

When modifying the ETL or simulation pipeline:

- Maintain date-based reproducibility
- Ensure outputs land in `runs/YYYY-MM-DD/`
- Add logging for debugging
- Handle missing data gracefully

### Model Improvements

When changing statistical models:

- Document the mathematical approach
- Compare against baseline performance
- Include validation/backtesting results
- Add diagnostic plots

### API Changes

When modifying the API:

- Maintain backward compatibility when possible
- Update API documentation
- Add integration tests
- Version the API if breaking changes are necessary

## Areas for Contribution

### Good First Issues

Look for issues tagged `good-first-issue`:
- Documentation improvements
- Test coverage increases
- Minor bug fixes
- Code cleanup

### High-Priority Areas

- **Data Sources**: Add new data providers
- **Statistics**: Implement additional player props (3PM, STL, BLK, TO)
- **Performance**: Optimize simulation speed
- **Visualization**: Create diagnostic plots
- **Testing**: Increase coverage

### Feature Requests

Have an idea? Open an issue first to discuss:
1. Describe the feature and use case
2. Outline the proposed implementation
3. Get feedback before coding

## Questions?

- Check the [documentation](docs/)
- Search [existing issues](https://github.com/tymedina100/nba-proj/issues)
- Open a new issue with the question tag

## Recognition

Contributors will be acknowledged in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for helping make NBA-Proj better!