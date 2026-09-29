"""Redaction and availability invariants on synthetic legal fixtures, no fitting."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from two_player.data import digest
from two_player.games import State
from two_player_v2 import GAMES_V2
from two_player_v2.data import closure, state_from
from two_player_v22 import data


def fixture_parent(split="train"):
    """Legal forks with deterministic synthetic labels, not solved research data."""
    roots, nodes, forks = [], {}, []
    for name, game in GAMES_V2.items():
        if game.gravity:
            state = game.initial()
            for action in (24, 28, 25, 20, 26, 12):
                state = game.transition(state, action)
        else:
            state = State((0, 1, -1, -1, -1, -1)+(-1,)*30, 1)
        transformed, _ = game.transform(state, 64, game.transforms()[1])
        states = [state, transformed]
        for seed in range(12, 200):
            rng = np.random.default_rng(seed)
            candidate = game.initial()
            for _ in range(8):
                if game.terminal(candidate) is not None:
                    break
                candidate = game.transition(candidate, int(rng.choice(game.legal_actions(candidate))))
            if game.terminal(candidate) is None and candidate not in states:
                states.append(candidate)
            if len(states) == 8:
                break
        for index, root_state in enumerate(states):
            root = {"game": name, "state": asdict(root_state), "split": split,
                    "trajectory": digest(["synthetic", name, index]),
                    "actions": list(game.legal_actions(root_state)),
                    "canonical_key": game.canonical_key(root_state), "beyond_depth": True,
                    "oracle_values": [1]*len(game.legal_actions(root_state)),
                    "episode": index, "depth2_zero_values": [0]*len(game.legal_actions(root_state)),
                    "nonterminal_depth2_leaves": 999}
            root["root_id"] = digest(root)
            roots.append(root)
            descendants, branches, _ = closure(name, root_state)
            for nid, node_state in descendants.items():
                outcome = game.terminal(node_state)
                legal = list(game.legal_actions(node_state))
                nodes[nid] = {"game": name, "state": asdict(node_state), "legal": legal,
                              "terminal": outcome is not None, "optimal": legal.copy(),
                              "value": node_state.player*outcome if outcome is not None else 1,
                              "action_values": [1]*len(legal)}
            for ids, actions in branches:
                forks.append({"game": name, "root_id": root["root_id"], "split": split,
                              "node_ids": ids, "actions": actions})
    return {"roots": roots, "nodes": nodes, "forks": forks,
            "manifest": {"dataset_fingerprint": "fixture-parent-fingerprint", "audit": {"status": "PASSED"},
                         "oracle": {"fixture_only": {"nodes": 0, "seconds": 0}}}}


class V22DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = fixture_parent()

    def test_known_labels_copy_hidden_labels_redact_and_full_arm_matches(self):
        scarce, selected = data._prepare(self.parent, .25, 271828)
        audit = data._inspect(scarce, .25, 271828, "train", selected)
        self.assertEqual(audit["status"], "PASSED", audit)
        self.assertTrue(all(c["unlabelled_nonterminal_fraction"] >= .5 for c in audit["counts"].values()))
        full, full_selected = data._prepare(self.parent, 1., 271828)
        self.assertEqual(scarce["roots"], full["roots"])
        self.assertEqual(scarce["forks"], full["forks"])
        self.assertEqual(data._inspect(full, 1., 271828, "train", full_selected)["status"], "PASSED")
        hidden = 0
        for nid, node in scarce["nodes"].items():
            original = self.parent["nodes"][nid]
            self.assertNotIn("action_values", node)
            if node["value_labelled"]:
                self.assertEqual(node["value"], original["value"])
            else:
                hidden += 1
                self.assertEqual(node["value"], 0)
                self.assertEqual(node["optimal"], [])
                self.assertFalse(node["policy_labelled"])
            if node["policy_labelled"]:
                self.assertEqual(node["optimal"], original["optimal"])
            self.assertTrue(full["nodes"][nid]["value_labelled"])
            self.assertEqual(full["nodes"][nid]["policy_labelled"], not node["terminal"])
        self.assertGreater(hidden, 0)

    def test_duplicate_and_symmetric_occurrences_share_global_masks(self):
        payload, selected = data._prepare(self.parent, .25, 271828)
        availability, aliases = {}, 0
        for node in payload["nodes"].values():
            key = (node["game"], GAMES_V2[node["game"]].canonical_key(state_from(node["state"])))
            value = (node["value_labelled"], node["policy_labelled"])
            if key in availability:
                aliases += 1
                self.assertEqual(availability[key], value)
            availability[key] = value
        self.assertGreater(aliases, 0)
        reordered = deepcopy(self.parent)
        reordered["roots"].reverse()
        reordered["forks"].reverse()
        other, selected_other = data._prepare(reordered, .25, 271828)
        self.assertEqual(selected, selected_other)
        first = data._inspect(payload, .25, 271828, "train", selected)
        second = data._inspect(other, .25, 271828, "train", selected_other)
        self.assertEqual(first["canonical_label_mask_sha256"], second["canonical_label_mask_sha256"])

    def test_free_terminal_labels_and_missing_horizon_masks(self):
        payload, selected = data._prepare(self.parent, .25, 271828)
        batch = data.batch_arrays(payload, range(len(payload["forks"])))
        self.assertFalse(np.any(batch["value_labelled"] & ~batch["valid"]))
        self.assertFalse(np.any(batch["policy_labelled"] & ~batch["valid"]))
        self.assertTrue(np.any(~batch["valid"][:, 2]))
        self.assertTrue(np.all(batch["value"][~batch["value_labelled"]] == 0))
        self.assertTrue(np.all(batch["policy"][~batch["policy_labelled"]] == 0))
        terminal_count = 0
        for node in payload["nodes"].values():
            if node["terminal"]:
                terminal_count += 1
                game = GAMES_V2[node["game"]]
                state = state_from(node["state"])
                self.assertEqual(node["value"], state.player*game.terminal(state))
                self.assertTrue(node["value_labelled"])
                self.assertFalse(node["policy_labelled"])
        self.assertGreater(terminal_count, 0)

    def test_root_identifiers_and_payload_exclude_hidden_oracle_metadata(self):
        payload, _ = data._prepare(self.parent, .25, 271828)
        encoded = json.dumps(payload)
        for original in self.parent["roots"]:
            self.assertNotIn(original["root_id"], encoded)
        for forbidden in ("oracle_values", "action_values", "beyond_depth", "depth2_zero_values", "episode"):
            self.assertNotIn('"'+forbidden+'"', encoded)
        for root in payload["roots"]:
            self.assertEqual(root["root_id"], digest([root["game"], root["trajectory"], root["state"]]))
        changed = deepcopy(self.parent)
        mapping = {}
        for root in changed["roots"]:
            old = root["root_id"]
            root["oracle_values"] = [-1]*len(root["oracle_values"])
            root["beyond_depth"] = False
            root["root_id"] = digest({k: v for k, v in root.items() if k != "root_id"})
            mapping[old] = root["root_id"]
        for fork in changed["forks"]:
            fork["root_id"] = mapping[fork["root_id"]]
        other, _ = data._prepare(changed, .25, 271828)
        self.assertEqual(payload["roots"], other["roots"])
        self.assertEqual(payload["forks"], other["forks"])

    def test_semantic_redaction_and_availability_corruption_fail_closed(self):
        payload, selected = data._prepare(self.parent, .25, 271828)
        hidden_id = next(nid for nid, node in payload["nodes"].items() if not node["value_labelled"])
        for change in ("hidden-value", "hidden-optimal", "availability", "root-labels", "orphan"):
            bad = deepcopy(payload)
            if change == "hidden-value":
                bad["nodes"][hidden_id]["value"] = 1
            elif change == "hidden-optimal":
                bad["nodes"][hidden_id]["optimal"] = bad["nodes"][hidden_id]["legal"][:1]
            elif change == "availability":
                bad["nodes"][hidden_id].update(value_labelled=True, policy_labelled=True,
                                               optimal=bad["nodes"][hidden_id]["legal"][:1])
            elif change == "root-labels":
                bad["roots"][0]["oracle_values"] = [1]
            else:
                bad["forks"].pop()
            with self.subTest(change=change), self.assertRaises(ValueError):
                data._inspect(bad, .25, 271828, "train", selected)

    def test_roundtrip_loaders_do_not_open_parent_and_tamper_is_rejected(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary)/"scarce"
            with patch.object(data, "parent_load", return_value=self.parent) as parent:
                manifest = data.build_dataset("synthetic-fixture-parent", path, .25)
                parent.assert_called_once_with("synthetic-fixture-parent", "train")
            with patch.object(data, "parent_load", side_effect=AssertionError("Parent must never be reopened")):
                loaded = data.load_dataset(path)
            self.assertEqual(loaded["manifest"]["dataset_fingerprint"], manifest["dataset_fingerprint"])
            with self.assertRaises(FileExistsError):
                data.build_dataset("synthetic-fixture-parent", path, .25)
            raw = (path/"data.json").read_bytes()
            (path/"data.json").write_bytes(raw+b" ")
            with self.assertRaisesRegex(ValueError, "bytes changed"):
                data.load_dataset(path)

    def test_fraction_and_mask_changes_invalidate_dataset_identity(self):
        with TemporaryDirectory() as temporary, patch.object(data, "parent_load", return_value=self.parent):
            scarce = data.build_dataset("fixture", Path(temporary)/"scarce", .25)
            full = data.build_dataset("fixture", Path(temporary)/"full", 1.)
            alternative = data.build_dataset("fixture", Path(temporary)/"mask2", .25, label_seed=314159)
            self.assertNotEqual(scarce["dataset_fingerprint"], full["dataset_fingerprint"])
            self.assertNotEqual(scarce["dataset_fingerprint"], alternative["dataset_fingerprint"])
            self.assertNotEqual(scarce["canonical_label_mask_sha256"], alternative["canonical_label_mask_sha256"])
            self.assertEqual(scarce["parent_dataset_fingerprint"], full["parent_dataset_fingerprint"])

    def test_standalone_development_export_and_protected_split_guards(self):
        parent = fixture_parent("development")
        with TemporaryDirectory() as temporary:
            path = Path(temporary)/"development"
            with patch.object(data, "parent_load", return_value=parent):
                manifest = data.build_development("fixture", path)
            with patch.object(data, "parent_load", side_effect=AssertionError("Parent must never be reopened")):
                loaded = data.load_dataset(path, "development")
            self.assertEqual(manifest["role"], "standalone-development")
            self.assertEqual([r["root_id"] for r in loaded["roots"]], [r["root_id"] for r in parent["roots"]])
            self.assertTrue(all(n["value_labelled"] for n in loaded["nodes"].values()))
            self.assertTrue(all("oracle_values" in r for r in loaded["roots"]))
            with self.assertRaises(ValueError):
                data.load_dataset(path, "train")
        for split in ("selection", "final", "test"):
            with self.assertRaises(ValueError):
                data.load_dataset("nonexistent-path", split)


if __name__ == "__main__":
    unittest.main()
