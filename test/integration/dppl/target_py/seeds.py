from runtimes.pyro.distributions import *
from runtimes.pyro.dppllib import sample, param, observe, factor, array, zeros, ones, empty, matmul, true_divide, floor_divide, transpose, dtype_long, dtype_float
from runtimes.pyro.stanlib import sqrt_real

def convert_inputs(inputs):
    I = inputs['I']
    n = array(inputs['n'], dtype=dtype_long)
    N = array(inputs['N'], dtype=dtype_long)
    x1 = array(inputs['x1'], dtype=dtype_float)
    x2 = array(inputs['x2'], dtype=dtype_float)
    return { 'I': I, 'n': n, 'N': N, 'x1': x1, 'x2': x2 }

def transformed_data(*, I, n, N, x1, x2):
    # Transformed data
    x1x2 = x1 * x2
    return { 'x1x2': x1x2 }

def model(*, I, n, N, x1, x2, x1x2):
    # Parameters
    alpha0 = sample('alpha0', improper_uniform(shape=[]))
    alpha1 = sample('alpha1', improper_uniform(shape=[]))
    alpha12 = sample('alpha12', improper_uniform(shape=[]))
    alpha2 = sample('alpha2', improper_uniform(shape=[]))
    tau = sample('tau', lower_constrained_improper_uniform(0, shape=[]))
    b = sample('b', improper_uniform(shape=[I]))
    # Transformed parameters
    sigma = true_divide(array(1.0, dtype=dtype_float), sqrt_real(tau))
    # Model
    observe('alpha0__1', normal(array(0.0, dtype=dtype_float), 1000), alpha0)
    observe('alpha1__2', normal(array(0.0, dtype=dtype_float), 1000), alpha1)
    observe('alpha2__3', normal(array(0.0, dtype=dtype_float), 1000), alpha2)
    observe('alpha12__4', normal(array(0.0, dtype=dtype_float), 1000), alpha12)
    observe('tau__5', gamma(array(0.001, dtype=dtype_float),
                            array(0.001, dtype=dtype_float)), tau)
    observe('b__6', normal(array(0.0, dtype=dtype_float), sigma), b)
    observe('n__7', binomial_logit(N,
                                   alpha0 + alpha1 * x1 + alpha2 * x2 + alpha12 * x1x2 + b), n)



def generated_quantities(__inputs__):
    tau = __inputs__['tau']
    # Transformed parameters
    sigma = true_divide(array(1.0, dtype=dtype_float), sqrt_real(tau))
    return { 'sigma': sigma }
