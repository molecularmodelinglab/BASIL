import gpytorch
import torch
from baybe.kernels import AdditiveKernel, MaternKernel, RQKernel, LinearKernel
from baybe.kernels.base import Kernel
from baybe.surrogates.gaussian_process.components.kernel import PlainKernelFactory



def gp_kernel():
    linear_kernel = LinearKernel(variance_initial_value=0.01)

    rq_kernel = RQKernel(lengthscale_initial_value=0.01)
    matern_kernel = MaternKernel(lengthscale_initial_value=0.1, nu=1.5)

    kernel = AdditiveKernel((linear_kernel, rq_kernel, matern_kernel))
    kernel_factory = PlainKernelFactory(component=kernel)

    return kernel_factory
