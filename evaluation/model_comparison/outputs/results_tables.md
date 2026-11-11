## 1. Height error after release (RMSE, % of rest height; 0-250 ms; lower is better)
| Model | Family | Window | 0536 train | 0537 train | 0538 TEST | 0539 TEST | test mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stay at rest (baseline) | baseline | from release | 58.8 | 63.3 | 36.4 | 36.8 | **36.6** |
| single exponential (baseline) | baseline | from release | 5.4 | 6.1 | 3.1 | 3.4 | **3.3** |
| bounce + recovery | lumped 1D | after first apex only | - | - | - | - | **-** |
| two-mass spring | lumped 1D | from release | 2.4 | 1.7 | 1.7 | 1.6 | **1.6** |
| fast-snap two-mass | lumped 1D | from release | 1.8 | 1.9 | 1.1 | 1.1 | **1.1** |
| 3D gas shell | 3D spring mesh | from release | 4.6 | 4.4 | 3.7 | 4.1 | **3.9** |
| 3D foam core, height fit | 3D spring mesh | from release | 3.8 | 3.4 | 3.3 | 3.0 | **3.2** |
| 3D foam core, shape fit | 3D spring mesh | from release | 3.0 | 3.8 | 2.0 | 1.7 | **1.9** |
| 3D foam core, no-lift | 3D spring mesh | from release | 1.7 | 1.0 | 1.1 | 1.2 | **1.1** |
| 3D foam core, with-lift | 3D spring mesh | from release | 3.0 | 3.8 | 2.1 | 1.9 | **2.0** |
| axisymmetric FEM, instant release (old protocol) | continuum | from release | 5.2 | 5.7 | 3.1 | 3.1 | **3.1** |
| axisymmetric FEM (Warp) | continuum | from release | 3.2 | 3.2 | 1.9 | 1.4 | **1.7** |
| axisymmetric FEM, damping relative to centre of mass x16 (hop) | continuum | from release | 2.1 | 1.7 | 1.6 | 1.3 | **1.4** |
| 3D MPM, FEM damping | continuum | from release | 3.5 | 3.6 | 2.2 | 1.8 | **2.0** |
| 3D MPM, calibrated damping | continuum | from release | 3.5 | 3.3 | 2.3 | 1.9 | **2.1** |

**Skill against the plain exponential** (1 - model RMSE / exponential RMSE on the same clip; positive = better than the baseline)
| Model | 0536 train | 0537 train | 0538 TEST | 0539 TEST |
| --- | --- | --- | --- | --- |
| two-mass spring | +0.56 | +0.72 | +0.47 | +0.52 |
| fast-snap two-mass | +0.66 | +0.69 | +0.64 | +0.69 |
| 3D gas shell | +0.14 | +0.27 | -0.21 | -0.19 |
| 3D foam core, height fit | +0.29 | +0.45 | -0.08 | +0.12 |
| 3D foam core, shape fit | +0.44 | +0.37 | +0.37 | +0.49 |
| 3D foam core, no-lift | +0.69 | +0.83 | +0.65 | +0.66 |
| 3D foam core, with-lift | +0.44 | +0.38 | +0.33 | +0.46 |
| axisymmetric FEM, instant release (old protocol) | +0.02 | +0.06 | +0.01 | +0.09 |
| axisymmetric FEM (Warp) | +0.41 | +0.48 | +0.39 | +0.58 |
| axisymmetric FEM, damping relative to centre of mass x16 (hop) | +0.62 | +0.72 | +0.49 | +0.63 |
| 3D MPM, FEM damping | +0.34 | +0.41 | +0.27 | +0.48 |
| 3D MPM, calibrated damping | +0.35 | +0.46 | +0.25 | +0.45 |

## 2. Time to 95 % of rest height (ms)
| Model | 0536 train | 0537 train | 0538 TEST | 0539 TEST | mean |error| on test |
| --- | --- | --- | --- | --- | --- |
| **real (SAM 2)** | 34 | 39 | 27 | 24 | - |
| single exponential (baseline) | 26 | 28 | 21 | 22 | 4 |
| bounce + recovery | - | - | - | - | - |
| two-mass spring | 39 | 39 | 35 | 34 | 9 |
| fast-snap two-mass | 30 | 31 | 24 | 24 | 2 |
| 3D gas shell | 14 | 25 | 22 | 9 | 10 |
| 3D foam core, height fit | 21 | 51 | 11 | 10 | 15 |
| 3D foam core, shape fit | 19 | 20 | 16 | 16 | 10 |
| 3D foam core, no-lift | 34 | 35 | 31 | 30 | 5 |
| 3D foam core, with-lift | 19 | 19 | 16 | 15 | 10 |
| axisymmetric FEM, instant release (old protocol) | 34 | 34 | 30 | 30 | 4 |
| axisymmetric FEM (Warp) | 30 | 31 | 24 | 24 | 2 |
| axisymmetric FEM, damping relative to centre of mass x16 (hop) | 33 | 34 | 20 | 20 | 6 |
| 3D MPM, FEM damping | 28 | 29 | 21 | 21 | 4 |
| 3D MPM, calibrated damping | 36 | 37 | 27 | 27 | 2 |

## 3. Pressed width (width while pressed / width at rest) and squeezed-outline squareness n
| Model | 0536 train | 0537 train | 0538 TEST | 0539 TEST | n at hold (mean of clips) |
| --- | --- | --- | --- | --- | --- |
| **real (SAM 2)** | 1.077 | 1.077 | 1.043 | 1.043 | 4.1 |
| 3D gas shell | 1.165 | 1.169 | 1.040 | 1.044 | - |
| 3D foam core, height fit | 1.033 | 1.038 | 1.051 | 1.050 | - |
| 3D foam core, shape fit (curve width; real = 1.069, 1.069, 1.030, 1.029) | 1.010 | 1.014 | 0.991 | 0.992 | 3.2 |
| 3D foam core, no-lift (curve width; real = 1.069, 1.069, 1.030, 1.029) | 1.028 | 1.039 | 0.994 | 0.997 | 3.1 |
| 3D foam core, with-lift (curve width; real = 1.069, 1.069, 1.030, 1.029) | 1.014 | 1.018 | 0.992 | 0.993 | 3.2 |
| axisymmetric FEM, instant release (old protocol) | 1.116 | 1.139 | 1.049 | 1.050 | 4.0 |
| axisymmetric FEM (Warp) | 1.129 | 1.157 | 1.053 | 1.055 | 4.0 |
| axisymmetric FEM, damping relative to centre of mass x16 (hop) | 1.129 | 1.157 | 1.053 | 1.055 | 4.0 |
| 3D MPM, FEM damping | 1.114 | 1.140 | 1.043 | 1.045 | - |
| 3D MPM, calibrated damping | 1.114 | 1.140 | 1.043 | 1.045 | - |

## 4. Hop: peak lift of the bottom edge (mm; real hops are 3-8 mm)
| Model | 0536 train | 0537 train | 0538 TEST | 0539 TEST |
| --- | --- | --- | --- | --- |
| **real (SAM 2)** | 7.1 | 7.5 | 3.3 | 5.4 |
| bounce + recovery | 7.1 | 6.5 | 2.5 | 4.7 |
| two-mass spring | 6.0 | 7.7 | 0.1 | 0.1 |
| fast-snap two-mass | 6.3 | 7.9 | 0.5 | 0.5 |
| 3D gas shell | 12.9 | 14.4 | 5.4 | 4.9 |
| 3D foam core, height fit | 7.4 | 8.2 | 2.8 | 2.3 |
| 3D foam core, shape fit | 5.6 | 6.9 | 0.4 | 0.3 |
| 3D foam core, no-lift | 0.2 | 0.6 | 0.0 | 0.0 |
| 3D foam core, with-lift | 6.4 | 7.8 | 0.9 | 0.7 |
| axisymmetric FEM, instant release (old protocol) | 0.0 | 0.0 | 0.0 | 0.0 |
| axisymmetric FEM (Warp) | 0.0 | 0.0 | 0.0 | 0.0 |
| axisymmetric FEM, damping relative to centre of mass x16 (hop) | 4.3 | 4.5 | 8.0 | 6.3 |
| 3D MPM, FEM damping | 0.0 | 0.0 | 0.0 | 0.0 |
| 3D MPM, calibrated damping | 0.0 | 0.0 | 0.0 | 0.0 |

## 5. Cost of one forward run (s, clip 0538, laptop CPU/GPU)
| Model | seconds |
| --- | --- |
| bounce + recovery | 0.0 |
| two-mass spring | 0.5 |
| fast-snap two-mass | 0.4 |
| 3D gas shell | 2.3 |
| 3D foam core, height fit | 2.8 |
| 3D foam core, shape fit | 3.3 |
| 3D foam core, no-lift | 3.3 |
| 3D foam core, with-lift | 3.3 |
| axisymmetric FEM, instant release (old protocol) | 1.6 |
| axisymmetric FEM (Warp) | 2.0 |
| axisymmetric FEM, damping relative to centre of mass x16 (hop) | 6.9 |
| 3D MPM, FEM damping | 5.8 |
| 3D MPM, calibrated damping | 5.9 |
