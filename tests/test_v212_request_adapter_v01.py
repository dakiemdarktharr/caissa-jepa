import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from two_player.v212_pilot import (
    RandomInferenceModel,
    Root,
    VARIANTS,
    _state_sha256,
    run_root_arm,
)
from two_player.v212_request_adapter_v01 import (
    EXPECTED_MEMORY_MAX,
    _run_worker_process,
    _search_action,
    current_cgroup_info,
    run_move_request,
    verify_memory_scope,
    verify_worker_scope,
)


class V212RequestAdapterV01Tests(unittest.TestCase):
    def _scope_snapshots(self, events_after=None):
        events_before = {"low": 0, "max": 0, "oom": 0,
                         "oom_kill": 0, "oom_group_kill": 0}
        scope = {"path": "/user.slice/request.scope",
                 "memory_max": EXPECTED_MEMORY_MAX,
                 "memory_oom_group": 0}
        before = {**scope, "events": events_before}
        after = {**scope, "events": events_after or events_before}
        return before, after, scope

    def _worker_reply(self, game, state, scope, *, depth=4,
                      stop_reason="depth_4_complete"):
        return {
            "action": game.legal_actions(state)[0],
            "completed_depth": depth,
            "stop_reason": stop_reason,
            "search_wall_seconds": 0.01,
            "node_visits": 1,
            "worker_cgroup_path": scope["path"],
            "worker_memory_max": scope["memory_max"],
        }

    def test_cgroup_reader_requires_a_finite_contained_v2_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            leaf = root / "scope.slice" / "worker.scope"
            leaf.mkdir(parents=True)
            proc = root / "proc-cgroup"
            proc.write_text("0::/scope.slice/worker.scope\n", encoding="utf-8")
            (leaf / "memory.max").write_text("1610612736\n", encoding="ascii")
            (leaf / "memory.events").write_text(
                "low 0\nmax 1\noom 0\noom_kill 0\noom_group_kill 0\n",
                encoding="ascii",
            )
            (leaf / "memory.oom.group").write_text("0\n", encoding="ascii")
            info = verify_memory_scope(1610612736, proc, root)
            self.assertEqual(info["path"], "/scope.slice/worker.scope")
            self.assertEqual(info["memory_max"], 1610612736)
            self.assertEqual(info["events"]["oom_kill"], 0)

            (leaf / "memory.max").write_text("max\n", encoding="ascii")
            with self.assertRaisesRegex(RuntimeError, "not finite"):
                current_cgroup_info(proc, root)

            (leaf / "memory.max").write_text("1610612736\n", encoding="ascii")
            (leaf / "memory.oom.group").write_text("1\n", encoding="ascii")
            with self.assertRaisesRegex(RuntimeError, "does not guarantee the supervisor survives"):
                verify_memory_scope(1610612736, proc, root)

            proc.write_text("0::/../../outside\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "escapes"):
                current_cgroup_info(proc, root)

    def test_request_returns_a_legal_action_without_recording_it_in_counters(self):
        game = next(game for game in VARIANTS
                    if game.name == "connect4-gravity-6x7")
        state = game.initial()
        root = Root(game.name, 0, 1, _state_sha256(game, state), state)
        before, after, scope = self._scope_snapshots()
        reply = self._worker_reply(game, state, scope)
        with patch(
            "two_player.v212_request_adapter_v01.verify_memory_scope",
            side_effect=[before, after],
        ), patch(
            "two_player.v212_request_adapter_v01._run_worker_process",
            return_value={"timed_out": False, "returncode": 0,
                          "reply": reply},
        ):
            response = run_move_request(
                game, root, "direct-leaf-value", model_seed=1,
            )
        self.assertEqual(response["status"], "response")
        self.assertIn(response["action"], game.legal_actions(state))
        self.assertEqual(response["completed_depth"], 4)
        self.assertNotIn("action", response["counters"])
        self.assertLess(response["request_wall_seconds"], 6.0)

    def test_request_deadline_includes_worker_startup_and_uses_legal_fallback(self):
        game = next(game for game in VARIANTS
                    if game.name == "connect4-gravity-6x7")
        state = game.initial()
        root = Root(game.name, 0, 1, _state_sha256(game, state), state)
        before, after, scope = self._scope_snapshots()
        reply = self._worker_reply(
            game, state, scope, depth=0, stop_reason="wall_cap"
        )
        request_payload = {}

        def delayed_worker(_command, payload, _deadline):
            request_payload.update(payload)
            time.sleep(0.02)
            return {"timed_out": False, "returncode": 0, "reply": reply}

        with patch(
            "two_player.v212_request_adapter_v01.verify_memory_scope",
            side_effect=[before, after],
        ), patch(
            "two_player.v212_request_adapter_v01._run_worker_process",
            side_effect=delayed_worker,
        ):
            response = run_move_request(
                game, root, "direct-leaf-value", model_seed=1,
                planner_seconds=0.001,
            )
        self.assertEqual(response["status"], "controlled_fallback")
        self.assertEqual(response["reason"], "wall_cap")
        self.assertEqual(response["completed_depth"], 0)
        self.assertEqual(response["action"], game.legal_actions(state)[0])
        self.assertLess(request_payload["planner_deadline"], time.monotonic())

    def test_request_search_counters_match_frozen_search_on_complete_fixture(self):
        game = next(game for game in VARIANTS
                    if game.name == "connect4-gravity-6x7")
        state = game.initial()
        root = Root(game.name, 0, 1, _state_sha256(game, state), state)
        for arm in ("direct-leaf-value", "multi-step-jepa"):
            with self.subTest(arm=arm):
                frozen_model = RandomInferenceModel(arm, seed=1)
                expected = run_root_arm(
                    game, root, frozen_model, node_cap=10_000,
                    wall_cap_seconds=5.0,
                )
                request_model = RandomInferenceModel(arm, seed=1)
                started = time.monotonic()
                actual = _search_action(
                    game, root, request_model, started, started + 5.0,
                    node_cap=10_000, rss_cap_bytes=2**63 - 1,
                )
                self.assertEqual(actual["completed_depth"], 4)
                self.assertIn(actual["action"], game.legal_actions(state))
                for name in (
                    "node_visits", "transition_calls", "encoder_calls",
                    "predictor_calls", "decoder_calls", "value_calls",
                    "model_calls", "terminal_nodes",
                ):
                    self.assertEqual(actual[name], expected[name], name)

    def test_response_watchdog_kills_and_reaps_stalled_worker(self):
        supervised = _run_worker_process(
            [sys.executable, "-c", "import time; time.sleep(10)"], {},
            time.monotonic() + 0.05,
        )
        self.assertTrue(supervised["timed_out"])
        self.assertEqual(supervised["returncode"], -signal.SIGKILL)
        self.assertTrue(supervised["worker_reaped"])

    def test_request_classifies_a_new_cgroup_oom_as_forfeit(self):
        game = next(game for game in VARIANTS
                    if game.name == "connect4-gravity-6x7")
        state = game.initial()
        root = Root(game.name, 0, 1, _state_sha256(game, state), state)
        events_after = {"low": 0, "max": 1, "oom": 1,
                        "oom_kill": 1, "oom_group_kill": 0}
        before, after, scope = self._scope_snapshots(events_after)
        reply = self._worker_reply(game, state, scope)
        with patch(
            "two_player.v212_request_adapter_v01.verify_memory_scope",
            side_effect=[before, after],
        ), patch(
            "two_player.v212_request_adapter_v01._run_worker_process",
            return_value={"timed_out": False, "returncode": 0,
                          "reply": reply},
        ):
            response = run_move_request(
                game, root, "direct-leaf-value", model_seed=1,
            )
        self.assertEqual(response["status"], "forfeit")
        self.assertEqual(response["reason"], "memory_cgroup_oom")
        self.assertEqual(response["cgroup_event_delta"]["oom_kill"], 1)

    def test_scope_preflight_requires_child_to_inherit_exact_cgroup(self):
        info = {
            "path": "/user.slice/request.scope",
            "memory_max": EXPECTED_MEMORY_MAX,
            "memory_oom_group": 0,
            "events": {"oom_kill": 0},
        }
        with patch(
            "two_player.v212_request_adapter_v01.verify_memory_scope",
            return_value=info,
        ), patch(
            "two_player.v212_request_adapter_v01._run_worker_process",
            return_value={"timed_out": False, "returncode": 0,
                          "reply": info},
        ):
            result = verify_worker_scope()
        self.assertTrue(result["same_cgroup"])
        self.assertEqual(result["parent"]["path"], result["worker"]["path"])
        wrong_worker = {**info, "path": "/user.slice/unbounded.scope"}
        with patch(
            "two_player.v212_request_adapter_v01.verify_memory_scope",
            return_value=info,
        ), patch(
            "two_player.v212_request_adapter_v01._run_worker_process",
            return_value={"timed_out": False, "returncode": 0,
                          "reply": wrong_worker},
        ), self.assertRaisesRegex(RuntimeError, "did not inherit"):
            verify_worker_scope()


if __name__ == "__main__":
    unittest.main()
