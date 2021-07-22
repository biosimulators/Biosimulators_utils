""" Utilities for working with Vega

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-22
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

__all__ = ['dict_to_vega_dataset']


def dict_to_vega_dataset(data_dict):
    """ Convert a dictionary of values, such as that produced by COBRApy, into a Vega
    dataset (array of data elements)

    Args:
        data_dict (:obj:`dict`): dictionary that maps the labels of predicted variables
            to their predicted values

    Returns:
        :obj:`list`: list of data elements, each with two keys ``label`` and `values`` whose values
            are the labels of each variable and an array of their predicted values
    """
    data_set = []
    for id, val in data_dict.items():
        data_set.append({
            'label': id,
            'values': val if isinstance(val, list) else [val]
        })
    return data_set
