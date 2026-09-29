# Grid02 value-alignment diagnosis

Date: 2026-09-29. **Post-hoc descriptive diagnosis; no new fit, search, oracle call, selection or final-set evaluation.** This note supersedes the earlier preference for an immediate action-gating experiment in `V23_RESEARCH_OPTIONS.md`. It does not establish a capacity bottleneck or JEPA advantage.

## Provenance and counting

Input: `chess_data/v21-value-alignment-01.json`, SHA-256 `3a7890c93bea95925624d561de986e7c1293824ae733e709d28c2c7abe809691`. Diagnostic source commit `086e839d5f9ed1559cce16a9f8ff9fdd6b843191`; script hash `92d3735949a14429b13f741cde4348ad1163048409df3d7df71314784e223df7`. Original diagnostic runtime: 15.875639 seconds. The source artifact contains all 18 receipt/checkpoint hashes and source/data identities. A public summary is `docs/validation/V21_VALUE_ALIGNMENT_DIAGNOSIS.json`; new constant/history aggregates are in `docs/validation/V21_TRAINING_CONVERGENCE_CONTEXT.json`. The original large per-root artifact remains excluded.

All six globally selected Grid02 families and seeds 17, 29, 43 are included. Selection was already made from the full Grid02 development grid; these are not unselected confirmatory checkpoints. All learning rates are 0.001; auxiliary weights are 1 for direct/value-dynamics/no-response and 0.1 for decoded/rjepa/raw-jepa. Direct has no trained dynamics, so its rollout entries are unavailable, never zero.

Only standalone full-label training and development exports (`chess_data/v22-full-01` and `chess_data/v22-development-01`) were read. The restricted-label arm, parent data payload and locked final set were not opened. The existing diagnostic reports zero selection predictions, zero final predictions and zero new search decisions. Development is already adaptively exposed.

H1 deduplicates (root, own action); H2 deduplicates (root, own action, reply) and excludes missing successors. Distinct paths to the same state remain separate targets. Each nonempty root receives equal weight within a game/horizon/stratum; seeds are then averaged equally. Transition-weighted values are also supplied. Counts are per seed, not multiplied by three into an artificial independent sample size. Forks, states and seeds are dependent observations; ranges below are descriptive, not confidence intervals.

## Target distributions and constant baselines

For each game/horizon/stratum, fit a scalar mean on training targets with the indicated weighting, then hold that scalar fixed for development. This is a descriptive label-prior comparator, not a deployable single value model: it may use horizon/terminal stratum. The zero comparator predicts exactly zero; it is not the saved randomly initialized neural network. The latter was not re-evaluated here.

ER probabilities and MSE give equal weight to nonempty roots. TW uses one weight per target. Counts (-1,0,+1) are unweighted target counts. `Mean` is the current split ER target mean; development constant MSE always uses the corresponding TRAIN mean.

| Game | H | Stratum | Split | Roots | Targets (-1,0,+1) | ER probabilities (-1,0,+1) | Mean | Zero ER MSE | Train-mean ER MSE | Train-mean TW MSE |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| connect4-4x5 | 1 | all | train | 248 | 214,306,356 | 0.2485,0.3560,0.3956 | 0.147110 | 0.644019 | 0.622377 | 0.624408 |
| connect4-4x5 | 1 | all | development | 107 | 128,142,130 | 0.3153,0.3621,0.3226 | 0.007321 | 0.637850 | 0.657338 | 0.669656 |
| connect4-4x5 | 1 | nonterminal | train | 248 | 142,306,356 | 0.1807,0.3831,0.4362 | 0.255444 | 0.616868 | 0.551617 | 0.548557 |
| connect4-4x5 | 1 | nonterminal | development | 107 | 85,142,130 | 0.2352,0.4065,0.3583 | 0.123053 | 0.593458 | 0.595843 | 0.605985 |
| connect4-4x5 | 1 | terminal | train | 71 | 72,0,0 | 1.0000,0.0000,0.0000 | -1.000000 | 1.000000 | 0.000000 | 0.000000 |
| connect4-4x5 | 1 | terminal | development | 43 | 43,0,0 | 1.0000,0.0000,0.0000 | -1.000000 | 1.000000 | 0.000000 | 0.000000 |
| connect4-4x5 | 2 | all | train | 248 | 471,919,1284 | 0.1759,0.3433,0.4809 | 0.304999 | 0.656727 | 0.563703 | 0.563880 |
| connect4-4x5 | 2 | all | development | 107 | 164,370,709 | 0.1353,0.3049,0.5598 | 0.424461 | 0.695083 | 0.529187 | 0.528158 |
| connect4-4x5 | 2 | nonterminal | train | 248 | 222,919,1284 | 0.0869,0.3785,0.5346 | 0.447686 | 0.621469 | 0.421046 | 0.429241 |
| connect4-4x5 | 2 | nonterminal | development | 107 | 83,370,709 | 0.0776,0.3340,0.5884 | 0.510845 | 0.665953 | 0.408979 | 0.401516 |
| connect4-4x5 | 2 | terminal | train | 111 | 249,0,0 | 1.0000,0.0000,0.0000 | -1.000000 | 1.000000 | 0.000000 | 0.000000 |
| connect4-4x5 | 2 | terminal | development | 35 | 81,0,0 | 1.0000,0.0000,0.0000 | -1.000000 | 1.000000 | 0.000000 | 0.000000 |
| reversi6 | 1 | all | train | 261 | 624,103,453 | 0.5165,0.0924,0.3911 | -0.125411 | 0.907576 | 0.891848 | 0.891711 |
| reversi6 | 1 | all | development | 102 | 218,53,184 | 0.4631,0.1251,0.4118 | -0.051331 | 0.874883 | 0.877736 | 0.882859 |
| reversi6 | 1 | nonterminal | train | 261 | 624,103,453 | 0.5165,0.0924,0.3911 | -0.125411 | 0.907576 | 0.891848 | 0.891711 |
| reversi6 | 1 | nonterminal | development | 102 | 218,53,184 | 0.4631,0.1251,0.4118 | -0.051331 | 0.874883 | 0.877736 | 0.882859 |
| reversi6 | 2 | all | train | 261 | 807,243,2954 | 0.2064,0.0651,0.7285 | 0.522045 | 0.934872 | 0.662341 | 0.651785 |
| reversi6 | 2 | all | development | 102 | 333,108,1008 | 0.2257,0.0819,0.6924 | 0.466674 | 0.918093 | 0.703374 | 0.713413 |
| reversi6 | 2 | nonterminal | train | 261 | 807,243,2953 | 0.2071,0.0651,0.7278 | 0.520768 | 0.934872 | 0.663673 | 0.651895 |
| reversi6 | 2 | nonterminal | development | 102 | 333,108,1008 | 0.2257,0.0819,0.6924 | 0.466674 | 0.918093 | 0.703234 | 0.713397 |
| reversi6 | 2 | terminal | train | 1 | 0,0,1 | 0.0000,0.0000,1.0000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 |

Reversi H1 has no terminal successors in either split. Reversi H2 has one terminal training target and none in development. Terminal-value/latent errors are excluded from the nonterminal interpretation because the saved search uses exact terminal overrides.

## All families, both horizons: nonterminal value alignment

`E` = encoded actual-state oracle MSE; `P` = recurrent predicted-state oracle MSE; `D` = squared difference between predicted and encoded values; `L` = raw online latent MSE. These are equal-root means across all three seeds. Latent scales differ between models, so L is not a common cross-model strategic scale.

| Game | Split | H | Roots / targets per seed | Family | E | P | D | L |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| connect4-4x5 | train | 1 | 248 / 804 | direct | 0.418421 | NA | NA | NA |
| connect4-4x5 | train | 1 | 248 / 804 | value-dynamics | 0.451923 | 0.388141 | 0.101686 | 0.592236 |
| connect4-4x5 | train | 1 | 248 / 804 | decoded | 0.444997 | 0.384191 | 0.094997 | 0.525652 |
| connect4-4x5 | train | 1 | 248 / 804 | rjepa | 0.454995 | 0.382567 | 0.083009 | 0.401487 |
| connect4-4x5 | train | 1 | 248 / 804 | raw-jepa | 0.464513 | 0.411801 | 0.097488 | 0.123477 |
| connect4-4x5 | train | 1 | 248 / 804 | no-response | 0.493034 | 0.447259 | 0.067111 | 0.203484 |
| connect4-4x5 | train | 2 | 248 / 2425 | direct | 0.349228 | NA | NA | NA |
| connect4-4x5 | train | 2 | 248 / 2425 | value-dynamics | 0.348375 | 0.341712 | 0.057124 | 0.577192 |
| connect4-4x5 | train | 2 | 248 / 2425 | decoded | 0.345329 | 0.338136 | 0.054996 | 0.583499 |
| connect4-4x5 | train | 2 | 248 / 2425 | rjepa | 0.343176 | 0.347813 | 0.048692 | 0.442057 |
| connect4-4x5 | train | 2 | 248 / 2425 | raw-jepa | 0.343219 | 0.344469 | 0.045054 | 0.081458 |
| connect4-4x5 | train | 2 | 248 / 2425 | no-response | 0.360404 | 0.382653 | 0.032924 | 0.240897 |
| connect4-4x5 | development | 1 | 107 / 357 | direct | 0.576112 | NA | NA | NA |
| connect4-4x5 | development | 1 | 107 / 357 | value-dynamics | 0.601373 | 0.576951 | 0.130255 | 0.596258 |
| connect4-4x5 | development | 1 | 107 / 357 | decoded | 0.584139 | 0.578563 | 0.123238 | 0.531353 |
| connect4-4x5 | development | 1 | 107 / 357 | rjepa | 0.596811 | 0.569347 | 0.095107 | 0.400930 |
| connect4-4x5 | development | 1 | 107 / 357 | raw-jepa | 0.606375 | 0.583756 | 0.119364 | 0.123247 |
| connect4-4x5 | development | 1 | 107 / 357 | no-response | 0.609909 | 0.561741 | 0.082994 | 0.205487 |
| connect4-4x5 | development | 2 | 107 / 1162 | direct | 0.412520 | NA | NA | NA |
| connect4-4x5 | development | 2 | 107 / 1162 | value-dynamics | 0.414930 | 0.445269 | 0.057203 | 0.576068 |
| connect4-4x5 | development | 2 | 107 / 1162 | decoded | 0.412699 | 0.431867 | 0.054068 | 0.580552 |
| connect4-4x5 | development | 2 | 107 / 1162 | rjepa | 0.404076 | 0.426966 | 0.050103 | 0.435850 |
| connect4-4x5 | development | 2 | 107 / 1162 | raw-jepa | 0.390483 | 0.429421 | 0.046667 | 0.080531 |
| connect4-4x5 | development | 2 | 107 / 1162 | no-response | 0.403874 | 0.416022 | 0.034118 | 0.235376 |
| reversi6 | train | 1 | 261 / 1180 | direct | 0.863166 | NA | NA | NA |
| reversi6 | train | 1 | 261 / 1180 | value-dynamics | 0.893516 | 0.725360 | 0.235236 | 0.732723 |
| reversi6 | train | 1 | 261 / 1180 | decoded | 0.887841 | 0.727680 | 0.217970 | 0.683441 |
| reversi6 | train | 1 | 261 / 1180 | rjepa | 0.887225 | 0.738776 | 0.199994 | 0.590885 |
| reversi6 | train | 1 | 261 / 1180 | raw-jepa | 0.873005 | 0.746375 | 0.199952 | 0.139879 |
| reversi6 | train | 1 | 261 / 1180 | no-response | 0.952940 | 0.765063 | 0.275089 | 0.296662 |
| reversi6 | train | 2 | 261 / 4003 | direct | 0.509776 | NA | NA | NA |
| reversi6 | train | 2 | 261 / 4003 | value-dynamics | 0.506844 | 0.535372 | 0.088574 | 0.752018 |
| reversi6 | train | 2 | 261 / 4003 | decoded | 0.511308 | 0.535128 | 0.083321 | 0.799447 |
| reversi6 | train | 2 | 261 / 4003 | rjepa | 0.509542 | 0.539229 | 0.088880 | 0.644920 |
| reversi6 | train | 2 | 261 / 4003 | raw-jepa | 0.511297 | 0.542303 | 0.082663 | 0.098539 |
| reversi6 | train | 2 | 261 / 4003 | no-response | 0.514599 | 0.586083 | 0.078273 | 0.309864 |
| reversi6 | development | 1 | 102 / 455 | direct | 0.828829 | NA | NA | NA |
| reversi6 | development | 1 | 102 / 455 | value-dynamics | 0.844478 | 0.784406 | 0.218619 | 0.742021 |
| reversi6 | development | 1 | 102 / 455 | decoded | 0.827683 | 0.785880 | 0.202835 | 0.688562 |
| reversi6 | development | 1 | 102 / 455 | rjepa | 0.818861 | 0.813558 | 0.196243 | 0.595838 |
| reversi6 | development | 1 | 102 / 455 | raw-jepa | 0.819049 | 0.816296 | 0.193297 | 0.136441 |
| reversi6 | development | 1 | 102 / 455 | no-response | 0.880906 | 0.811190 | 0.261415 | 0.300239 |
| reversi6 | development | 2 | 102 / 1449 | direct | 0.530518 | NA | NA | NA |
| reversi6 | development | 2 | 102 / 1449 | value-dynamics | 0.524150 | 0.604916 | 0.100184 | 0.743550 |
| reversi6 | development | 2 | 102 / 1449 | decoded | 0.523651 | 0.607385 | 0.100299 | 0.796307 |
| reversi6 | development | 2 | 102 / 1449 | rjepa | 0.527736 | 0.608356 | 0.098556 | 0.659276 |
| reversi6 | development | 2 | 102 / 1449 | raw-jepa | 0.523842 | 0.605974 | 0.091804 | 0.100360 |
| reversi6 | development | 2 | 102 / 1449 | no-response | 0.527341 | 0.635844 | 0.083129 | 0.310942 |

## H2 seed sensitivity and weighting sensitivity

Each seed cell is `E/P`, in fixed order 17, 29, 43. TW is the three-seed mean under target weighting. No seed was omitted.

| Game | Split | Family | Seed 17 E/P | Seed 29 E/P | Seed 43 E/P | TW E/P |
| --- | --- | --- | --- | --- | --- | --- |
| connect4-4x5 | train | direct | 0.340212/NA | 0.341307/NA | 0.366165/NA | 0.348735/NA |
| connect4-4x5 | train | value-dynamics | 0.375260/0.344835 | 0.337553/0.342777 | 0.332312/0.337522 | 0.349127/0.343357 |
| connect4-4x5 | train | decoded | 0.360558/0.340558 | 0.340473/0.335632 | 0.334955/0.338219 | 0.344527/0.341230 |
| connect4-4x5 | train | rjepa | 0.357610/0.347173 | 0.321177/0.335200 | 0.350740/0.361065 | 0.344551/0.349566 |
| connect4-4x5 | train | raw-jepa | 0.349211/0.338123 | 0.341087/0.347568 | 0.339361/0.347718 | 0.345687/0.345974 |
| connect4-4x5 | train | no-response | 0.357091/0.384431 | 0.342985/0.364227 | 0.381135/0.399302 | 0.361022/0.380265 |
| connect4-4x5 | development | direct | 0.406465/NA | 0.395101/NA | 0.435994/NA | 0.390787/NA |
| connect4-4x5 | development | value-dynamics | 0.458599/0.473565 | 0.403902/0.443765 | 0.382287/0.418477 | 0.394229/0.431136 |
| connect4-4x5 | development | decoded | 0.442442/0.446782 | 0.405470/0.423413 | 0.390185/0.425406 | 0.391388/0.416035 |
| connect4-4x5 | development | rjepa | 0.428254/0.437748 | 0.371238/0.402988 | 0.412734/0.440161 | 0.378562/0.403699 |
| connect4-4x5 | development | raw-jepa | 0.413564/0.431507 | 0.376082/0.416502 | 0.381805/0.440253 | 0.373641/0.419801 |
| connect4-4x5 | development | no-response | 0.407614/0.417433 | 0.371727/0.385958 | 0.432279/0.444676 | 0.385117/0.408295 |
| reversi6 | train | direct | 0.509799/NA | 0.512307/NA | 0.507222/NA | 0.493122/NA |
| reversi6 | train | value-dynamics | 0.511418/0.530781 | 0.507571/0.539923 | 0.501543/0.535414 | 0.491868/0.516885 |
| reversi6 | train | decoded | 0.509959/0.536118 | 0.518085/0.535198 | 0.505880/0.534069 | 0.494901/0.514500 |
| reversi6 | train | rjepa | 0.505732/0.535087 | 0.518127/0.541566 | 0.504768/0.541034 | 0.494156/0.519250 |
| reversi6 | train | raw-jepa | 0.505240/0.542745 | 0.520022/0.540646 | 0.508630/0.543518 | 0.494392/0.519016 |
| reversi6 | train | no-response | 0.510953/0.576901 | 0.519083/0.595616 | 0.513761/0.585731 | 0.498905/0.566954 |
| reversi6 | development | direct | 0.538782/NA | 0.535676/NA | 0.517096/NA | 0.517615/NA |
| reversi6 | development | value-dynamics | 0.534354/0.601697 | 0.522277/0.596800 | 0.515819/0.616252 | 0.510095/0.596228 |
| reversi6 | development | decoded | 0.527420/0.608428 | 0.525947/0.599335 | 0.517585/0.614392 | 0.508155/0.596236 |
| reversi6 | development | rjepa | 0.536243/0.602599 | 0.521514/0.595447 | 0.525450/0.627023 | 0.515329/0.592322 |
| reversi6 | development | raw-jepa | 0.531585/0.607496 | 0.518660/0.597411 | 0.521281/0.613015 | 0.511568/0.594083 |
| reversi6 | development | no-response | 0.532478/0.633100 | 0.527704/0.644163 | 0.521841/0.630270 | 0.515144/0.619732 |

## Training histories at fixed epochs

The following values come from all selected `history.json` files at epochs 1, 10, 20 and 40. They average each epoch's reported sample-weighted minibatch metrics over three seeds. These are measurements during optimization on resampled, augmented batches, not fixed-probe checkpoint evaluations. They mix game/horizon/terminal strata, so they cannot be equated with the equal-root table above. Counts inside `metrics_sample_weighted` are averaged batch counts, not total target counts. Actual schedule exposure is 8,352 fork draws per epoch (4,176 per game), 66 updates, and 2,640 updates at epoch 40; unique roots are 248 Connect4 and 261 Reversi, with repeated roots/forks explicitly possible.

| Family | Epoch | Encoded value MSE mean [seed min,max] | Policy NLL | H1 predicted value MSE | H2 predicted value MSE | H1 auxiliary | H2 auxiliary |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| direct | 1 | 0.574667 [0.568257,0.578132] | 1.173955 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| direct | 10 | 0.499896 [0.496000,0.504444] | 1.108237 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| direct | 20 | 0.471572 [0.463878,0.477149] | 1.081915 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| direct | 40 | 0.425267 [0.420865,0.431582] | 1.020945 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| value-dynamics | 1 | 0.573939 [0.569932,0.576359] | 1.177657 | 0.736692 | 0.620827 | 0.000000 | 0.000000 |
| value-dynamics | 10 | 0.503049 [0.499826,0.507020] | 1.115037 | 0.654311 | 0.532094 | 0.000000 | 0.000000 |
| value-dynamics | 20 | 0.480364 [0.473920,0.488596] | 1.089736 | 0.632421 | 0.516262 | 0.000000 | 0.000000 |
| value-dynamics | 40 | 0.436578 [0.429249,0.445151] | 1.043391 | 0.573365 | 0.475395 | 0.000000 | 0.000000 |
| decoded | 1 | 0.573932 [0.569792,0.576514] | 1.177942 | 0.735948 | 0.619395 | 0.272846 | 0.277933 |
| decoded | 10 | 0.503825 [0.501178,0.507234] | 1.116219 | 0.653535 | 0.531799 | 0.066645 | 0.070963 |
| decoded | 20 | 0.481655 [0.477016,0.488024] | 1.089662 | 0.631783 | 0.515082 | 0.058924 | 0.065417 |
| decoded | 40 | 0.436278 [0.429508,0.444555] | 1.041567 | 0.573572 | 0.475835 | 0.055230 | 0.062311 |
| rjepa | 1 | 0.573741 [0.569001,0.576131] | 1.185423 | 0.738961 | 0.618617 | 0.667724 | 0.660063 |
| rjepa | 10 | 0.503240 [0.500881,0.506066] | 1.120516 | 0.652839 | 0.531631 | 0.119338 | 0.116477 |
| rjepa | 20 | 0.482594 [0.478444,0.486443] | 1.094154 | 0.632666 | 0.515964 | 0.162487 | 0.142682 |
| rjepa | 40 | 0.437288 [0.432817,0.443181] | 1.047806 | 0.578650 | 0.481936 | 0.164823 | 0.137066 |
| raw-jepa | 1 | 0.573866 [0.569550,0.576678] | 1.178587 | 0.735877 | 0.619401 | 0.207101 | 0.197786 |
| raw-jepa | 10 | 0.503479 [0.500562,0.506258] | 1.116812 | 0.655506 | 0.533424 | 0.071107 | 0.054402 |
| raw-jepa | 20 | 0.481338 [0.472888,0.488229] | 1.092069 | 0.637560 | 0.516841 | 0.093876 | 0.067886 |
| raw-jepa | 40 | 0.439799 [0.432947,0.446940] | 1.048266 | 0.586441 | 0.486981 | 0.125353 | 0.087253 |
| no-response | 1 | 0.583827 [0.581119,0.585228] | 1.207347 | 0.773843 | 0.641994 | 0.529789 | 0.468320 |
| no-response | 10 | 0.505797 [0.503802,0.508078] | 1.134872 | 0.658943 | 0.560721 | 0.034097 | 0.038039 |
| no-response | 20 | 0.491961 [0.486313,0.495027] | 1.110071 | 0.647563 | 0.551398 | 0.049590 | 0.064929 |
| no-response | 40 | 0.456344 [0.451770,0.459303] | 1.085242 | 0.621843 | 0.537048 | 0.065446 | 0.109122 |

Direct's reported recurrent zeros mean the losses are absent, not perfect predictions. Auxiliary losses have different definitions/scales; their numerical size cannot rank the models. History file hashes below record this read; they are not a claim that the original receipt cryptographically committed every history file.

## Interpretation and next diagnostic

1. **Do not jump to a transition architecture change.** Raw JEPA H2 train E/P is 0.343219/0.344469 in Connect4 and 0.511297/0.542303 in Reversi. Development E/P is 0.390483/0.429421 and 0.523842/0.605974. Encoded error is already substantial, but these numbers alone do not identify optimization, capacity, multitask interference, or irreducible finite-sample generalization as the cause.

2. **Models do learn beyond label priors.** For H2 nonterminal training, the constant-mean E comparator is 0.421046 in Connect4 and 0.663673 in Reversi; raw E improves on these by about 18.5% and 23.0%. Reversi E=0.51 must not be described as no learning simply because it looks large. Zero MSE there is 0.934872. Conversely, Reversi H1 raw E=0.873005 barely improves on its training constant 0.891848, and value-dynamics E=0.893516 is slightly worse. Its recurrent P=0.746375 (raw) or 0.725360 (value-dynamics) is better, so the re-encoded state is not always the superior value estimator. H1 versus H2 target priors differ sharply (Reversi train mean -0.125411 versus +0.520768), requiring stratified calibration checks before attributing this to network capacity.

3. **MSE gaps are not additive error attribution.** Write encoded residual u=V(E(x))-y and rollout displacement d=V(pred)-V(E(x)). Then P=E+D+2 mean(u d). A small P-E can hide substantial rollout displacement cancelled by a negative cross term. Raw Connect4 H2 train has D=0.045054 despite P-E=0.001250; Reversi has D=0.082663 and P-E=0.031006. Thus the diagnostic deprioritizes an unmotivated transition change but does not prove dynamics errors are negligible. Development D remains 0.046667/0.091804.

4. **Smaller latent error has not produced clear value superiority.** Raw H2 L is around 0.08/0.10 versus value-dynamics 0.58/0.75 on train, but their value errors are close. Part of this can be scale/coordinate choice. No causal claim follows from comparing cross-model L. The current auxiliary moving EMA target can also become harder while value learning improves: raw H2 training-stream auxiliary rises from 0.054402 at epoch 10 to 0.087253 at epoch 40. That is not by itself divergence.

5. **The available histories do not demonstrate convergence.** Encoded training-stream MSE falls from epoch 20 to 40 in every family: direct 0.471572 to 0.425267; value-dynamics 0.480364 to 0.436578; decoded 0.481655 to 0.436278; rjepa 0.482594 to 0.437288; raw 0.481338 to 0.439799; no-response 0.491961 to 0.456344. Policy NLL and recurrent value errors also improve. New fixed-probe learning curves are needed because resampled epoch averages alone do not establish the later slope or generalization benefit.

6. **Train/development gaps are heterogeneous.** Raw H2 E gaps are +0.047264 Connect4 and +0.012545 Reversi, while P gaps are +0.084952 and +0.063671. Some H1 development errors are lower because priors/composition differ. These are already exposed descriptive splits, not evidence that the next design will generalize. No additional development queries are necessary for the next fit-capacity diagnosis.

### A finite prospective training-only test (proposal, not frozen)

Before any fits, freeze `docs/METHOD_V23_DIAGNOSTIC.md`, source identities, deterministic training probes, and resource limits. The proposed bounded study is three unchanged families (direct, value-dynamics, raw-jepa), two capacity configurations (hidden/latent 64/32 versus 128/64), and three paired seeds (17,29,43): **18 runs**. Keep the full-label train roots, existing valid augmentation, fork sampler, labels, learning rate 0.001, and weights 1/1/0.1 unchanged. Larger latent width also changes transition and value/policy head capacity: this is a total-model-capacity diagnostic, not an isolated encoder-width treatment. Decoded remains a required strong control for any later claim-bearing development comparison; excluding it from this limited optimization diagnosis cannot support JEPA superiority.

Rerun each cell from paired initialization for at most 160 epochs, preserving checkpoints/probe records at initialization and epochs 40, 80 and 160. The small-model epoch-40 trajectory should reproduce its existing run within declared numerical tolerance before interpreting later epochs. Do not mutate a frozen 40-epoch checkpoint identity into a longer run. A new source/config identity must cover the complete diagnostic. No development evaluator imports, development probes, extra search or new oracle labels belong in this runtime.

Evaluate a fixed training-only probe over all original train roots and complete valid H0/H1/H2 states. Keep H1 deduplication and H2 path counting explicit. Report root-balanced and transition-weighted value MSE, class-conditioned signed errors/calibration, policy NLL, baseline-normalized improvement, E/P/D/cross term, effective rank and gradient diagnostics. Supply all/terminal/nonterminal strata; terminal behavior is not the same as learned nonterminal planning. A fixed legal-symmetry probe may be added only if frozen first. No adaptively selected difficult roots are allowed.

Proposed convergence screening: for each game and family, report relative fixed-probe encoded-MSE improvement `(E80-E160)/max(E80,1e-12)` with all three seeds. Less than 5% improvement is merely a **near-flat observed interval**, not proof of optimization convergence; require consistency in at least two of three seeds and expose every horizon/stratum rather than hiding disagreement behind a pooled scalar. Freeze the exact primary training aggregate before fitting. If any relevant family/game still improves materially at 160, retain that nonconvergence result instead of extending the run. Training MSE and the resource cap may shortlist a capacity/budget for a later prospective study, but training fit cannot promote a JEPA model or replace the existing 0.05 development margin.

Measured selected Grid02 40-epoch median receipt runtimes are 15.3664 seconds for direct, 12.8369 for value-dynamics, and 13.7487 for raw JEPA. Linear extrapolation for the small model gives approximately 61.47, 51.35 and 54.99 seconds at 160 epochs, before the new diagnostics. These are rough budget references, not measured 160-epoch runtimes; larger matrix products, diagnostic work and machine load can change them. A prospective cap of 300 seconds per cell and 5,400 seconds total for 18 cells, with `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1`, leaves a bounded local test. Count checkpoint/probe I/O inside the budget. Censored/failed runs remain visible and make the corresponding diagnosis inconclusive.

If the small model continues learning, the former 40-epoch budget was not a demonstrated plateau. If it is near-flat while the large model fits better, total capacity is implicated only provisionally, because capacity and work per update both change. If neither fits beyond priors sufficiently, audit perspective, sampling/calibration and objective interactions before inventing another latent loss. Report these alternatives for all families rather than choosing the pattern most favorable to JEPA. Any subsequent development grid must separately freeze its design, include decoded and relevant EMA-value controls, account for resource differences, retain failed attempts and leave locked-final data untouched. This paragraph is a proposal; it does not authorize fits before the root-owned method freeze.

## History provenance

| Run | Current history SHA-256 |
| --- | --- |
| direct-lr0.001-w1-s17 | `a015c1883c3f4789b11d3d44d75baf8bd9a476f0b45c8151b9d4f6fe1d32fe77` |
| direct-lr0.001-w1-s29 | `041e8e719871d4a32865a1f8ce750cc37bcd9b6a285efad394e9538ee02667ce` |
| direct-lr0.001-w1-s43 | `2333cfeb54dddb26a229e83ab99242239922e3aa1f5a98497d6f60024709b04c` |
| value-dynamics-lr0.001-w1-s17 | `40510d612dafa1cec5f7392fde3a0086a7c6c2da298ae3b8080a4fb2ef5cd6cc` |
| value-dynamics-lr0.001-w1-s29 | `422150c42ad1c0f095a6d62519f5fe601c23de5b5685a3dc6324212cf38e0ec0` |
| value-dynamics-lr0.001-w1-s43 | `f76208b6ca209a87233014b5aa2a7cda42f206a988ab67279ebc435e49f9e555` |
| decoded-lr0.001-w0.1-s17 | `b6849e577fdcfb186d0d8957739a9311fa7e39482dcbb44be52f6d14a351f94f` |
| decoded-lr0.001-w0.1-s29 | `3417e8920d0a80f2f96ad73c775c4f9c321f0ca069e2433433f31dc41185e15d` |
| decoded-lr0.001-w0.1-s43 | `c22cdb95034d6547df992ec463e48e1c7218384089fb4da9401c9d2353da734e` |
| rjepa-lr0.001-w0.1-s17 | `9fc3a827b2a7813c8aebc118e518d5050d8506d257176f63f4185839ea3fb864` |
| rjepa-lr0.001-w0.1-s29 | `eb1d7e808ced7907785a86dd15ab9c11f55194cfd452d49d04acb467e1a28a73` |
| rjepa-lr0.001-w0.1-s43 | `91276956237d637b0d192d9545f5cedf416c4a20aa4d03cf9e20039184c8726b` |
| raw-jepa-lr0.001-w0.1-s17 | `9ece41b2b044e936462ed5b73af27f3a0d9db3584003c6ba34f73e84ee25c2cd` |
| raw-jepa-lr0.001-w0.1-s29 | `79c490557083148660eae204b4e3e94ea6f6317383a396c4f1a777ba438dfe43` |
| raw-jepa-lr0.001-w0.1-s43 | `820286b6cf4cd02ff80ddabdefe24eedc86d1960308d39d3ba4ebdd9ade57eda` |
| no-response-lr0.001-w1-s17 | `710d144dfac7da33f6999b47e7ff15c61e86e202bab0dd9b7de290ccdeae0485` |
| no-response-lr0.001-w1-s29 | `4728ab57697950d8c1b6ec534853dd7a365816152f150a57a9ba3dc94e079721` |
| no-response-lr0.001-w1-s43 | `293770e55b2fcf794f7c7a674a7904f700ed5b5125db2ec0845ad4255575a582` |
