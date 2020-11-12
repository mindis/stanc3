import time, datetime
import os, sys, traceback, logging, argparse
import numpy, numpyro

from typing import Any, Dict, IO
from dataclasses import dataclass, field
from pandas import DataFrame, Series
from posteriordb import PosteriorDatabase
from os.path import splitext, basename
from runtimes.dppl import NumpyroModel as Model, _flatten_dict

logger = logging.getLogger(__name__)


@dataclass
class Config:
    iterations: int
    warmups: int
    chains: int
    thin: int


def parse_config(posterior):
    args = posterior.reference_draws_info()["inference"]["method_arguments"]
    return Config(
        iterations=args["iter"],
        warmups=args["warmup"],
        chains=args["chains"],
        thin=args["thin"],
    )


def gold_summary(posterior):
    """
    Summary for pdb reference_draws
    - Aggregate all chains and compute mean, std for all params
    - Flatten results in a DataFrame
    """
    samples = posterior.reference_draws()
    if isinstance(samples, list):
        # Multiple chains
        assert len(samples) > 0
        res = samples[0]
        for c in samples[1:]:
            res = {k: v + c[k] for k, v in res.items()}
    else:
        # Only one chain
        assert isinstance(samples, dict)
        res = samples
    d_mean = _flatten_dict({k: numpy.mean(v, axis=0) for k, v in res.items()})
    d_std = _flatten_dict({k: numpy.std(v, axis=0) for k, v in res.items()})
    return DataFrame({"mean": Series(d_mean), "std": Series(d_std)})


def run_model(*, posterior, mode, config):
    """
    Compile and run the model.
    Returns the summary Dataframe
    """
    model = posterior.model
    data = posterior.data
    stanfile = model.code_file_path("stan")
    pyro_model = Model(stanfile, recompile=True, mode=mode)
    mcmc = pyro_model.mcmc(
        config.iterations,
        warmups=config.warmups,
        chains=config.chains,
        thin=config.thin,
    )
    inputs = pyro_model.module.convert_inputs(data.values())
    mcmc.run(**inputs)
    return mcmc.summary()


class ComparisonError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def compare(*, posterior, mode, config):
    """
    Compare gold standard with model.
    """
    logger.info(f"Processing {posterior.name}")
    sg = gold_summary(posterior)
    sm = run_model(posterior=posterior, mode=mode, config=config)
    sm["err"] = abs(sm["mean"] - sg["mean"])
    sm = sm.dropna()
    # perf_cmdstan condition: err > 0.0001 and (err / stdev) > 0.3
    comp = sm[(sm["err"] > 0.0001) & (sm["err"] / sg["std"] > 0.3)].dropna()
    if not comp.empty:
        logger.error(f"Failed {posterior.name}")
        raise ComparisonError(str(comp))
    else:
        logger.info(f"Success {posterior.name}")


@dataclass
class Monitor:
    name: str
    file: IO

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        duration = time.perf_counter() - self.start
        if exc_type == ComparisonError:
            print(f"{name},False,{duration}", file=self.file, flush=True)
        elif exc_type is not None:
            err = " ".join(traceback.format_exception_only(exc_type, exc_value)).rstrip()
            logger.error(f"Failed {self.name} with {err}")
            print(f'{name},False,NaN, "{err}"', file=self.file, flush=True)
        else:
            print(f"{name},True,{duration}", file=self.file, flush=True)
        return True


## Stan gold models
# golds = [
#     "arK",
#     "arma",
#     "eight_schools",
#     "garch",
#     "gp_pois_regr",
#     "gp_regr",
#     "irt_2pl",
#     "low_dim_corr_gauss",
#     "low_dim_gauss_mix_collapse",
#     "low_dim_gauss_mix",
#     "sir",
# ]

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Run experiments on PosteriorDB models."
    )
    parser.add_argument(
        "--mode",
        help="compilation mode (generative, comprehensive, mixed)",
        required=True,
    )
    parser.add_argument("--iterations", type=int, help="number of iterations")
    parser.add_argument("--warmups", type=int, help="warmups steps")
    parser.add_argument("--chains", type=int, help="number of chains")
    parser.add_argument("--thin", type=int, help="thinning factor")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    numpyro.set_host_device_count(20)
    # numpyro.set_platform('gpu')

    pdb_root = "/home/baudart/projects/deepstan/posteriordb"
    pdb_path = os.path.join(pdb_root, "posterior_database")
    my_pdb = PosteriorDatabase(pdb_path)

    today = datetime.datetime.now()
    logpath = f"{today.strftime('%y%m%d_%H%M')}_numpyro_{args.mode}.csv"

    def test_ref(name):
        try:
            posterior = my_pdb.posterior(name)
            posterior.reference_draws_info()
            return True
        except Exception:
            return False

    golds = [x for x in my_pdb.posterior_names() if test_ref(x)]

    with open(logpath, "a") as logfile:
        print(",status,time,exception", file=logfile, flush=True)
        for name in (n for n in golds):
            with Monitor(name, logfile):
                posterior = my_pdb.posterior(name)
                config = parse_config(posterior)
                if args.iterations:
                    config.iterations = args.iterations
                if args.warmups:
                    config.warmups = args.warmups
                if args.chains:
                    config.chains = args.chains
                if args.thin:
                    config.thin = args.thin
                compare(posterior=posterior, mode=args.mode, config=config)
