"""Training-only metric invariants on synthetic legal fixtures, no fitting."""
from copy import deepcopy
from dataclasses import asdict
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from two_player.games import State
from two_player_v2 import GAMES_V2
from two_player_v2.data import closure
from two_player_v22.model import Config, Model
from two_player_v23_diagnostic.metrics import _geometry, snapshot_metrics


def fixture():
    roots, nodes, forks = [], {}, []
    for name, game in GAMES_V2.items():
        middle = game.initial()
        for _ in range(3):
            middle = game.transition(middle, game.legal_actions(middle)[0])
        if game.gravity:
            ending = game.initial()
            for action in (24, 28, 25, 20, 26, 12):
                ending = game.transition(ending, action)
        else:
            ending = State((0, 1, -1, -1, -1, -1)+(-1,)*30, -1)
        for i, state in enumerate((game.initial(), middle, ending)):
            rid = name+"-fixture-"+str(i)
            roots.append({"root_id": rid, "trajectory": rid, "game": name, "split": "train"})
            descendants, branches, _ = closure(name, state)
            for nid, s in descendants.items():
                outcome = game.terminal(s)
                legal = list(game.legal_actions(s))
                # Synthetic oracle placeholders, not claimed minimax solutions.
                value = s.player*outcome if outcome is not None else int(sum(v != 0 for v in s.board) % 4 == 0)
                nodes[nid] = {"game": name, "state": asdict(s), "legal": legal, "optimal": legal.copy(),
                              "value": value, "terminal": outcome is not None,
                              "value_labelled": True, "policy_labelled": outcome is None}
            for ids, actions in branches:
                forks.append({"root_id": rid, "game": name, "split": "train", "node_ids": ids, "actions": actions})
    return {"roots": roots, "nodes": nodes, "forks": forks,
            "manifest": {"role": "redacted-training", "split": "train", "fraction": 1.}}


class ZeroValue:
    config = SimpleNamespace(variant="direct")

    def encode(self, x):
        return np.zeros((len(x), 3))

    def value(self, z):
        return np.zeros((len(z), 1))

    def rollout(self, *args, **kwargs):
        raise AssertionError("Direct's unused dynamics must never be scored")


class V23MetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = fixture()

    def test_equal_root_components_terminal_and_missing_horizons(self):
        result = snapshot_metrics(ZeroValue(), self.data, time.perf_counter()+30)
        expected, unequal_weighting = [], False
        for game in GAMES_V2:
            for horizon in (1, 2):
                root_errors, all_errors = [], []
                for root in self.data["roots"]:
                    if root["game"] != game:
                        continue
                    seen, errors = set(), []
                    for fork in self.data["forks"]:
                        if fork["root_id"] != root["root_id"]:
                            continue
                        path = tuple(fork["actions"][:horizon])
                        nid = fork["node_ids"][horizon]
                        if nid is None or path in seen:
                            continue
                        seen.add(path)
                        node = self.data["nodes"][nid]
                        if not node["terminal"]:
                            errors.append(node["value"]**2)
                    if errors:
                        root_errors.append(np.mean(errors))
                        all_errors.extend(errors)
                mean = float(np.mean(root_errors)); expected.append(mean)
                component = result["S_components"][game][str(horizon)]
                self.assertAlmostEqual(component["encoded_oracle_mse"], mean)
                self.assertEqual(component["roots_with_targets"], len(root_errors))
                self.assertEqual(component["transition_targets"], len(all_errors))
                unequal_weighting |= not np.isclose(mean, np.mean(all_errors))
        self.assertTrue(unequal_weighting)
        self.assertAlmostEqual(result["S"], np.mean(expected))
        self.assertGreater(sum(r["missing_h2_forks"] for r in result["fit"]["per_root"]), 0)
        self.assertFalse(result["fit"]["dynamics_metrics_available"])
        self.assertTrue(all(r["saved_planning"] is None for r in result["fit"]["per_root"]))
        self.assertEqual(len(result["collapse"]), 2)

    def test_h1_deduplicates_replies_geometry_counts_raw_nodes_once(self):
        result = snapshot_metrics(ZeroValue(), self.data, time.perf_counter()+30)
        for row in result["fit"]["per_root"]:
            paths = [f for f in self.data["forks"] if f["root_id"] == row["root_id"]]
            self.assertEqual(row["horizons"]["1"]["all"]["count"], len({f["actions"][0] for f in paths}))
            self.assertEqual(row["horizons"]["2"]["all"]["count"], sum(f["node_ids"][2] is not None for f in paths))
        for game, stats in result["geometry"].items():
            selected = [n for n in self.data["nodes"].values() if n["game"] == game]
            self.assertEqual(stats["samples"], len(selected))
            self.assertEqual(stats["terminal_nodes"], sum(n["terminal"] for n in selected))
            self.assertIn("raw training node", stats["weighting"])

    def test_effective_rank_uses_squared_singular_entropy_and_population_std(self):
        z = np.array([[2., 0.], [-2., 0.], [0., 1.], [0., -1.]])
        stats = _geometry(z)
        p = np.array([.8, .2])
        self.assertAlmostEqual(stats["effective_rank"], np.exp(-np.sum(p*np.log(p))))
        self.assertAlmostEqual(stats["median_std"], np.median(np.std(z, axis=0)))
        self.assertAlmostEqual(stats["mean_std"], np.std(z, axis=0).mean())
        self.assertEqual(_geometry(np.ones((4, 3)))["effective_rank"], 0.)
        with self.assertRaises(ValueError):
            _geometry([[float("nan")]])

    def test_real_model_diagnostics_do_not_mutate_data_or_online_target_adam(self):
        model = Model(Config(variant="raw-jepa", jepa_weight=.1))
        before = [{k: v.copy() for k, v in group.items()} for group in (model.params, model.target, model.m, model.v)]
        data_before = deepcopy(self.data)
        counters = model.epoch, model.step
        result = snapshot_metrics(model, self.data, time.perf_counter()+30)
        self.assertTrue(result["fit"]["dynamics_metrics_available"])
        for current, old in zip((model.params, model.target, model.m, model.v), before):
            for name, value in old.items():
                np.testing.assert_array_equal(current[name], value)
        self.assertEqual((model.epoch, model.step), counters)
        self.assertEqual(self.data, data_before)

    def test_split_label_deadline_and_support_fail_closed(self):
        for change in ("split", "fraction", "node_label"):
            data = deepcopy(self.data)
            if change == "split": data["roots"][0]["split"] = "development"
            elif change == "fraction": data["manifest"]["fraction"] = .25
            else: next(iter(data["nodes"].values()))["value_labelled"] = False
            with patch("two_player_v23_diagnostic.metrics.diagnostic") as helper:
                with self.assertRaises(ValueError):
                    snapshot_metrics(ZeroValue(), data, time.perf_counter()+30)
                helper.assert_not_called()
        with self.assertRaises(TimeoutError):
            snapshot_metrics(ZeroValue(), self.data, time.perf_counter()-1)
        # Real helper must reject S when all observed targets have terminal stratum.
        data = deepcopy(self.data)
        for node in data["nodes"].values():
            node["terminal"] = True; node["policy_labelled"] = False
        with self.assertRaisesRegex(ValueError, "nonterminal target support"):
            snapshot_metrics(ZeroValue(), data, time.perf_counter()+30)


if __name__ == "__main__":
    unittest.main()
