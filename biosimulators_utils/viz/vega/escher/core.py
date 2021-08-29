""" Utility for converting metabolic maps from Escher to Vega format

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-02-06
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...utils import cubic_bezier_point, cubic_bezier_angle
import bezier
import copy
import json
import math
import numpy
import os
import pkg_resources

__all__ = ['escher_to_vega', 'read_escher_map_config']


def escher_to_vega(reaction_fluxes_data_set, escher_filename, vega_filename,
                   max_width_height=800, legend_padding=20, legend_width=40, signal_height=20,
                   arrow_head_gap=16., indent=2, metabolic_map_data_file=None):
    """ Convert a metabolic pathway map from Escher format to Vega format.

    Args:
        reaction_fluxes_data_set (:obj:`dict`): Vega data set with each predicted reaction flux. The dictionary should
            have one of the following schemas

            * Contain a key ``values`` whose value is a list of the predicted flux values. Each predicted flux value
              should be a dictionary with two keys

                * ``label``: value should be the BiGG identifier of the corresponding reaction
                * ``values``: array with a single value equal to the predicted flux

            * Contain a key ``url`` whose value is a URL where the predicted flux values can be retrieved in JSON
              format. The data should be in the same format outlined above.
            * Contain a key ``sedmlUri`` whose value is an array which contains two elements that indicate

                * The location of the SED-ML file (within its parent COMBINE/OMEX archive) which will produce
                  the flux predictions for the visualization
                * The id of the SED-ML report which will contain the flux predictions for the visualization

        escher_filename (:obj:`str`): path to the visualization in Escher format
        vega_filename (:obj:`str`): path to save the visualization in Vega format
        max_width_height (:obj:`int`, optional): maximum height/width of the metabolic map in pixels
        legend_padding (:obj:`int`, optional): horizontal spacing between the metabolic map and legend in pixels
        legend_width (:obj:`int`, optional): legend width in pixels, including the width of the title
        signal_height (:obj:`int`, optional): height of signals in pixels
        arrow_head_gap (:obj:`float`, optional): spacing between arrow heads and nodes
        indent (:obj:`int` or :obj:`None`, optional): indentation
        metabolic_map_data_file (:obj:`dict` or :obj:`None`, optional): If :obj:`None`, store the data for
            the metabolic map (e.g., coordinates of metabolites, reactions) inline within the generated Vega
            file. If not :obj:`None`, store the data for the metabolic map in a separate file to be loaded
            via a URL. In this case, the argument must be a dictionary which two keys, ``filename`` and ``url``
            which indicate where the data should be saved and where this file will be hosted.
    """
    # read the Escher version of the map
    escher = read_escher_map_config(escher_filename)

    # determine the extent (min/max x/y) of the map
    min_x = math.inf
    min_y = math.inf
    max_x = -math.inf
    max_y = -math.inf

    nodes = escher[1]['nodes']
    for node in nodes.values():
        min_x = min(min_x, node['x'])
        min_y = min(min_y, node['y'])
        max_x = max(max_x, node['x'])
        max_y = max(max_y, node['y'])

        if 'label_x' in node:
            min_x = min(min_x, node['label_x'])
            min_y = min(min_y, node['label_y'])
            max_x = max(max_x, node['label_x'])
            max_y = max(max_y, node['label_y'])

    for reaction in escher[1]['reactions'].values():
        if 'label_x' in reaction:
            min_x = min(min_x, reaction['label_x'])
            min_y = min(min_y, reaction['label_y'])
            max_x = max(max_x, reaction['label_x'])
            max_y = max(max_y, reaction['label_y'])

    escher_width = max_x - min_x
    escher_height = max_y - min_y

    if escher_width > escher_height:
        width = max_width_height
        coordinate_scale = width / escher_width
        height = escher_height * coordinate_scale
    else:
        height = max_width_height
        coordinate_scale = height / escher_height
        width = escher_width * coordinate_scale

    # convert metabolite circle nodes to Vega
    metabolites = []
    for id, node in nodes.items():
        if node["node_type"] == "metabolite":
            metabolite = {}

            metabolite["id"] = id
            metabolite["biggId"] = node['bigg_id']
            metabolite["name"] = node['name']

            metabolite["x"] = (node["x"] - min_x) * coordinate_scale
            metabolite["y"] = (node["y"] - min_y) * coordinate_scale

            if node.get('node_is_primary', False):
                metabolite['size'] = 10 ** 2 * coordinate_scale
            else:
                metabolite['size'] = 20 ** 2 * coordinate_scale

            if "label_x" in node:
                metabolite["labelX"] = (node["label_x"] - min_x) * coordinate_scale
                metabolite["labelY"] = (node["label_y"] - min_y) * coordinate_scale

            reaction_ids = set()
            for rxn_id, reaction in escher[1]['reactions'].items():
                for segment in reaction["segments"].values():
                    if segment["from_node_id"] == id or segment["to_node_id"] == id:
                        reaction_ids.add(rxn_id)
                        break
            metabolite['reactionIds'] = list(reaction_ids)
            metabolite['metaboliteIds'] = []

            related_metabolite_ids = set()
            for reaction_id in reaction_ids:
                reaction = escher[1]['reactions'][reaction_id]

                for segment in reaction["segments"].values():
                    from_node = nodes[segment["from_node_id"]]
                    to_node = nodes[segment["to_node_id"]]

                    if from_node["node_type"] == "metabolite":
                        related_metabolite_ids.add(segment["from_node_id"])
                    if to_node['node_type'] == 'metabolite':
                        related_metabolite_ids.add(segment["to_node_id"])
            metabolite['relatedMetaboliteIds'] = list(related_metabolite_ids)

            metabolites.append(metabolite)

    # convert reaction paths to Vega
    reaction_segment_coordinates = []
    reaction_arrow_head_coordinates = []
    reaction_labels = []
    for id, reaction in escher[1]['reactions'].items():
        metabolite_ids = set()
        for rxn_id, other_reaction in escher[1]['reactions'].items():
            if other_reaction['bigg_id'] == reaction['bigg_id']:
                for segment in reaction["segments"].values():
                    from_node = nodes[segment["from_node_id"]]
                    to_node = nodes[segment["to_node_id"]]

                    if from_node["node_type"] == "metabolite":
                        metabolite_ids.add(segment["from_node_id"])
                    if to_node['node_type'] == 'metabolite':
                        metabolite_ids.add(segment["to_node_id"])
        metabolite_ids = list(metabolite_ids)

        reaction_labels.append({
            "id": id,
            "biggId": reaction["bigg_id"],
            "x": (reaction["label_x"] - min_x) * coordinate_scale,
            "y": (reaction["label_y"] - min_y) * coordinate_scale,
            'reactionIds': [],
            'metaboliteIds': metabolite_ids,
            'relatedMetaboliteIds': [],
        })

        for segment in reaction["segments"].values():
            from_node = nodes[segment["from_node_id"]]
            to_node = nodes[segment["to_node_id"]]

            if from_node['node_type'] == 'metabolite':
                if segment['b1']:
                    points = [
                        [from_node['x'], from_node['y']],
                        [segment['b1']['x'], segment['b1']['y']],
                        [segment['b2']['x'], segment['b2']['y']],
                        [to_node['x'], to_node['y']],
                    ]
                    segment_len = bezier.Curve(numpy.array(points).transpose(), degree=3).length
                    t = min(1., arrow_head_gap / segment_len)
                    x0, y0 = cubic_bezier_point(points, t)
                    angle = cubic_bezier_angle(points, t) - 90.
                else:
                    segment_len = math.sqrt((from_node['x'] - to_node['x']) ** 2 + (from_node['y'] - to_node['y']) ** 2)
                    angle = math.atan2(from_node['y'] - to_node['y'], from_node['x'] - to_node['x'])
                    t = min(1., arrow_head_gap / segment_len)
                    x0 = from_node["x"] * (1 - t) + to_node["x"] * t
                    y0 = from_node["y"] * (1 - t) + to_node["y"] * t

                reaction_arrow_head_coordinates.append({
                    'id': id,
                    'biggId': reaction['bigg_id'],
                    'start': True,
                    'x': (x0 - min_x) * coordinate_scale,
                    'y': (y0 - min_y) * coordinate_scale,
                    'angle': angle,
                    'reactionIds': [],
                    'metaboliteIds': metabolite_ids,
                    'relatedMetaboliteIds': [],
                })
            else:
                x0 = from_node["x"]
                y0 = from_node["y"]

            if to_node['node_type'] == 'metabolite':
                if segment['b1']:
                    points = [
                        [from_node['x'], from_node['y']],
                        [segment['b1']['x'], segment['b1']['y']],
                        [segment['b2']['x'], segment['b2']['y']],
                        [to_node['x'], to_node['y']],
                    ]
                    segment_len = bezier.Curve(numpy.array(points).transpose(), degree=3).length
                    t = max(0., 1. - arrow_head_gap / segment_len)
                    x3, y3 = cubic_bezier_point(points, t)
                    angle = cubic_bezier_angle(points, t) + 90.
                else:
                    segment_len = math.sqrt((from_node['x'] - to_node['x']) ** 2 + (from_node['y'] - to_node['y']) ** 2)
                    angle = math.atan2(to_node['y'] - from_node['y'], to_node['x'] - from_node['x'])
                    t = max(0., 1. - arrow_head_gap / segment_len)
                    x3 = from_node["x"] * (1 - t) + to_node["x"] * t
                    y3 = from_node["y"] * (1 - t) + to_node["y"] * t

                reaction_arrow_head_coordinates.append({
                    'id': id,
                    'biggId': reaction['bigg_id'],
                    'start': False,
                    'x': (x3 - min_x) * coordinate_scale,
                    'y': (y3 - min_y) * coordinate_scale,
                    'angle': angle,
                    'reactionIds': [],
                    'metaboliteIds': metabolite_ids,
                    'relatedMetaboliteIds': [],
                })
            else:
                x3 = to_node["x"]
                y3 = to_node["y"]

            if segment["b1"]:
                reaction_segment_coordinates.append({
                    "id": id,
                    "biggId": reaction["bigg_id"],
                    "name": reaction["name"],
                    'type': 'curve',
                    'x0': (x0 - min_x) * coordinate_scale,
                    'y0': (y0 - min_y) * coordinate_scale,
                    'x1': (segment["b1"]["x"] - min_x) * coordinate_scale,
                    'y1': (segment["b1"]["y"] - min_y) * coordinate_scale,
                    'x2': (segment["b2"]["x"] - min_x) * coordinate_scale,
                    'y2': (segment["b2"]["y"] - min_y) * coordinate_scale,
                    'x3': (x3 - min_x) * coordinate_scale,
                    'y3': (y3 - min_y) * coordinate_scale,
                    'reactionIds': [],
                    'metaboliteIds': metabolite_ids,
                    'relatedMetaboliteIds': [],
                })
            else:
                reaction_segment_coordinates.append({
                    "id": id,
                    "biggId": reaction["bigg_id"],
                    "name": reaction["name"],
                    'type': 'line',
                    'x0': (x0 - min_x) * coordinate_scale,
                    'y0': (y0 - min_y) * coordinate_scale,
                    'x1': (x3 - min_x) * coordinate_scale,
                    'y1': (y3 - min_y) * coordinate_scale,
                    'reactionIds': [],
                    'metaboliteIds': metabolite_ids,
                    'relatedMetaboliteIds': [],
                })

    # insert metabolite circles and reaction paths into Vega template
    template_filename = pkg_resources.resource_filename(
        'biosimulators_utils',
        os.path.join('viz', 'vega', 'escher', 'template.json'))
    with open(template_filename, 'r') as file:
        vega = json.load(file)

    vega['width'] = width + legend_padding + legend_width
    vega['height'] = height + signal_height

    map_width_signal = next(signal for signal in vega['signals'] if signal['name'] == 'mapMaxX')
    map_width_signal['value'] = width

    map_height_signal = next(signal for signal in vega['signals'] if signal['name'] == 'mapMaxY')
    map_height_signal['value'] = height

    legend_width_signal = next(signal for signal in vega['signals'] if signal['name'] == 'legendWidth')
    legend_width_signal['value'] = legend_width

    legend_padding_signal = next(signal for signal in vega['signals'] if signal['name'] == 'legendPadding')
    legend_padding_signal['value'] = legend_padding

    signal_height_signal = next(signal for signal in vega['signals'] if signal['name'] == 'signalHeight')
    signal_height_signal['value'] = signal_height

    signal_padding_signal = next(signal for signal in vega['signals'] if signal['name'] == 'signalPadding')
    signal_padding_signal['value'] = 0

    metabolite_stroke_width_signal = next(signal for signal in vega['signals'] if signal['name'] == 'metaboliteStrokeWidthData')
    metabolite_stroke_width_signal['value'] = 2 * coordinate_scale

    reaction_stroke_width_signal = next(signal for signal in vega['signals'] if signal['name'] == 'reactionStrokeWidthData')
    reaction_stroke_width_signal['value'] = 18 * coordinate_scale

    arrow_head_stroke_width_signal = next(signal for signal in vega['signals'] if signal['name'] == 'arrowHeadStrokeWidthData')
    arrow_head_stroke_width_signal['value'] = 1 * coordinate_scale

    metabolic_map_data = {
        "metabolites": metabolites,
        "reactionSegmentCoordinates": reaction_segment_coordinates,
        "reactionArrowHeadCoordinates": reaction_arrow_head_coordinates,
        "reactionLabels": reaction_labels,
    }
    if metabolic_map_data_file:
        with open(metabolic_map_data_file['filename'], 'w') as file:
            json.dump(metabolic_map_data, file, indent=indent)

        for key in metabolic_map_data.keys():
            vega_data_set = next(data for data in vega['data'] if data['name'] == key)
            del vega_data_set['values']
            vega_data_set['url'] = metabolic_map_data_file['url']
            vega_data_set['format'] = {
                'type': 'json',
                'property': key
            }
    else:
        for key, values in metabolic_map_data.items():
            vega_data_set = next(data for data in vega['data'] if data['name'] == key)
            vega_data_set['values'] = values

    i_reaction_fluxes_data_set = next(i_data for i_data, data in enumerate(vega['data']) if data['name'] == 'reactionFluxes')
    vega['data'][i_reaction_fluxes_data_set] = copy.copy(reaction_fluxes_data_set)
    vega['data'][i_reaction_fluxes_data_set]['name'] = 'reactionFluxes'

    # save Vega-formatted map
    with open(vega_filename, 'w') as file:
        json.dump(vega, file, indent=indent)


def read_escher_map_config(filename):
    """ Read the configuration of an Escher map from a file

    Args:
        filename (:obj:`str`): path to a configuration of an Escher map

    Returns:
        :obj:`list`: configuration of an Escher map
    """
    with open(filename, 'r') as file:
        return json.load(file)
