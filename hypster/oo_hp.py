# AUTOGENERATED! DO NOT EDIT! File to edit: 02_oo_hp.ipynb (unless otherwise specified).

__all__ = ['SEED', 'auto_assign', 'HypsterBase', 'HpExpression', 'HYPSTER_TYPES', 'SubExpression', 'AddExpression',
           'MulExpression', 'DivExpression', 'PowExpression', 'HpInt', 'HpFloat', 'HpFunc', 'HpCategorical',
           'HpVarLenList', 'list_to_tuple', 'populate_iterable', 'populate_dict', 'HpList', 'HpTuple', 'HpDict',
           'HpBool', 'HpToggle', 'DATA_STRUCTURES', 'contains_hypster', 'sample_hp', 'run_hp_test']

# Cell
import fastai2
from fastai2.tabular.all import *
from fastai2.metrics import *

# Cell
from copy import deepcopy

# Cell
import optuna

# Cell
SEED = 42

# Cell
from collections.abc import Iterable

# Cell
from inspect import signature, Parameter
import functools

def auto_assign(func):
    # Signature:
    sig = signature(func)
    for name, param in sig.parameters.items():
        if param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
            raise RuntimeError('Unable to auto assign if *args or **kwargs in signature.')
    # Wrapper:
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        for i, (name, param) in enumerate(sig.parameters.items()):
            # Skip 'self' param:
            if i == 0: continue
            # Search value in args, kwargs or defaults:
            if i - 1 < len(args):
                val = args[i - 1]
            elif name in kwargs:
                val = kwargs[name]
            else:
                val = param.default
            setattr(self, name, val)
        func(self, *args, **kwargs)
    return wrapper

# Cell
class HypsterBase(object):
    def __init__(self): return
#TODO: add stuff here

# Cell
class HpExpression(object):
    def __init__(self, exp1, exp2):
        self.exp1 = exp1; self.exp2 = exp2

    def sample(self, trial): raise NotImplementedError

    def get_name(self):
        if self.name is not None: return self.name

        name = ""
        if self.exp1 is not None and isinstance(self.exp1, HpExpression) and hasattr(self.exp1, "name"):
            name += self.exp1.name
        if self.exp2 is not None and isinstance(self.exp2, HpExpression) and hasattr(self.exp2, "name"):
            if len(name) > 0:
                name +=  "_"
            name += self.exp2.name
        self.name = name
        return self.name
        #TODO: refactor

    def __add__(self, other):  return AddExpression(self, other)
    def __radd__(self, other): return AddExpression(other, self)
    def __sub__(self, other):  return SubExpression(self, other)
    def __rsub__(self, other): return SubExpression(other, self)
    def __mul__(self, other):  return MulExpression(self, other)
    def __rmul__(self, other): return MulExpression(other, self)
    def __div__(self, other):  return DivExpression(self, other)
    def __rdiv__(self, other): return DivExpression(other, self)
    def __pow__(self, other):  return PowExpression(self, other)
    def __rpow__(self, other): return PowExpression(other, self)

# Cell
HYPSTER_TYPES = (HypsterBase, HpExpression)

# Cell
class SubExpression(HpExpression):
    def sample(self, trial):
        exp1 = sample_hp(self.exp1, trial)
        exp2 = sample_hp(self.exp2, trial)
        return exp1 - exp2

# Cell
class AddExpression(HpExpression):
    def sample(self, trial):
        exp1 = sample_hp(self.exp1, trial)
        exp2 = sample_hp(self.exp2, trial)
        return exp1 + exp2

# Cell
class MulExpression(HpExpression):
    def sample(self, trial):
        exp1 = sample_hp(self.exp1, trial)
        exp2 = sample_hp(self.exp2, trial)
        return exp1 * exp2

# Cell
class DivExpression(HpExpression):
    def sample(self, trial):
        exp1 = sample_hp(self.exp1, trial)
        exp2 = sample_hp(self.exp2, trial)
        return exp1 / exp2

# Cell
class PowExpression(HpExpression):
    def sample(self, trial):
        exp1 = sample_hp(self.exp1, trial)
        exp2 = sample_hp(self.exp2, trial)
        return exp1 ** exp2

# Cell
class HpInt(HpExpression):
    @auto_assign
    def __init__(self, name, low, high, step=1): pass

    def sample(self, trial):
        return trial.suggest_int(self.name, self.low, self.high, self.step)

# Cell
class HpFloat(HpExpression):
    @auto_assign
    def __init__(self, name, low, high, log=False, step=None): pass
        #self.result = None
        #TODO: check what's up with log and step
        #TODO: move result to HpExpression?

    def sample(self, trial):
        return trial.suggest_float(self.name, self.low, self.high)

    #TODO: warn if log=True & step is not None
    #TODO: check what is the "*" in the function definition

# Cell
def _log_optuna_param(param_name, result, trial):
    trial.set_user_attr(param_name, result)

# Cell
class HpFunc(HpExpression):
    def __init__(self, name, func, **kwargs):
        self.name = name
        self.func = func
        self.kwargs = kwargs

    def sample(self, trial):
        result = self.func(trial, **self.kwargs)
        _log_optuna_param(self.name, result, trial)
        return result

# Cell
class HpCategorical(HpExpression):
    @auto_assign
    def __init__(self, name, choices): pass

    def sample(self, trial):
        choices           = self.choices
        name              = self.name
        optuna_valid_cats = [str, int, float, bool, NoneType] #TODO: add more + move to global area

        if any([type(choice) not in optuna_valid_cats for choice in self.choices]):
            #TODO: add check for "choice.__name__"
            self.items_str = [choice.__name__ for choice in choices]
            self.str_dict  = dict(zip(self.items_str, choices))
            chosen_hp      = trial.suggest_categorical(name, self.str_dict)
            result         = self.str_dict[chosen_hp]
        else:
            result = trial.suggest_categorical(name, choices)
        return result

# Cell
class HpVarLenList(HpExpression):
    #TODO: think of a better name?
    @auto_assign
    def __init__(self, name, min_len, max_len, hp, same_value=False): pass
        #self.result = None

    def sample(self, trial):
        lst_len = trial.suggest_int(self.name, self.min_len, self.max_len)
        lst = []
        if (self.same_value) or (not contains_hypster(self.hp, HYPSTER_TYPES)):
            lst = [sample_hp(self.hp, trial)] * lst_len
        else:
            for i in range(lst_len):
                hp = deepcopy(self.hp)
                hp.result = None
                hp.name = f"{hp.get_name()}_{i+1}"
                result = sample_hp(hp, trial)
                lst.append(result)

        return lst

# Cell
def list_to_tuple(lst): return (*lst, )

# Cell
def populate_iterable(iterable, trial):
    sampled_lst = []
    for item in iterable:
        if isinstance(item, HpToggle):
            if sample_hp(item, trial):
                sampled_lst.append(sample_hp(item.hp, trial))
        else:
            sampled_lst.append(sample_hp(item, trial))
    return sampled_lst

# Cell
def populate_dict(dct, trial):
    sampled_dict = {}
    for key, value in dct.items():
        if isinstance(value, HpToggle):
            if sample_hp(value, trial):
                sampled_dict[key] = sample_hp(value.hp, trial)
        else:
            sampled_dict[key] = sample_hp(value, trial)
    return sampled_dict

# Cell
class HpList(HpExpression):
    @auto_assign
    def __init__(self, lst): pass

    def sample(self, trial):
        return populate_iterable(self.lst, trial)

# Cell
class HpTuple(HpExpression):
    @auto_assign
    def __init__(self, tup): pass

    def sample(self, trial):
        return list_to_tuple(populate_iterable(self.tup, trial))

# Cell
class HpDict(HpExpression):
    @auto_assign
    def __init__(self, dct): pass

    def sample(self, trial):
        return populate_dict(self.dct, trial)

# Cell
class HpBool(HpCategorical):
    def __init__(self, name):
        super().__init__(name, choices=[False, True])

# Cell
class HpToggle(HpBool):
    @auto_assign
    def __init__(self, name, hp): return
    def sample(self, trial): return HpBool(self.name).sample(trial)
    #automatically add name? toggle_ + hp.__name__

# Cell
DATA_STRUCTURES = (set, list, tuple, dict)

# Cell
def contains_hypster(x, types):
    if not isinstance(x, DATA_STRUCTURES):
        x = [x]
    elif isinstance(x, dict):
        x = x.values()

    for item in x:
        if isinstance(item, DATA_STRUCTURES):
            if contains_hypster(item, types):
                return True
        else:
            if isinstance(item, types):
                return True
    return False

# Cell
def sample_hp(hp, trial):
    if not contains_hypster(hp, HYPSTER_TYPES):
        return hp
    #TODO: change to dynamic dispatch
    if isinstance(hp, list):
        hp = HpList(hp)
    elif isinstance(hp, tuple):
        hp = HpTuple(hp)
    elif isinstance(hp, dict):
        hp = HpDict(hp)
    return hp.sample(trial)
#TODO: handle list of lists
#TODO!: check if class attributes / methods? have hypster in them

# Cell
def run_hp_test(hp):
    def objective(trial):
        print(sample_hp(hp, trial))
        return 1.0

    optuna.logging.set_verbosity(0)
    pruner = optuna.pruners.NopPruner()
    study = optuna.create_study(direction="maximize", pruner=pruner)
    study.optimize(objective, n_trials=5, timeout=600)