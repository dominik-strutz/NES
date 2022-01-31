import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter
import pkg_resources


######################################################
                ### VELOCITY CLASSES ###
######################################################


class Interpolator:
    """
        Interpolator using 'scipy.interpolate.RegularGridInterpolator'

    """    
    dim = None
    F = None
    dF = None
    LF = None
    axes = None
    Func = None
    dFunc = None
    LFunc = None
    xmin = None
    xmax = None
    min = None
    max = None

    def __init__(self, F, *axes, **interp_kw):
        """
        The interpolator uses 'scipy.interpolate.RegularGridInterpolator'
        
        Arguments:
            F: numpy array (nx,) or (nx,ny) or (nx,ny,nz)
                Values 
            axes: tuple of numpy arrays (nx,), (ny), (nz)
                Grid
            interp_kw: dictionary of keyword arguments for 'scipy.interpolate.RegularGridInterpolator'
        """
        self.dim = len(F.shape)
        self.axes = axes
        self.F = F
        self.Func = RegularGridInterpolator(axes, F, **interp_kw)

        self.xmin = [xi.min() for xi in axes]
        self.xmax = [xi.max() for xi in axes]
        self.min = F.min()
        self.max = F.max()

    def __call__(self, X):
        """
        Computes values of function using interpolation at points X
        """
        return self.Func(X)

    def gradient(self, X, **interp_kw):
        """
        Computes partial derivatives (using default np.gradient) of function using interpolation at points X
        """
        if self.dFunc is None:
            self.dF = np.stack(np.gradient(self.F, *self.axes), axis=-1)
            self.dFunc = RegularGridInterpolator(self.axes, self.dF, **interp_kw)
        return self.dFunc(X)

    def laplacian(self, X, **interp_kw):
        """
        Computes laplacian (using default np.gradient) of function using interpolation at points X
        """
        if self.dFunc is None:
            self.dF = np.stack(np.gradient(self.F, *self.axes), axis=-1)
            self.dFunc = RegularGridInterpolator(self.axes, self.dF, **interp_kw)

        if self.LFunc is None:
            d2F = [np.gradient(self.dF[...,i], xi, axis=i) for i, xi in enumerate(self.axes)]
            L = np.sum(np.stack(d2F, axis=-1), axis=-1)
            self.LFunc = RegularGridInterpolator(self.axes, L, **interp_kw)

        return self.LFunc(X)

class VerticalGradient:
    """
        Velocity class for vertical gradient model
    """
    v0 = None
    a = None
    xmin = None
    xmax = None
    min = None
    max = None
    dim = None

    def __init__(self, v0, a, xmin=None, xmax=None):
        """ v0 : initial velocity ar z=0
            a : gradient of velocity
        """
        self.v0 = v0
        self.a = a
        self.xmin = xmin
        self.xmax = xmax

    def __call__(self, X):
        """ Computes the velocity value at 'X', where X is (...., dim), and z=X[..., -1]
        """
        if self.xmin is None:
            self.xmin = X.reshape(-1, X.shape[-1]).min(axis=0)
        if self.xmax is None:
            self.xmax = X.reshape(-1, X.shape[-1]).max(axis=0)
        if self.dim is None:
            self.dim = X.shape[-1]

        V = self.v0 + self.a * X[..., -1]

        if self.min is None:
            self.min = V.min()
        if self.max is None:
            self.max = V.max()

        return V

    def gradient(self, X):
        """ Computes the gradient of velocity value at 'X'
        """
        return np.concatenate([np.zeros_like(X[..., :-1]), 
            np.full_like(X[..., -2:-1], self.a)], axis=-1)

    def time(self, X, xs):
        """ Computes the analytical traveltimes at 'X'
        """
        Xdiff = X - xs[None,:]
        Vxszs = self(xs)
        up = self.a**2 * (Xdiff**2).sum(axis=-1)
        down = 2 * Vxszs * (self.a * Xdiff[...,-1] + Vxszs)
        tau = np.arccosh(up / down + 1) / self.a
        return tau

    def dtime(self, X, xs):
        """ Computes the analytical gradient of traveltimes at 'X'
        """
        Xdiff = X - xs[None,:]
        Vxszs = self(xs)
        up = self.a*2 * (Xdiff**2).sum(axis=-1)
        down = 2 * Vxszs * (self.a * Xdiff[...,-1] + Vxszs)
        A = 1 / self.a / np.sqrt((up / down + 1)**2 - 1)
        dt_dx = 2 * self.a**2 * Xdiff[...,0] / down * A
        dt_dz = (2 * self.a**2 * Xdiff[...,-1] / down - 2 * self.a * Vxszs * up / down**2) * A
        return np.stack([dt_dx, dt_dz], axis=-1)

class LocAnomaly:
    """
        Velocity class for model with gaussian anomaly
    """
    mus = None
    sigmas = None
    xmin = None
    xmax = None
    min = None
    max = None
    dim = None

    def __init__(self, vmin, vmax, mus, sigmas, xmin=None, xmax=None):
        """ vmin : minimal velocity
            vmax : maximal velocity
            mus : center of gaussian anomaly
            sigmas : width of gaussian anomaly
            xmin : [x_min, y_min, z_min] lower bound of the domain
            xmax : [x_max, y_max, z_max] upper bound of the domain
        """
        self.mus = np.array(mus).reshape(1, -1)
        self.sigmas = np.array(sigmas).reshape(1, -1)
        self.min = min(vmin, vmax)
        self.max = max(vmin, vmax)
        self.vmin = vmin
        self.vmax = vmax
        self.xmin = xmin
        self.xmax = xmax
        self.dim = len(mus)

    def __call__(self, X):
        """ Computes the velocity value at 'X'
        """
        if self.xmin is None:
            self.xmin = X.reshape(-1, X.shape[-1]).min(axis=0)
        if self.xmax is None:
            self.xmax = X.reshape(-1, X.shape[-1]).max(axis=0)

        V = (self.vmax - self.vmin) 
        V *= np.exp(- ((X - self.mus)**2 / 2 / self.sigmas**2).sum(axis=-1))
        return V + self.vmin

    def gradient(self, X):
        """ Computes the analytical gradient of velocity at 'X'
        """
        return (self.__call__(X) - self.vmin)[..., None] * (self.mus - X) / self.sigmas

def Marmousi(smooth=None, section=None):
    """
        Creates Interpolator of Marmousi model

        Arguments:
            smooth : float : smoothes model using "scipy.ndimage.gaussian_filter(sigma=smooth)"
                             If 'None', smoothing is not applied
            section : list of ints : indices to cut out a rectangle part of Marmousi model. 
                                     Example - 'section = [[100, 200], [0, 150]]' 
                                     where the first pair is for axis 0, the second - axis 1
        Return:
            Vel : instance of 'NES.Interpolator' for Marmousi model in 'km/s' units
    """
    f = pkg_resources.resource_stream(__name__, "data//Marmousi_Pwave_smooth_12_5m.npy")
    V = np.load(f) / 1000.0
    if section is not None:
        i = [0, V.shape[0]+1] if section[0] is None else section[0]
        j = [0, V.shape[1]+1] if section[1] is None else section[1]
        V = V[i[0] : i[1], j[0] : j[1]]
    if smooth is not None:
        V = gaussian_filter(V, sigma=smooth)

    nx, nz = V.shape
    xmin, xmax = 0.0, .0125 * nx
    zmin, zmax = 0.0, .0125 * nz
    x = np.linspace(xmin, xmax, nx)
    z = np.linspace(zmin, zmax, nz)
    Vel = Interpolator(V, x, z)
    return Vel

def MarmousiSmoothedPart():
    """
        Return smoothed central part of Marmousi model 'NES.Marmousi(smooth=3, section=[[600, 900], None])' 
    """
    return Marmousi(smooth=3, section=[[600, 900], None])


######################################################
        ### GENERATION OF COLLOCATION POINTS ###
######################################################

class RegularGrid:
    """
        API for generating regular distribution in a given velocity model
    """
    limits = None 
    def __init__(self, velocity):
        """velocity: velocity class
        """
        self.xmins = velocity.xmin
        self.xmaxs = velocity.xmax

    def __call__(self, axes):
        """ axes : tuple of ints : (nx, ny, nz)
        """
        xi = [np.linspace(self.xmins[i], self.xmaxs[i], axes[i]) for i in range(len(axes))]
        X = np.meshgrid(*xi, indexing='ij')
        X = np.stack(X, axis=-1)
        return X

class Uniform_PDF:
    """
        API for generating uniform distribution in a given velocity model
    """
    limits = None 
    def __init__(self, velocity):
        """velocity: velocity class
        """
        xmins = velocity.xmin
        xmaxs = velocity.xmax
        self.limits = np.array([xmins, xmaxs]).T

    def __call__(self, num_points):
        """ Return random points from uniform distribution in a given domain
        """
        return np.random.uniform(*self.limits.T, 
            size=(num_points, len(self.limits)))


class GradientBased_PDF:
    """
        API for generating gradient based distribution in a given velocity model
    """
    limits = None 
    def __init__(self, velocity):
        """velocity: velocity class
        """
        xmins = velocity.xmin
        xmaxs = velocity.xmax
        self.grad_func = velocity.gradient
        self.limits = np.array([xmins, xmaxs]).T

    def __call__(self, num_pts, regular=0.7, random_base=20000):
        """ Return random points from uniform distribution in a given domain
        """
        reg_num = int(np.sqrt(num_pts * regular))
        x_reg = [np.linspace(*limi, reg_num) for limi in self.limits]
        x_reg = np.stack(np.meshgrid(*x_reg, indexing='ij'), axis=-1)
        x_reg = x_reg.reshape(-1, x_reg.shape[-1])

        rand_num = num_pts - reg_num**2
        x_rand_base = np.random.uniform(*self.limits.T, size=(random_base, len(self.limits)))
        dv = self.grad_func(x_rand_base)
        dv = np.linalg.norm(dv, axis=-1)
        dv += dv.mean()
        dv /= dv.sum()
        rand_ids = np.random.choice(random_base, rand_num, p=dv, replace=False)
        x_rand = x_rand_base[rand_ids]

        x = np.concatenate((x_reg, x_rand), axis=0)
        return x