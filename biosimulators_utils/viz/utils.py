""" Utilities for visualizations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-22
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import math

__all__ = ['cubic_bezier_point', 'cubic_bezier_angle']


def cubic_bezier_point(points, t):
    """ Get the coordinate of a point along a cubic bezier curve

    Args:
        points (:obj:`list` of :obj:`list` of :obj:`float`): control points
        t (:obj:`float`): position along the curve [0, 1]

    Returns:
        :obj:`tuple` of :obj:`float`: position of the curve at point :obj:`t`
    """
    return (
        (
            ((1. - t) ** 3.) * points[0][0]
            + 3. * t * ((1. - t) ** 2.) * points[1][0]
            + (3. * t ** 2.) * (1. - t) * points[2][0]
            + (t ** 3.) * points[3][0]
        ),
        (
            ((1. - t) ** 3.) * points[0][1]
            + 3. * t * ((1. - t) ** 2.) * points[1][1]
            + 3. * (t ** 2.) * (1. - t) * points[2][1]
            + (t ** 3.) * points[3][1]
        ),
    )


def cubic_bezier_angle(points, t):
    """ Get the angle of a point along a cubic bezier curve

    Args:
        points (:obj:`list` of :obj:`list` of :obj:`float`): control points
        t (:obj:`float`): position along the curve [0, 1]

    Returns:
        :obj:`float`: angle of the curve at point :obj:`t`
    """
    dx = (
        (1 - t) ** 2 * (points[1][0] - points[0][0])
        + 2 * t * (1 - t) * (points[2][0] - points[1][0])
        + t ** 2 * (points[3][0] - points[2][0])
    )
    dy = (
        (1 - t) ** 2 * (points[1][1] - points[0][1])
        + 2 * t * (1 - t) * (points[2][1] - points[1][1])
        + t ** 2 * (points[3][1] - points[2][1])
    )
    return math.atan2(dy, dx) * 180 / math.pi
