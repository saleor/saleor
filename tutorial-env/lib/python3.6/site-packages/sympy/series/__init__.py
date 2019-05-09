"""A module that handles series: find a limit, order the series etc.
"""
from .order import Order
from .limits import limit, Limit
from .gruntz import gruntz
from .series import series
from .approximants import approximants
from .residues import residue
from .sequences import (EmptySequence, SeqPer, SeqFormula, sequence, SeqAdd,
                        SeqMul)
from .fourier import fourier_series
from .formal import fps
from .limitseq import difference_delta, limit_seq

O = Order

__all__ = ['Order', 'O', 'limit', 'Limit', 'gruntz', 'series', 'residue',
           'EmptySequence', 'SeqPer', 'SeqFormula', 'sequence',
           'SeqAdd', 'SeqMul', 'fourier_series', 'fps', 'difference_delta',
           'limit_seq']
