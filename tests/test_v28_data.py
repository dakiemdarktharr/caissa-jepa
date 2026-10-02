import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from two_player.v28_data import (
    DATA_VERSION, POLICIES, SPLITS, V28_GAMES, _closure_keys,
    _policy_family_hashes, audit, choose_action, digest, generate_trajectory,
    replay, source_hash, trajectory_fingerprint,
)
from two_player.v28_development import load_development_split


class V28DataTests(unittest.TestCase):
    def test_development_loader_binds_exact_unapproved_data_and_split_scope(self):
        with tempfile.TemporaryDirectory() as unpinned:
            with self.assertRaisesRegex(ValueError, "exact audited DEV09"):
                load_development_split(Path(unpinned) / "dataset", "train",
                                       Path(unpinned) / "approval.json")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "dataset"
            data_dir.mkdir()
            records = [{"split": "train"}]
            audit_report = {"status": "PASSED", "dataset_fingerprint": "b" * 64,
                            "records_fingerprint": digest(records)}
            trajectories_bytes = b'{"fixture": true}\n'
            records_bytes = b'{"split": "train"}\n'
            (data_dir / "trajectories.jsonl").write_bytes(trajectories_bytes)
            (data_dir / "records.jsonl").write_bytes(records_bytes)
            manifest = {"schema": DATA_VERSION, "audit_passed": True,
                        "training_approved": False,
                        "source_sha256": source_hash(),
                        "policy_family_hashes": _policy_family_hashes(),
                        "audit": audit_report,
                        "artifacts": {"records.jsonl": {"sha256": "c" * 64},
                                      "trajectories.jsonl": {"sha256": "d" * 64}}}
            manifest["artifacts"]["records.jsonl"] = {
                "sha256": hashlib.sha256(records_bytes).hexdigest(),
                "bytes": len(records_bytes)}
            manifest["artifacts"]["trajectories.jsonl"] = {
                "sha256": hashlib.sha256(trajectories_bytes).hexdigest(),
                "bytes": len(trajectories_bytes)}
            raw_manifest = json.dumps(manifest, sort_keys=True).encode("utf-8")
            (data_dir / "manifest.json").write_bytes(raw_manifest)
            amendment = (Path(__file__).resolve().parents[1] / "docs" /
                         "V28_DEVELOPMENT_FIT_AMENDMENT_01.md")
            panel_spec = (Path(__file__).resolve().parents[1] / "docs" /
                          "validation" / "V28_DEV_FIT_PANEL_V01.json")
            loader_source = (Path(__file__).resolve().parents[1] / "two_player" /
                             "v28_development.py")
            approval = {"schema": "caissa-jepa-development-fit-approval-v01",
                        "scope": "development-only",
                        "protocol": "V28_DEVELOPMENT_FIT_AMENDMENT_01",
                        "fit_split": "train",
                        "evaluation_splits": ["validation", "selection"],
                        "training_approved_manifest": False,
                        "dataset": {
                            "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
                            "source_sha256": manifest["source_sha256"],
                            "dataset_fingerprint": "b" * 64,
                            "audit_sha256": hashlib.sha256(json.dumps(
                                manifest["audit"], sort_keys=True, separators=(",", ":"),
                                allow_nan=False).encode("utf-8")).hexdigest(),
                            "records_sha256": manifest["artifacts"]["records.jsonl"]["sha256"],
                            "trajectories_sha256": manifest["artifacts"]["trajectories.jsonl"]["sha256"]},
                        "amendment_sha256": hashlib.sha256(
                            amendment.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                        "panel_spec_sha256": hashlib.sha256(
                            panel_spec.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                        "loader_sha256": hashlib.sha256(
                            loader_source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()}
            approval_path = root / "approval.json"
            approval_path.write_text(json.dumps(approval), encoding="utf-8")
            with patch("two_player.v28_development.DATASET_ROOT", data_dir.resolve()), \
                    patch("two_player.v28_development.EXPECTED_DATA", approval["dataset"]), \
                    patch("two_player.v28_development.validate_development_spec"), \
                    patch("two_player.v28_development.v28_data.audit",
                          return_value=(records, audit_report)) as loader:
                records, fingerprint, grant_sha = load_development_split(
                    data_dir, "train", approval_path)
                self.assertEqual(records, [{"split": "train"}])
                self.assertEqual(fingerprint, "b" * 64)
                self.assertEqual(len(grant_sha), 64)
                loader.assert_called_once()
                with self.assertRaisesRegex(ValueError, "refuses locked-final"):
                    load_development_split(data_dir, "locked-final", approval_path)
            manifest["audit"]["dataset_fingerprint"] = "e" * 64
            (data_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exact audited DEV09"):
                load_development_split(data_dir, "train", approval_path)

    def test_registered_games_match_candidate_scope_and_shared_tensor_contract(self):
        self.assertEqual(set(V28_GAMES), {"connect4-gravity-6x7", "reversi6"})
        self.assertEqual(set(POLICIES), {"uniform", "tactical", "positional", "bounded-search"})
        self.assertIn("locked-final", SPLITS)
        for game in V28_GAMES.values():
            state = game.initial()
            game.validate(state)
            self.assertTrue(game.legal_actions(state))
            self.assertEqual(game.features(state).shape, (198,))

    def test_all_policy_families_choose_only_legal_moves_on_both_games(self):
        import numpy as np
        for game in V28_GAMES.values():
            state = game.initial()
            for family in POLICIES:
                action, _ = choose_action(game, state, family, np.random.default_rng(19))
                self.assertIn(action, game.legal_actions(state), (game.name, family))

    def test_trajectory_generation_is_reproducible_and_replay_valid(self):
        for game in V28_GAMES.values():
            left = generate_trajectory(game, "train", 7, 28093041)
            right = generate_trajectory(game, "train", 7, 28093041)
            self.assertEqual(left, right)
            self.assertEqual(left["schema"], DATA_VERSION)
            self.assertEqual(left["provenance"], "project-owned rules and policies; generated self-play")
            self.assertIn(left["policies_by_player"]["+1"], {"uniform", "tactical"})
            self.assertIn(left["policies_by_player"]["-1"], {"uniform", "tactical"})
            states = replay(left)
            self.assertEqual(len(states), len(left["actions"]) + 1)
            self.assertEqual(game.terminal(states[-1]), left["outcome"])
        reversi = V28_GAMES["reversi6"]
        for seed in range(12):
            self.assertIsNotNone(reversi.terminal(replay(generate_trajectory(reversi, "train", seed, 1000 + seed))[-1]))

    def test_policy_families_are_held_out_by_split(self):
        game = V28_GAMES["reversi6"]
        for split, expected in (("train", {"uniform", "tactical"}),
                                ("validation", {"uniform", "tactical"}),
                                ("selection", {"positional"}),
                                ("locked-final", {"bounded-search"})):
            row = generate_trajectory(game, split, 2, 321)
            self.assertEqual(set(row["policies_by_player"].values()), expected)

    def test_counterfactual_closure_enumerates_all_legal_reply_successors(self):
        for game in V28_GAMES.values():
            state = game.initial()
            keys = _closure_keys(game, state)
            own_actions = game.legal_actions(state)
            expected_min = len(own_actions) * 2
            self.assertGreaterEqual(len(keys), expected_min, game.name)
            for action in own_actions:
                after = game.transition(state, action)
                for reply in game.legal_actions(after):
                    game.validate(game.transition(after, reply))

    def test_fingerprint_is_stable_and_changes_with_game_identity(self):
        game = V28_GAMES["connect4-gravity-6x7"]
        row = generate_trajectory(game, "train", 1, 99)
        states = replay(row)
        fingerprint = trajectory_fingerprint(game, states, row["actions"], row["outcome"])
        self.assertEqual(fingerprint, trajectory_fingerprint(game, states, row["actions"], row["outcome"]))
        self.assertEqual(len(fingerprint), 64)

    def test_malformed_trajectory_fails_closed_without_crashing_audit(self):
        from two_player.v28_data import audit
        _, report = audit([{"schema": "wrong", "game": "missing"}])
        self.assertEqual(report["status"], "FAILED")
        self.assertTrue(any("malformed" in str(error) for error in report["errors"]))
        self.assertEqual(report["counts"]["illegal_or_malformed_trajectory"], 1)

    def test_duplicate_trajectory_cannot_cross_split_boundary(self):
        from two_player.v28_data import audit
        game = V28_GAMES["connect4-gravity-6x7"]
        train = generate_trajectory(game, "train", 0, 8831)
        validation = dict(train, split="validation")
        _, report = audit([train, validation])
        self.assertEqual(report["counts"]["duplicate_cross_split"], 1)
        self.assertTrue(any("duplicate trajectory crosses" in str(error) for error in report["errors"]))

    def test_symmetry_equivalent_trajectory_is_duplicate(self):
        from two_player.v28_data import replay
        game = V28_GAMES["connect4-gravity-6x7"]
        original = generate_trajectory(game, "train", 3, 55491)
        mapping = game.transforms()[1]
        transformed_states = [game.transform(state, 64, mapping)[0] for state in replay(original)]
        transformed_actions = [game.transform(replay(original)[i], action, mapping)[1]
                               for i, action in enumerate(original["actions"])]
        self.assertEqual(trajectory_fingerprint(game, replay(original), original["actions"], original["outcome"]),
                         trajectory_fingerprint(game, transformed_states, transformed_actions, original["outcome"]))

    def test_shared_counterfactual_targets_join_component_before_split(self):
        from two_player.v28_data import _component_assign, replay, trajectory_fingerprint
        game = V28_GAMES["connect4-gravity-6x7"]
        left = generate_trajectory(game, "train", 4, 55101)
        right = generate_trajectory(game, "validation", 4, 55101)
        assigned, receipt = _component_assign([left, right])
        self.assertEqual(len(assigned), 1)
        self.assertFalse(receipt["quarantined"])
        fingerprints = {trajectory_fingerprint(game, replay(row), row["actions"], row["outcome"])
                        for row in (left, right)}
        joined = [component for component in receipt["components"]
                  if fingerprints.issubset(set(component["fingerprints"]))]
        self.assertEqual(len(joined), 1)
        self.assertEqual(joined[0]["source_splits"], ["train", "validation"])
        self.assertEqual({row["split"] for row in assigned}, {joined[0]["assigned_split"]})

    def test_loader_never_opens_locked_final(self):
        from two_player.v28_data import load_split
        with self.assertRaisesRegex(ValueError, "refuses locked-final"):
            load_split("unused", "locked-final")

    def test_missing_or_miskeyed_policy_metadata_is_rejected_without_crash(self):
        from two_player.v28_data import audit, build_records
        row = generate_trajectory(V28_GAMES["connect4-gravity-6x7"], "train", 0, 17)
        row["policies_by_player"] = {"+1": "uniform", "player-2": "tactical"}
        with self.assertRaisesRegex(ValueError, "before data audit passes"):
            build_records([row])
        _, report = audit([row])
        self.assertEqual(report["status"], "FAILED")

    def test_failed_audit_does_not_return_internal_model_facing_rows(self):
        from two_player.v28_data import audit
        row = generate_trajectory(V28_GAMES["connect4-gravity-6x7"], "train", 0, 8832)
        rows, report = audit([row])
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(rows, [])

    def test_failed_generation_never_publishes_model_facing_records(self):
        import json
        import tempfile
        from pathlib import Path
        from two_player.v28_data import generate_dataset, load_split
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "pilot"
            manifest = generate_dataset(destination, protocol_id="unit-diagnostic",
                                        episodes_per_game_split=1, seed=883001)
            self.assertFalse(manifest["audit_passed"])
            self.assertFalse(manifest["training_approved"])
            self.assertNotIn("records.jsonl", manifest["artifacts"])
            self.assertFalse((destination / "records.jsonl").exists())
            self.assertTrue((destination / "trajectories.jsonl").exists())
            with self.assertRaisesRegex(ValueError, "not passed audit"):
                load_split(destination, "train")

    def test_audit_enforces_support_floor_for_each_development_split(self):
        from two_player.v28_data import audit
        game = V28_GAMES["connect4-gravity-6x7"]
        rows = [generate_trajectory(game, split, 0, 7000 + i)
                for i, split in enumerate(("train", "validation", "selection"))]
        _, report = audit(rows)
        failed_groups = {item.get("group") for item in report["errors"]
                         if item.get("reason") == "support floor failed"}
        self.assertEqual(failed_groups, {f"{game_name}/{split}"
                                         for game_name in V28_GAMES
                                         for split in ("train", "validation", "selection")})

    def test_audit_requires_regenerable_lineage(self):
        from two_player.v28_data import audit
        row = generate_trajectory(V28_GAMES["connect4-gravity-6x7"], "train", 0, 8101)
        row.pop("seed")
        _, report = audit([row])
        self.assertEqual(report["counts"]["illegal_or_malformed_trajectory"], 1)
        self.assertEqual(report["status"], "FAILED")

    def test_component_assignment_keeps_each_component_in_one_split(self):
        from two_player.v28_data import _component_assign, audit
        game = V28_GAMES["connect4-gravity-6x7"]
        candidates = [generate_trajectory(game, "train", i, 71400 + i) for i in range(12)]
        candidates += [generate_trajectory(game, "validation", i, 82900 + i) for i in range(12)]
        assigned, receipt = _component_assign(candidates)
        _, report = audit(assigned)
        self.assertFalse(receipt["quarantined"])
        self.assertEqual(report["overlap_components"]["mixed_split_count"], 0)

    def test_duplicate_path_carries_all_family_lineage_into_quarantine(self):
        from unittest.mock import patch
        import two_player.v28_data as data_module
        game = V28_GAMES["connect4-gravity-6x7"]
        training = generate_trajectory(game, "train", 2, 71701)
        heldout = dict(training, split="selection", source_split="selection",
                       policies_by_player={"+1": "positional", "-1": "positional"})
        states = replay(training)
        with patch.object(data_module, "replay", return_value=states):
            assigned, receipt = data_module._component_assign([training, heldout])
        self.assertEqual(assigned, [])
        self.assertEqual(len(receipt["quarantined"]), 1)
        self.assertEqual(set(receipt["quarantined"][0]["families"]),
                         {"uniform", "tactical", "positional"})

    def test_formal_generation_rejects_unfrozen_quota_or_seed(self):
        import tempfile
        from pathlib import Path
        from two_player.v28_data import generate_dataset
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "named, frozen"):
                generate_dataset(Path(temp) / "bad", protocol_id="dev09-v1",
                                 episodes_per_game_split=49, seed=28094007)

    def test_formal_generation_rejects_duplicate_omitted_or_reordered_splits(self):
        import tempfile
        from pathlib import Path
        from two_player.v28_data import generate_dataset
        with tempfile.TemporaryDirectory() as temp:
            for index, splits in enumerate((("train", "train", "validation", "selection"),
                                            ("train", "validation"),
                                            ("validation", "train", "selection"))):
                with self.subTest(splits=splits), self.assertRaisesRegex(ValueError, "split schedule"):
                    generate_dataset(Path(temp) / f"bad-{index}", protocol_id="dev09-v1",
                                     episodes_per_game_split=48, seed=28094007, splits=splits)

    def test_audit_and_public_record_builder_reject_alternate_phase_threshold(self):
        from two_player.v28_data import audit, build_records
        row = generate_trajectory(V28_GAMES["connect4-gravity-6x7"], "train", 0, 9101)
        with self.assertRaisesRegex(ValueError, "phase threshold is frozen"):
            audit([row], min_phase=0.0)
        with self.assertRaisesRegex(ValueError, "phase threshold is frozen"):
            build_records([row], min_phase=0.0)


if __name__ == "__main__":
    unittest.main()
