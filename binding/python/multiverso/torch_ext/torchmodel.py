#!/usr/bin/env python
# coding:utf8

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.autograd import Variable

import numpy as np
import multiverso as mv


class MVTorchModel(object):
    def __init__(self, tmobj):
        assert(isinstance(tmobj, nn.Module))
        self._tmobj = tmobj
        self._mv_params=[]
        for param in self._tmobj.parameters():
            self._mv_params.append(mv.ArrayTableHandler(param.data.numpy().size, param.data.numpy().reshape((-1,))))
        mv.barrier()
        self._last_mv_params=[]
        for mv_param in self._mv_params:
            self._last_mv_params.append(mv_param.get())
        for param, last_mv_param in zip(self._tmobj.parameters(), self._last_mv_params):
            param.data=torch.from_numpy(last_mv_param.reshape(param.data.numpy().shape))

    def mv_sync(self, lr=0.1, mom=0.0, rho=0.0, lam=0.0):
        for mv_param, last_mv_param, param in zip(self._mv_params, self._last_mv_params, self._tmobj.parameters()):
            mv_param.add(last_mv_param - param.data.numpy().reshape((-1,)), lr=lr, mom=mom, rho=rho, lam=lam)

        for i, (mv_param, last_mv_param, param) in enumerate(zip(self._mv_params, self._last_mv_params, self._tmobj.parameters())):
            self._last_mv_params[i]=mv_param.get()
            param.data=torch.from_numpy(self._last_mv_params[i].reshape(param.data.numpy().shape))

    def __call__(self, *args, **kwargs):
        return self._tmobj(*args, **kwargs)

    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict['_mv_params']
        return odict

    def __getattribute__(self, attr):
        if attr in ['_tmobj', '_mv_params', '_last_mv_params']:
            return object.__getattribute__(self, attr)
        elif attr in ['mv_sync', '__call__','__getstate__']:
            return getattr(MVTorchModel, attr).__get__(self)
        else:
            return getattr(self._tmobj, attr)
