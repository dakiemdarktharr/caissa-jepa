# V2.12 root-schedule yield sensitivity — draft 01

**Status: analytic design sensitivity only.** This note does not freeze a
minimum schedule-pass probability, authorize root generation, or change the
proposed 64-slot/16-accept schedule. No roots, rollouts, simulations, scores,
or outcomes were produced or inspected.

## Question

Root schedule design 02 proposes six variant × occupancy-band strata, with 64
predeclared candidate slots in each and a global pass only when every stratum
has at least 16 valid slots. `V212_ROOT_SAMPLING_REVIEW_01.md` leaves open what
minimum probability of schedule completion is acceptable. This note quantifies
the idealized independent-slot Binomial sensitivity; it does not estimate any
stratum's validity probability.

Let a stratum have per-slot validity probability `p`, with independent,
identically distributed slots. Its pass probability is

```text
q(p) = P[Binomial(64, p) >= 16]
     = sum(k=16..64) C(64,k) p^k (1-p)^(64-k).
```

If all six strata have the same `p` and are mutually independent, the global
schedule-pass probability is `q(p)^6`. For different stratum probabilities
`p_j`, it is `product(q(p_j))`, assuming independence across strata. These
factorizations fail if slot outcomes are dependent, including shared random
streams or common operational failure. Deterministic PRNG stream separation is
an implementation approximation to the independence assumption, not empirical
proof of it.

## Sensitivity under equal stratum yield

| Assumed per-slot validity `p` | One-stratum pass `q(p)` | All-six pass `q(p)^6` |
| ---: | ---: | ---: |
| 0.25 | 0.547869 | 0.027043 |
| 0.30 | 0.843763 | 0.360846 |
| 0.35 | 0.967617 | 0.820767 |
| 0.40 | 0.995989 | 0.976176 |
| 0.45 | 0.999707 | 0.998244 |
| 0.50 | 0.999988 | 0.999927 |

The inverse calculation gives the equal-yield `p` required to meet candidate
global pass-probability targets:

| Illustrative global target | Required per-stratum pass `q` | Equal per-slot yield `p` |
| ---: | ---: | ---: |
| 0.90 | 0.982593 | 0.366219 |
| 0.95 | 0.991488 | 0.383364 |
| 0.99 | 0.998326 | 0.417880 |

The 0.90/0.95/0.99 rows are decision points for review, not accepted thresholds.
Equal-yield rows are optimistic as summaries when strata differ: an average
yield cannot substitute for the six individual `p_j` values, and one low-yield
band can dominate schedule failure.

## Interpretation and limits

- The schedule's no-top-up rule preserves the proposed conditional sampling
  law, but makes schedule failure a real possibility. Increasing the candidate
  count after observing failures would change the frozen design and is not
  covered by these calculations.
- These probabilities are analytic consequences of assumed `p` values, not
  evidence that the six held-out variant/band rollouts attain those yields.
  The game-policy process may induce different validity probabilities by
  variant and band.
- A pre-generation review must decide whether to set a global completion
  threshold, what value to use, and how to handle its failure. The threshold
  must be chosen before observing candidate validity. If probability claims
  are required, they also need a defensible source for each stratum's yield
  assumptions; these calculations supply none.
- This is separate from bootstrap coverage, familywise error, power, and the
  nomination boundary. Passing a yield threshold would establish none of
  those properties and would not make v04's development method current.

## Reproduction

The values above use only the binomial tail and bisection, with no RNG:

```python
from math import comb

def stratum_pass(p):
    return sum(comb(64, k) * p**k * (1-p)**(64-k)
               for k in range(16, 65))

def all_six_pass(p):
    return stratum_pass(p) ** 6
```

No data or generated artifacts are required to reproduce the table. The
schedule remains unapproved: root generation, scoring, fitting, and matches
remain closed pending versioned method decisions and independent review.
