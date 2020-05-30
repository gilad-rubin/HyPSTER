# AUTOGENERATED! DO NOT EDIT! File to edit: 04_tabular_api.ipynb (unless otherwise specified).

__all__ = ['SEED', 'path', 'df', 'df', 'cat_names', 'cont_names', 'dep_var', 'Normalize', 'norm', 'procs', 'to', 'dls',
           'cbs', 'start_mom', 'tabular_learner', 'learner', 'run_learner', 'study']

# Cell
from .oo_hp import *
from .hypster_prepare import *

import fastai2
from fastai2.tabular.all import *
from fastai2.metrics import *

from sklearn.model_selection import train_test_split

from copy import deepcopy

import optuna

# Cell
SEED = 42

# Cell
path = untar_data(URLs.ADULT_SAMPLE)
path.ls()

# Cell
df = pd.read_csv(path/'adult.csv')
df.head()

# Cell
df = df.sample(frac=0.1)

# Cell
cat_names = ['workclass', 'education', 'marital-status', 'occupation', 'relationship', 'race']
cont_names = ['age', 'fnlwgt', 'education-num']
dep_var = "salary"

# Cell
train_df, test_df = train_test_split(df, test_size=0.6,
                                     random_state=SEED,
                                     stratify=df[dep_var])

# Cell
Normalize = prepare(Normalize)
norm = Normalize(mean=HpFloat("mean_norm", 0.001, 10.4))

# Cell
procs = [Categorify, imp, HpToggle("norm_bool", norm)]

# Cell
to = TabularPandas(train_df,
                   y_block = CategoryBlock(),
                   y_names = dep_var,
                   splits = RandomSplitter()(range_of(train_df)),
                   cat_names = cat_names,
                   cont_names = cont_names,
                   procs = procs,
                   reduce_memory=False,
                   inplace=False
                  )

# Cell
#dls = to.dataloaders(batch_size=2 ** HpInt("batch_size", 5, 9))
#dls = to.dataloaders(batch_size=HpInt("batch_size", 16, 128, 16))

# Cell
dls = to.dataloaders(batch_size=32)

# Cell
cbs = [TrackerCallback(monitor="roc_auc_score"),
       ReduceLROnPlateau("roc_auc_score", patience=3)]

# Cell
start_mom = HpFloat("start_mom", 0.85, 0.99)

# Cell
tabular_learner = prepare(tabular_learner)

# Cell
learner = tabular_learner(dls,
                          metrics=RocAuc(),
                          opt_func=HpCategorical("optimizer", [Adam, SGD, QHAdam]),
                          layers=HpVarLenList("layers", 1, 4, HpInt("layer_size", 50, 300, 50), same_value=False),
                          cbs=cbs,
                          moms=(start_mom, start_mom-0.1, start_mom),
                          wd_bn_bias=HpBool("wd_bn_bias"),
                          )

# Cell
def run_learner(fit_method, get_metric, n_trials=5): #learner
    class Objective():
        def __init__(self, fit_method, get_metric): #learner
            #self.learner   = learner
            self.fit_method = fit_method
            self.get_metric = get_metric

        def __call__(self, trial):
            #learner = self.learner.sample(trial)
            self.fit_method.sample(trial)
            res = self.get_metric.sample(trial)
            #print(self.fit_method.base_call)
            #print(self.get_metric.base_call.base_call)
            print(res)
            return res

    objective = Objective(fit_method, get_metric) #learner
    optuna.logging.set_verbosity(0)
    pruner = optuna.pruners.NopPruner()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    study = optuna.create_study(direction="maximize", study_name = now, pruner=pruner)
    study.optimize(objective, n_trials=n_trials, n_jobs=1, timeout=600)
    return study

# Cell
study = run_learner(#learner    = learner,
                    fit_method = learner.fit_one_cycle(2, lr),
                    get_metric = learner.tracker.best,
                    n_trials   = 5
                   )

# Cell
print("Number of finished trials: {}".format(len(study.trials)))

# Cell
study.trials_dataframe()