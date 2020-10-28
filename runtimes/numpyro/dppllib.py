import numpyro
import jax.numpy as jnp
from numpyro.distributions import Exponential
from jax.numpy import array
from jax.numpy import zeros, ones, matmul, true_divide, floor_divide, transpose, empty
from jax.ops import index as ops_index
from jax.ops import index_update as ops_index_update
from jax.lax import cond as lax_cond
from jax.lax import while_loop as lax_while_loop
from jax.lax import fori_loop as lax_fori_loop
from jax.lax import map as lax_map


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
