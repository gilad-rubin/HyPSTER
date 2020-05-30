# AUTOGENERATED! DO NOT EDIT! File to edit: 03_hypster_prepare.ipynb (unless otherwise specified).

__all__ = ['HypsterPrepare', 'prepare', 'run_func_test']

# Cell
from .oo_hp import *

# Cell
from inspect import signature
import functools
from collections import OrderedDict

# Cell
class HypsterPrepare(HypsterBase):
    def __init__(self, call, base_call, *args, **kwargs):
        self.call            = call
        self.base_call       = base_call
        self.args            = args
        self.kwargs          = kwargs
        self.trials_sampled  = set()
        self.studies_sampled = set()
        self.base_object     = None
        self.result          = None

    def sample(self, trial):
        if trial.study.study_name not in self.studies_sampled:
            self.trials_sampled = set()
        elif trial.number in self.trials_sampled:
            return self.result

        if self.base_call is not None:
            self.base_object = self.base_call.sample(trial)

        #TODO: add HpToggle Here
        #self.sampled_args   = [sample_hp(arg, trial) for arg in self.args]
        #sampled_kwargs      = [sample_hp(arg, trial) for arg in self.kwargs.values()]
        #self.sampled_kwargs = OrderedDict(zip(self.kwargs.keys(), sampled_kwargs))

        self.sampled_args   = populate_iterable(self.args, trial)
        self.sampled_kwargs = populate_dict(self.kwargs, trial)

        self.trials_sampled.add(trial.number)
        self.studies_sampled.add(trial.study.study_name)

        if self.base_object:
            if len(self.sampled_args) == 0 and len(self.sampled_kwargs) == 0:
                self.result = getattr(self.base_object, self.call)
            else:
                self.result = getattr(self.base_object, self.call)(*self.sampled_args, **self.sampled_kwargs)
        else:
            self.result = self.call(*self.sampled_args, **self.sampled_kwargs)
        return self.result

    def __call__(self, *args, **kwargs):
        #print(f"args {args}, kwargs {kwargs}")
        self.args = args
        self.kwargs = kwargs
        return self

    def __getattr__(self, name, *args, **kwargs):
        #print(f"name {name}, args {args}, kwargs {kwargs}")
        return HypsterPrepare(name, self, *args, **kwargs)

# Cell
def prepare(call):
    @functools.wraps(call)
    def wrapper_decorator(*args, **kwargs):
        #print(f"args: {args}")
        #print(f"kwargs: {kwargs}")
        all_args = list(args) + list(kwargs.values())
        if any([contains_hypster(arg, HYPSTER_TYPES) for arg in all_args]):
            return HypsterPrepare(call, None, *args, **kwargs)
        else:
            return call(*args, **kwargs)
    return wrapper_decorator

# Cell
import optuna

# Cell
def run_func_test(x, n_trials=5):
    def objective(trial):
        y = x.sample(trial)
        print(y)
        return 1.0

    optuna.logging.set_verbosity(0)
    pruner = optuna.pruners.NopPruner()
    study = optuna.create_study(direction="maximize", pruner=pruner)
    study.optimize(objective, n_trials=n_trials, timeout=600)