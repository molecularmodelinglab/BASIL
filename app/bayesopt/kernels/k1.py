import gpytorch
import torch
from baybe.kernels import AdditiveKernel, MaternKernel, RQKernel
from baybe.kernels.base import Kernel
from baybe.surrogates.gaussian_process.kernel_factory import PlainKernelFactory


class DotProductKernel(Kernel):
    def __init__(self, sigma=1.0):
        super().__init__()
        object.__setattr__(self, "_sigma", sigma)

    @property
    def sigma(self):
        return self._sigma

    def forward(self, X, Y):
        return self.sigma**2 + torch.mm(X, Y.T)

    def to_gpytorch(self, ard_num_dims=None, batch_shape=torch.Size([]), active_dims=None):
        # Map your custom kernel to an existing gpytorch kernel
        return gpytorch.kernels.LinearKernel(
            # num_dims=ard_num_dims,
            batch_shape=batch_shape,
            active_dims=active_dims,
            # variance_prior=None,
            # bias_prior=None,
        )


def gp_kernel():
    dot_product_kernel = DotProductKernel(sigma=0.01)

    rq_kernel = RQKernel(lengthscale_initial_value=0.01)
    matern_kernel = MaternKernel(lengthscale_initial_value=0.1, nu=1.5)

    kernel = AdditiveKernel((dot_product_kernel, rq_kernel, matern_kernel))
    kernel_factory = PlainKernelFactory(kernel=kernel)

    return kernel_factory
