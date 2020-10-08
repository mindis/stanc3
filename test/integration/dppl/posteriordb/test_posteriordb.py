from dataclasses import dataclass, field
from posteriordb import PosteriorDatabase
from os.path import splitext, basename
import os
from runtimes.pyro.dppl import PyroModel
from runtimes.numpyro.dppl import NumpyroModel

import numpy as np
from jax import numpy as jnp
from torch import tensor
import torch

pdb_root = "/Users/lmandel/stan/posteriordb"
pdb_path = os.path.join(pdb_root, "posterior_database")

@dataclass
class Config:
    # iterations: int = 100
    # warmups: int = 10
    # chains: int = 1
    # thin: int = 2
    iterations: int = 1
    warmups: int = 0
    chains: int = 1
    thin: int = 1


def _convert_to_tensor(value, typ):
    if isinstance(value, (list, np.ndarray)):
        if typ == 'int':
            return tensor(value, dtype=torch.long)
        elif typ == 'real':
            return tensor(value, dtype=torch.float)
        else:
            raise "error"
    else:
        return value

def test(posterior, config):
    model = posterior.model
    data = posterior.data
    stanfile = model.code_file_path("stan")
    pythonfile = os.path.join(os.getcwd(), splitext(basename(stanfile))[0] + ".py")
    try:
        pyro_model = PyroModel(stanfile, pyfile=pythonfile)
    except Exception as e:
        return { 'code': 1, 'msg': f'compilation error ({posterior.name}): {model.name}', 'exn': e }
    try:
        mcmc = pyro_model.mcmc(config.iterations,
                               warmups=config.warmups,
                               chains=config.chains,
                               thin=config.thin)
        # inputs_info = model.information['inputs']
        # inputs = {k: _convert_to_tensor(data.values()[k], v['type']) for k, v in inputs_info.items()}
        inputs = pyro_model.convert_inputs(data.values())
        mcmc.run(**inputs)
    except Exception as e:
    # except torch.Tensor as e:
        return { 'code': 2, 'msg': f'Inference error ({posterior.name}): {model.name}({data.name})', 'exn': e }
    return { 'code': 0, 'samples': mcmc.get_samples() }


my_pdb = PosteriorDatabase(pdb_path)

xfail = [ ('soil_carbon-soil_incubation', 'bad model') ]
bugs = [
    # rep_matrix?
    ('ecdc0501-covid19imperial_v2', 'rep_matrix'),
    ('ecdc0401-covid19imperial_v2', 'The expanded size of the tensor (14) must match the existing size (6) at non-singleton dimension 0'),
    ('ecdc0501-covid19imperial_v3', 'rep_matrix'),
    ('ecdc0401-covid19imperial_v3', 'The expanded size of the tensor (14) must match the existing size (6) at non-singleton dimension 0.'),
    ('diamonds-diamonds', 'The expanded size of the tensor (24) must match the existing size (25) at non-singleton dimension 0'),
    # not defined (hard?)
    ('hudson_lynx_hare-lotka_volterra', 'integrate_ode_rk45 is not defined'),
    ('sir-sir', 'integrate_ode_rk45 is not defined'),
    ('one_comp_mm_elim_abs-one_comp_mm_elim_abs', 'integrate_ode_bdf is not defined'),
    ('gp_pois_regr-gp_pois_regr', 'cov_exp_quad is not defined'),
    ('gp_pois_regr-gp_regr', 'cov_exp_quad is not defined'),
    # not defined (easy?)
    ('mnist-nn_rbm1bJ100', 'append_col is not defined'),
    ('mnist_100-nn_rbm1bJ10', 'append_col is not defined'),
    ('mcycle_gp-accel_gp', 'dims is not defined'),
    ('dogs-dogs_log', 'inv_logit is not defined'),
    # ('low_dim_gauss_mix_collapse', 'log_mix is not defined'),
    # ('low_dim_gauss_mix_collapse-low_dim_gauss_mix_collapse', 'log_mix is not defined'),
    # ('normal_2-normal_mixture', 'log_mix'),
    ('mcycle_splines-accel_splines', 'dot is not defined'),
    # ('sblrc-blr', 'dot is not defined'),
    # ('sblri-blr', 'dot is not defined'),
    ('ovarian-logistic_regression_rhs', 'std_normal is not defined'),
    ('prostate-logistic_regression_rhs', 'std_normal is not defined'),
    # compile?
    ('butterfly-multi_occupancy', 'Tensor object is not callable'),
    # ('rstan_downloads-prophet', 'index 1 is out of bounds for dimension 0 with size 1'),
    ('dogs-dogs', 'result type Float can t be cast to the desired output type Long'),
    ('irt_2pl-irt_2pl', 'result type Float can t be cast to the desired output type Long'),
    ('election88-election88_full', 'result type Float can t be cast to the desired output type Long'),
    ('arma-arma11', 'one of the variables needed for gradient computation has been modified by an inplace operation'),
    ('garch-garch11', 'one of the variables needed for gradient computation has been modified by an inplace operation') ]

constraints = [
    ('bball_drive_event_0-hmm_drive_0', 'hmm_drive_0'),
    ('bball_drive_event_1-hmm_drive_1', 'hmm_drive_1'),
    ('hmm_example-hmm_example', 'hmm_example'),
    ('prideprejustice_chapter-ldaK5', 'ldaK5'),
    ('prideprejustice_paragraph-ldaK5', 'ldaK5'),
    ('sat-hier_2pl', 'hier_2pl'),
    ('low_dim_gauss_mix-low_dim_gauss_mix', 'low_dim_gauss_mix'),
    ('normal_5-normal_mixture_k', 'normal_mixture_k') ]

# posterior = my_pdb.posterior('mesquite-logmesquite_logvas')
# posterior = my_pdb.posterior('radon_mn-radon_variable_intercept_centered')
# posterior = my_pdb.posterior('mesquite-logmesquite_logvas')
# posterior = my_pdb.posterior('irt_2pl-irt_2pl')
# posterior = my_pdb.posterior('butterfly-multi_occupancy')
# posterior = my_pdb.posterior('mcycle_gp-accel_gp')
# posterior = my_pdb.posterior('election88-election88_full')
# posterior = my_pdb.posterior('dogs-dogs_log')
# posterior = my_pdb.posterior('sblri-blr')
# posterior = my_pdb.posterior('rstan_downloads-prophet')
# posterior = my_pdb.posterior('ecdc0401-covid19imperial_v2')
# posterior = my_pdb.posterior('dogs-dogs')
# posterior = my_pdb.posterior('mcycle_gp-accel_gp')
# posterior = my_pdb.posterior('mnist_100-nn_rbm1bJ10')
# posterior = my_pdb.posterior('garch-garch11')
# posterior = my_pdb.posterior('prostate-logistic_regression_rhs')
# config = Config()
# res = test(posterior, config)
# print(res['code'])
# print(res['msg'])
# print(res['exn'])

success = 0
compile_error = 0
inference_error = 0

for name in my_pdb.posterior_names():
# for name, _ in bugs:
    print(f'- Test {name}')
    posterior = my_pdb.posterior(name)
    config = Config()
    res = test(posterior, config)
    if res['code'] == 0:
        success = success + 1
    elif res['code'] == 1:
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        print(res['msg'])
        print(res['exn'])
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        compile_error = compile_error + 1
    elif res['code'] == 2:
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        print(res['msg'])
        print(res['exn'])
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        inference_error = inference_error + 1
    print(f'success: {success}, compile errors: {compile_error}, inference errors: {inference_error}, total: {success + compile_error + inference_error}')