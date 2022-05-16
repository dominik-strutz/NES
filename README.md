# Neural Eikonal Solver
**Neural Eikonal Solver (NES)** is framework for solving factored eikonal equation using physics-informed neural network, for details see our [paper](https://github.com/sgrubas/NES).

## Tutorials
See quick introduction on [Google Colab](https://colab.research.google.com/github/sgrubas/NES/blob/main/notebooks/NES_Introduction.ipynb)

NES has two versions:
1.   **One-Point NES (NES-OP)** is to solve conventional one-point eikonal ([NES-OP tutorial](https://github.com/sgrubas/NES/blob/main/notebooks/NES-OP_Tutorial.ipynb))
<p align="center">
<img src="https://render.githubusercontent.com/render/math?math=|\nabla \tau|=\displaystyle\frac{1}{v}">
</p>

3.   **Two-Point NES (NES-TP)** is to solve generalized two-point eikonal ([NES-TP tutorial](https://github.com/sgrubas/NES/blob/main/notebooks/NES-TP_Tutorial.ipynb))
<p align="center">
<img src="https://render.githubusercontent.com/render/math?math=|\nabla_r T|=\displaystyle\frac{1}{v_r}"> &nbsp;&nbsp;   
<img src="https://render.githubusercontent.com/render/math?math=|\nabla_s T|=\displaystyle\frac{1}{v_s}">
</p>

For comparison with existing neural-network solutions see [EikoNet](https://github.com/sgrubas/NES/blob/main/notebooks/EikoNet_NES-TP_Marmousi.ipynb) and [PINNeik](https://github.com/sgrubas/NES/blob/main/notebooks/PINNeik_NES-OP_Marmousi.ipynb)

## Installation
```python
pip install git+https://github.com/sgrubas/NES.git
```

# Quick example
```python
import NES

Vel = NES.misc.MarmousiSmoothedPart()
Eik = NES.NES_TP(velocity=Vel)
Eik.build_model()
h = Eik.train(x_train=100000, epochs=1000, batch_size=25000)

grid = NES.utils.RegularGrid(Vel)
Xs = grid((5, 5)); Xr = grid((100, 100))
X = grid.sou_rec_pairs(Xs, Xr)
T = Eik.Traveltime(X)
```

# Citation
If you find NES useful for your research, please cite:
```
@article{grubas2022nes,
  title={Neural Eikonal Solver: improving accuracy of physics-informed neural networks for solving eikonal equation in case of caustics},
  author={Grubas, Serafim I and Loginov, Georgy N and Duchkov, Anton A},
  journal={######},
  year={2022},
}
```

# Future plans
*  Anisotropic eikonal
*  Earthquake localization
*  Traveltime tomography

# Developers
Serafim Grubas (serafimgrubas@gmail.com) <br>
Nikolay Shilov <br>
Anton Duchkov <br>
Georgy Loginov
