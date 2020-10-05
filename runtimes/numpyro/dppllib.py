import numpyro
import jax.numpy as jnp
from numpyro.distributions import Exponential
from jax.numpy import array
from jax.numpy import zeros, ones, matmul, true_divide, floor_divide, transpose, empty

dtype_float=jnp.dtype('float32')
dtype_long=jnp.dtype('int32')

def sample(site_name, dist):
    return numpyro.sample(site_name, dist)

def param(site_name, init):
    return numpyro.param(site_name, init)

def observe(site_name, dist, obs):
    numpyro.sample(site_name, dist, obs = obs)

def factor(site_name, x):
    numpyro.sample(site_name, Exponential(1), obs=-x)

def register_network(name, x):
    numpyro.module(name, x)
