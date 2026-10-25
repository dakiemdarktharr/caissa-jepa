Table 1. Finite development-screen counts; screens reuse the same episodes.

| Screen | Game | Episodes | No candidate | Complete / attempted | Pairable | Potential nonzero support |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | connect4-6x7 | 50 | 43 | 7 / 7 | 0 | 0 |
| 1 | reversi6 | 50 | 0 | 50 / 50 | 11 | 4 |
| 2 | connect4-6x7 | 50 | 41 | 9 / 9 | 0 | 0 |
| 2 | reversi6 | 50 | 0 | 50 / 50 | 11 | 4 |

Potential support was diagnosed after screen 1 and frozen as a necessary gate before screen 2. It is not actual model matching.

Table 2. Builder resources; excludes tests, agent work and rendering.

| Screen | Wall seconds | CPU seconds | Peak RSS bytes | Windows train / development |
| --- | ---: | ---: | ---: | ---: |
| 1 | 15.551 | 15.392 | 80,281,600 | 256 / 64 |
| 2 | 16.308 | 16.143 | 80,220,160 | 256 / 64 |
