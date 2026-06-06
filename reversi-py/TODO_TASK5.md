# Task 5: Non-blocking AI Moves TODO

- [ ] Import `threading` and `queue` in `main.py`
- [ ] Initialize AI state in `App.__init__` (`self.ai_thread`, `self.ai_queue`, `self.is_ai_thinking`)
- [ ] Refactor `App._handle_ai_or_pass` to start AI thread
- [ ] Implement `App._run_ai_agent` worker
- [ ] Update `App._update_state` to poll `self.ai_queue`
- [ ] Prevent human move while `self.is_ai_thinking` is True
- [ ] Show "Thinking..." message during AI moves
- [ ] Update and run tests to verify threaded AI moves
