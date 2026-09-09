# Testing & Evidence — Nihal's Module

This folder is owned by **Nihal**.

## What to build
1. `interrupt_test.py` — Automated test script that:
   - Connects to LiveKit room
   - Triggers a 15-second agent response
   - Sends "stop" interrupt after 3 seconds
   - Measures timestamp diff (interrupt latency)
   - Repeats 5 times
   - Outputs results to `RIME_EVIDENCE.md`
2. `dashboard.py` — Simple status/logging dashboard showing:
   - "Rime active" status
   - Live latency numbers
   - Pipeline health check
3. `RIME_EVIDENCE.md` — Auto-generated evidence document with measured numbers

## Integration point
Test script connects to the same LiveKit room as `agent.py` and sends audio/data to trigger responses.

## Key files to create
- `interrupt_test.py` — Main test harness
- `dashboard.py` — Status dashboard
- `RIME_EVIDENCE.md` — Generated evidence (don't manually edit)
- `test_config.py` — Test configuration (room name, timing params)
