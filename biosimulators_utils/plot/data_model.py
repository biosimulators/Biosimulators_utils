""" Data model for plots

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum


__all__ = ['PlotFormat']


class PlotFormat(str, enum.Enum):
    """ Format of a report """
    jpg = 'jpg'
    pdf = 'pdf'
    png = 'png'
    svg = 'svg'
