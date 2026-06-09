# Task 2: Integrate into Local Check Script
- [ ] Modify `scripts/check.sh` to include `scripts/test_gui_init.py` as step 5/5
- [ ] Implement `xvfb-run` fallback logic in `scripts/check.sh`
- [ ] Verify `scripts/check.sh` locally

# Task 3: Integrate into GitHub Actions
- [ ] Modify `.github/workflows/ci.yml` to include the GUI integration test step
- [ ] Use `xvfb-run` for the GUI integration test in CI
- [ ] Verify YAML syntax
