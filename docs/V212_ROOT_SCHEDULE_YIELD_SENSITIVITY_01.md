# V2.12 root-schedule yield sensitivity 01

**Status: analytical sensitivity only.** This note quantifies the proposed
candidate-slot yield rule under an idealized validity model. It does not
estimate validity from data, select an acceptable schedule-pass threshold,
validate the v05 estimand, authorize root generation, or calibrate coverage,
FWER, or power. The v05 root-sampling proposal remains unaccepted; see
`docs/V212_ROOT_SAMPLING_REVIEW_01.md` and
`docs/METHOD_SPEC_V212_V05_ROOT_SAMPLING_DRAFT.md`.

## Proposed yield rule

The draft allocates 64 candidate slots to each of six variant × occupancy-band
strata and requires at least 16 valid slots in every stratum. If a stratum's
candidate slots are independent and have a common validity probability `q`,
its pass probability is

```text
Y(q) = P[Binomial(64, q) >= 16]
     = sum(k=16..64) choose(64, k) q^k (1-q)^(64-k).
```

If the six strata are also independent and share that same `q`, the complete
schedule-pass probability is `Y(q)^6`. With heterogeneous stratum rates and
independent strata it is `product_j Y(q_j)`. These products are not valid when
stratum yields are dependent. Given only marginal pass probabilities `p_j`,
the six-event Fréchet bounds are
`max(0, sum_j p_j - 5) <= P(all six pass) <= min_j p_j`; report these rather
than multiplying marginals unless independence is justified.

## Homogeneous-rate sensitivity

| Assumed per-slot validity `q` | One-stratum pass probability `Y(q)` | Six-stratum pass probability `Y(q)^6` |
| ---: | ---: | ---: |
| 0.25 | 0.547869 | 0.027043 |
| 0.30 | 0.843763 | 0.360846 |
| 0.35 | 0.967617 | 0.820767 |
| 0.3834 | 0.9915 | 0.9500 |
| 0.40 | 0.995989 | 0.976176 |
| 0.4179 | 0.9983 | 0.9900 |
| 0.45 | 0.999707 | 0.998244 |
| 0.50 | 0.999988 | 0.999927 |

Under this model, a 90%, 95%, or 99% whole-schedule pass probability would
require common `q` of approximately 0.3662, 0.3834, or 0.4179 respectively.
Those values are algebraic implications of hypothetical targets, not proposed
acceptance thresholds. The large change between `q=0.30` and `q=0.40` shows why
the six-stratum global stop can fail often even when each individual stratum
has a seemingly reasonable chance of passing.

## Limits and review consequence

No candidate validity rate is currently observed, and equal rates are not
justified across games or occupancy bands. Policy-pair and prefix-length
composition may affect validity; dependence between strata also needs either
an explicit RNG/probability argument or a conservative bound. This calculation
does not estimate any of those quantities and must not be read as a feasibility
result.

Before root generation, independent method/statistical review still needs to
decide whether the protocol should specify a minimum schedule-pass probability,
what target and stratum-rate/dependence assumptions would support it, and
whether the fixed 64-slot allocation is retained. Any changed allocation,
acceptance rule, or estimand requires a versioned amendment and review. No roots,
scores, outcomes, data, or model were generated or accessed for this note.
