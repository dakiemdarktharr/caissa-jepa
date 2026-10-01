import tempfile
import unittest
from pathlib import Path

import numpy as np

from two_player.games import State
from two_player.v28_data import (V28_GAMES, _build_records_unchecked,
                                 generate_trajectory, replay)
from two_player.v28_model import Config, Model, build_batch


def observed_root(game_name):
    game = V28_GAMES[game_name]
    state = game.initial()
    action = game.legal_actions(state)[0]
    after = game.transition(state, action)
    reply = game.legal_actions(after)[0]
    leaf = game.transition(after, reply)
    return {
        "game": game_name,
        "split": "train",
        "state": {"board": state.board, "player": state.player},
        "action": action,
        "reply": reply,
        "future2": {"board": leaf.board, "player": leaf.player},
        "value": 0,
    }


def observed_from_state(game_name, state):
    game = V28_GAMES[game_name]
    action = game.legal_actions(state)[0]
    after = game.transition(state, action)
    reply = game.legal_actions(after)[0]
    leaf = game.transition(after, reply)
    return {"game": game_name, "split": "train", "state": {
        "board": state.board, "player": state.player}, "action": action,
        "next": {"board": after.board, "player": after.player},
        "reply": reply, "future2": {"board": leaf.board, "player": leaf.player},
        "value": 0}


class V28ModelTests(unittest.TestCase):
    def test_batch_contains_complete_legal_two_ply_reply_closure(self):
        for game_name, game in V28_GAMES.items():
            record = observed_root(game_name)
            batch = build_batch([record])
            state = game.initial()
            expected = sum(
                len(game.legal_actions(game.transition(state, action)))
                for action in game.legal_actions(state)
                if game.terminal(game.transition(state, action)) is None
            )
            self.assertEqual(len(batch["branch_roots"]), expected)
            self.assertTrue(batch["branch_nonterminal"].all())
            self.assertEqual(batch["observed_branch"].shape, (1,))
            self.assertGreaterEqual(batch["observed_branch"][0], 0)

    def test_real_terminal_h2_record_is_retained_and_uses_exact_terminal_path(self):
        game = V28_GAMES["reversi6"]
        row = generate_trajectory(game, "train", 0, 28094007)
        records, _ = _build_records_unchecked([row])
        record = next(record for record in records
                      if record["future2"] is not None
                      and game.terminal(State(tuple(record["future2"]["board"]),
                                              record["future2"]["player"])) is not None)
        batch = build_batch([record])
        model = Model(Config(variant="reply-jepa", seed=4, latent=5, batch_size=2))
        metrics, gradients = model.loss_grad(batch)
        self.assertEqual(metrics["observed_terminal_exact_count"], 1)
        self.assertEqual(metrics["observed_leaf_value_mse"], 0.0)
        root = State(tuple(record["state"]["board"]), record["state"]["player"])
        leaf = State(tuple(record["future2"]["board"]), record["future2"]["player"])
        exact = root.player * game.terminal(leaf)
        self.assertEqual(model.branch_value(game, root, record["action"],
                                            record["reply"], leaf), exact)
        self.assertTrue(np.isfinite(metrics["loss"]))
        self.assertTrue(all(np.all(np.isfinite(g)) for g in gradients.values()))

    def test_planner_terminal_scores_and_color_swap_perspective(self):
        game = V28_GAMES["reversi6"]
        model = Model(Config(variant="reply-jepa", seed=18, latent=5, batch_size=2))
        cases = ((0, -1), (2, 1), (23, 0))
        for episode, expected_relative in cases:
            with self.subTest(episode=episode, relative_outcome=expected_relative):
                row = generate_trajectory(game, "train", episode, 28094007)
                states = replay(row)
                root = states[-2]
                action = row["actions"][-1]
                terminal = game.transition(root, action)
                actual = root.player * game.terminal(terminal)
                self.assertEqual(actual, expected_relative)
                _, scores = model.plan_action(game, root)
                self.assertEqual(scores[action], float(expected_relative))

                mirrored = State(tuple(-cell for cell in root.board), -root.player)
                mirrored_terminal = game.transition(mirrored, action)
                self.assertEqual(mirrored.player * game.terminal(mirrored_terminal),
                                 expected_relative)
                _, mirrored_scores = model.plan_action(game, mirrored)
                self.assertEqual(mirrored_scores[action], float(expected_relative))

    def test_nonterminal_branch_values_are_invariant_to_color_role_swap(self):
        game = V28_GAMES["connect4-gravity-6x7"]
        root = game.transition(game.initial(), game.legal_actions(game.initial())[0])
        mirrored = State(tuple(-cell for cell in root.board), -root.player)
        np.testing.assert_array_equal(game.features(root), game.features(mirrored))
        action = game.legal_actions(root)[0]
        reply_state = game.transition(root, action)
        reply = game.legal_actions(reply_state)[0]
        leaf = game.transition(reply_state, reply)
        mirrored_leaf = game.transition(game.transition(mirrored, action), reply)
        for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf"):
            with self.subTest(variant=variant):
                model = Model(Config(variant=variant, seed=31, latent=5, batch_size=2))
                value = model.branch_value(game, root, action, reply, leaf)
                swapped_value = model.branch_value(game, mirrored, action, reply,
                                                   mirrored_leaf)
                self.assertAlmostEqual(value, swapped_value, places=12)

    def test_forced_reversi_pass_is_in_complete_reply_closure(self):
        game = V28_GAMES["reversi6"]
        found = None
        for episode in range(24):
            row = generate_trajectory(game, "train", episode, 28094007)
            states = replay(row)
            for ply, state in enumerate(states[:-1]):
                if game.legal_actions(state) == (64,):
                    found = observed_from_state("reversi6", state)
                    break
            if found is not None:
                break
        self.assertIsNotNone(found, "fixed generated trajectory bank must include a forced pass")
        batch = build_batch([found])
        actions = batch["branch_actions"]
        self.assertTrue(np.any(np.argmax(actions[:, 0, :], axis=1) == 64))

        found_reply = None
        for episode in range(24):
            row = generate_trajectory(game, "train", episode, 28094007)
            states = replay(row)
            for ply, action in enumerate(row["actions"][:-1]):
                if game.legal_actions(states[ply + 1]) == (64,):
                    root, leaf = states[ply], states[ply + 2]
                    found_reply = {"game": "reversi6", "split": "train",
                                   "state": {"board": root.board, "player": root.player},
                                   "action": action,
                                   "next": {"board": states[ply + 1].board,
                                            "player": states[ply + 1].player},
                                   "reply": 64,
                                   "future2": {"board": leaf.board,
                                               "player": leaf.player},
                                   "value": root.player * row["outcome"]}
                    break
            if found_reply is not None:
                break
        self.assertIsNotNone(found_reply, "fixed generated bank must include an opponent pass")
        reply_batch = build_batch([found_reply])
        reply_actions = reply_batch["branch_actions"]
        self.assertTrue(np.any(np.argmax(reply_actions[:, 1, :], axis=1) == 64))

    def test_generated_minus_one_roots_keep_side_to_move_value_sign(self):
        game = V28_GAMES["connect4-gravity-6x7"]
        row = generate_trajectory(game, "train", 2, 28094007)
        records, _ = _build_records_unchecked([row])
        record = next(record for record in records if record["state"]["player"] == -1)
        batch = build_batch([record])
        self.assertEqual(batch["value"][0, 0],
                         record["state"]["player"] * row["outcome"])

    def test_training_batch_rejects_nontraining_splits(self):
        record = observed_root("reversi6")
        for split in ("validation", "selection", "locked-final"):
            with self.subTest(split=split):
                record["split"] = split
                with self.assertRaisesRegex(ValueError, "train split"):
                    build_batch([record])
        record["split"] = "train"

    def test_batch_rejects_mismatched_observed_h1_and_h2_targets(self):
        record = observed_root("reversi6")
        record["next"] = record["state"]
        with self.assertRaisesRegex(ValueError, "one-ply target"):
            build_batch([record])
        record = observed_root("reversi6")
        record["future2"] = record["state"]
        with self.assertRaisesRegex(ValueError, "two-ply leaf|legal two-ply"):
            build_batch([record])

    def test_reply_jepa_loss_has_nonzero_gradient_and_finite_difference_matches(self):
        game = V28_GAMES["reversi6"]
        state = game.initial()
        records = [observed_root("reversi6") for _ in range(2)]
        batch = build_batch(records)
        model = Model(Config(variant="reply-jepa", seed=4, latent=5, batch_size=2))
        metrics, gradients = model.loss_grad(batch)
        self.assertGreater(metrics["reply_jepa_loss"], 0)
        self.assertTrue(np.isfinite(metrics["loss"]))
        self.assertGreater(float(np.linalg.norm(gradients["gw"])), 0)
        self._assert_gradient_close(model, batch, gradients, "gw", (0, 0))
        self._assert_gradient_close(model, batch, gradients, "ew", (0, 0))
        self._assert_gradient_close(model, batch, gradients, "pw", (0, 0))
        self._assert_gradient_close(model, batch, gradients, "vw", (0, 0))

    def test_nonunit_jepa_weight_keeps_observed_return_gradient_unweighted(self):
        batch = build_batch([observed_root("reversi6"), observed_root("reversi6")])
        component_keys = ("policy_nll", "root_value_mse", "observed_leaf_value_mse",
                          "variance_loss", "covariance_loss")
        reference = None
        for weight in (0.0, 0.5):
            with self.subTest(jepa_weight=weight):
                model = Model(Config(variant="reply-jepa", seed=4, latent=5,
                                     batch_size=2, jepa_weight=weight))
                metrics, gradients = model.loss_grad(batch)
                target_before = {key: value.copy() for key, value in model.target.items()}
                model.loss_grad(batch)
                for key, value in target_before.items():
                    np.testing.assert_array_equal(model.target[key], value)
                self._assert_gradient_close(model, batch, gradients, "gw", (0, 0))
                if reference is None:
                    reference = metrics
                else:
                    for key in component_keys:
                        self.assertAlmostEqual(metrics[key], reference[key], places=12)
                    self.assertAlmostEqual(
                        metrics["loss"] - reference["loss"],
                        weight * metrics["reply_jepa_loss"], places=12)

    def test_each_arm_has_finite_difference_coverage_for_weights_and_biases(self):
        batch = build_batch([observed_root("connect4-gravity-6x7"),
                             observed_root("reversi6")])
        for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf"):
            config = Config(variant=variant, seed=19, latent=4, batch_size=2,
                            jepa_weight=0.5)
            model = Model(config)
            _, gradients = model.loss_grad(batch)
            for name, values in model.params.items():
                with self.subTest(variant=variant, parameter=name):
                    coordinate = tuple(0 for _ in values.shape)
                    self._assert_gradient_close(model, batch, gradients, name, coordinate)

    def test_observed_terminal_leaf_is_masked_from_learned_value_loss(self):
        batch = build_batch([observed_root("reversi6")])
        batch["branch_nonterminal"][batch["observed_branch"][0]] = False
        model = Model(Config(variant="reply-jepa", seed=4, latent=5, batch_size=2))
        metrics, gradients = model.loss_grad(batch)
        self.assertEqual(metrics["observed_terminal_exact_count"], 1)
        self.assertEqual(metrics["observed_leaf_value_mse"], 0.0)
        self.assertTrue(np.isfinite(metrics["loss"]))
        self.assertTrue(all(np.all(np.isfinite(g)) for g in gradients.values()))

    def _assert_gradient_close(self, model, batch, gradients, parameter, key):
        original = model.params[parameter][key]
        epsilon = 1e-6
        model.params[parameter][key] = original + epsilon
        plus = model.loss_grad(batch)[0]["loss"]
        model.params[parameter][key] = original - epsilon
        minus = model.loss_grad(batch)[0]["loss"]
        model.params[parameter][key] = original
        numerical = (plus - minus) / (2 * epsilon)
        self.assertAlmostEqual(gradients[parameter][key], numerical, delta=2e-5)

    def test_all_matched_variants_update_and_planner_scores_are_bounded(self):
        batch = build_batch([observed_root("connect4-gravity-6x7"),
                             observed_root("reversi6")])
        for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf"):
            model = Model(Config(variant=variant, seed=11, latent=6, batch_size=2))
            metrics = model._update(batch)
            self.assertEqual(model.step, 1)
            self.assertTrue(np.isfinite(metrics["loss"]))
            self.assertGreater(metrics["gradient_norm"], 0)
            _, gradients = model.loss_grad(batch)
            parameter = "gw" if variant == "task-value-dynamics" else "ew"
            self._assert_gradient_close(model, batch, gradients, parameter, (0, 0))
            game = V28_GAMES["reversi6"]
            state = game.initial()
            action = game.legal_actions(state)[0]
            after = game.transition(state, action)
            reply = game.legal_actions(after)[0]
            leaf = game.transition(after, reply)
            self.assertTrue(-1 <= model.branch_value(game, state, action, reply, leaf) <= 1)

    def test_checkpoint_requires_exact_config_and_dataset_identity(self):
        model = Model(Config(variant="reply-jepa", seed=3, latent=4, batch_size=2))
        identity = {"dataset_sha256": "a" * 64,
                    "audit_sha256": "b" * 64,
                    "run_config_sha256": "c" * 64, "split": "train"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.npz"
            model.save(path, identity)
            restored = Model.load(path, model.config, identity)
            self.assertEqual(restored.step, 0)
            for key in model.params:
                np.testing.assert_array_equal(restored.params[key], model.params[key])
            with self.assertRaisesRegex(ValueError, "identity"):
                Model.load(path, model.config, {"dataset_sha256": "c" * 64,
                                                "audit_sha256": "b" * 64,
                                                "run_config_sha256": "c" * 64,
                                                "split": "train"})
            with self.assertRaisesRegex(ValueError, "requires dataset"):
                model.save(path, {})
            with self.assertRaisesRegex(ValueError, "train split"):
                model.save(path, {**identity, "split": "selection"})

    def test_checkpoint_rejects_inconsistent_epoch_history_and_optimizer_steps(self):
        model = Model(Config(seed=3, latent=4, batch_size=2))
        identity = {"dataset_sha256": "a" * 64,
                    "audit_sha256": "b" * 64,
                    "run_config_sha256": "c" * 64, "split": "train"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.npz"
            model.training_state = {"completed_epochs": 1, "history": []}
            with self.assertRaisesRegex(ValueError, "epoch count"):
                model.save(path, identity)
            model.training_state = {
                "completed_epochs": 1,
                "history": [{"epoch_index": 0, "updates": 1,
                             "metric_semantics": "root_weighted_pre_update_minibatch_train"}]}
            with self.assertRaisesRegex(ValueError, "optimizer step"):
                model.save(path, identity)


if __name__ == "__main__":
    unittest.main()
