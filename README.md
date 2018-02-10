# pyrunner

Run python code in a separate process made easy. Useful when you need function call from conflicting library or recycle resource  dynamically.

I my case, I need model results from Pytorch and Tensorflow, which are using conflicting version of cuDNN. I would also like to dynamically aquire and release GPU.

Some sample could be as follows:

First, prepare the codes to be run in processes as classes.
```python
class TFModel(object):
    def __init__(self, gpu='0'):
        import tensorflow
        ...
        self.model = ...
        ...
    
    def __call__(self, data):
        ...
        pred = self.model.predict(data)
        ...
        return pred
        
class PTModel(object):
    def __init__(self, model_path):
        import torch
        ...
        self.model = ...
        ...
    
    def __call__(self, data):
        ...
        pred = self.model.predict(data)
        ...
        return pred
```

Second, prepare them in `runner`.
Parameters are redirected to the corresponding constructor `__init__()` in specified class.
```python
from runner import RunnerProcess
tfmodel = RunnerProcess(TFModel, gpu='0')
ptmodel = RunnerProcess(PTModel, model_path='path/to/saved/torch/model')
...
```

Third, actually invoke them somewhere.
Parameters are redirected to the corresponding magic method `__call__()` in specified class.
```python
...
tfresult = tfmodel(data)
ptresult = ptmodel(data)
...
tfresult = tfmodel(data2)
ptresult = ptmodel(data2)
...
```

Finally, manually destory them to end the process or wait for the GC.
```python
del tfmodel
del ptmodel
```

I am quite new to python multiprocessing module.
The implementation is trival.
Happy hacking.
