""" Utility for converting activity flow diagrams from GINsim Markup Language (GINML) to Vega format

:Author: Andrew Freiburger <afreiburger@uvic.ca>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-23
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import copy
import json
import math
import os
import pkg_resources
import xml.etree.ElementTree as et

__all__ = ['ginml_to_vega']


def ginml_to_vega(node_values_data_set, ginml_filename, vega_filename,
                  optimum_nodes_quantity=18,
                  edge_x_value_adjustment=0,
                  edge_y_value_adjustment=45,
                  signal_height=65,
                  signal_padding=10,
                  indent=2):
    """ Convert an activity flow diagram from GINsim Markup Language (GINML) format to Vega format.

    Args:
        node_values_data_set (:obj:`dict`): Vega data set with the predicted values of each node. The dictionary should
            have one of the following schemas

            * Contain a key ``values`` whose value is a list of the predicted node values. Each item of the list
              should be a dictionary with two keys

                * ``label``: value should be the SBML-qual identifier of the corresponding node
                * ``values``: array of the predicted value of the species at each time step

            * Contain a key ``url`` whose value is a URL where the predicted values can be retrieved in JSON
              format. The data should be in the same format outlined above.
            * Contain a key ``sedmlUri`` whose value is an array which contains two elements that indicate

                * The location of the SED-ML file (within its parent COMBINE/OMEX archive) which will produce
                  the predictions for the visualization
                * The id of the SED-ML report which will contain the predictions for the visualization

        ginml_filename (:obj:`str`): path to the visualization in GINML format
        vega_filename (:obj:`str`): path to save the visualization in Vega format
        optimum_nodes_quantity (:obj:`int`)
        edge_x_value_adjustment (:obj:`int`)
        edge_y_value_adjustment (:obj:`int`)
        signal_height (:obj:`int`)
        signal_padding (:obj:`int`)
        indent (:obj:`int` or :obj:`None`, optional): indentation
    """

    # parse the diagram from the GINML file
    with open(ginml_filename, 'r') as file:
        tree = et.parse(file)
    root = tree.getroot()
    graph = root[0]

    nodes = []
    regulations = {}
    for child in graph:
        if child.tag == 'node':
            try:
                comment = child.find('annotation/comment').text
            except AttributeError:
                comment = None

            node_coordinates = child.find('nodevisualsetting/ellipse')
            if node_coordinates is None:
                node_coordinates = child.find('nodevisualsetting/rect')

            y_coordinate = node_coordinates.attrib['y']
            x_coordinate = node_coordinates.attrib['x']
            node_width = node_coordinates.attrib['width']
            node_height = node_coordinates.attrib['height']
            node_fill_color = node_coordinates.attrib['backgroundColor']
            text_color = node_coordinates.attrib['foregroundColor']
            nodes.append({
                'id': child.attrib['id'],
                'name': child.attrib.get('name', child.attrib['id']),
                'x_value': x_coordinate,
                'y_value': y_coordinate,
                'node_width': node_width,
                'node_height': node_height,
                'text_color': text_color,
                'fill_color': node_fill_color,
                'comment': comment
            })

        elif child.tag == 'edge':
            line_points = child.find('edgevisualsetting/polyline')
            edge_color = line_points.attrib['line_color']
            edge_width = line_points.attrib['line_width']
            coordinates = line_points.attrib['points']
            regulations[child.attrib['id']] = {
                'from_node': child.attrib['from'],
                'to_node': child.attrib['to'],
                'sign': child.attrib['sign'],
                'line_points': coordinates,
                'line_color': edge_color,
                'line_width': edge_width
            }

    # the associated nodes for each node are identified and stored
    self_loops = []
    for regulation, value in regulations.items():
        first_node, second_node = regulation.split(':', 1)
        value['associated_nodes'] = [first_node, second_node]
        if first_node == second_node:
            self_loops.append(regulation)

    # determine and parameterize the map coordinates
    min_x = math.inf
    min_y = math.inf
    max_x = -math.inf
    max_y = -math.inf
    for node in nodes:
        min_x = min(min_x, float(node['x_value']))
        max_x = max(max_x, float(node['x_value']))
        min_y = min(min_y, float(node['y_value']))
        max_y = max(max_y, float(node['y_value']))

    ginsim_width = max_x - min_x
    ginsim_height = max_y - min_y

    quantity_nodes = len(nodes)
    # print('Quantity of nodes', quantity_nodes)
    nodes_per_map_scale = (quantity_nodes / optimum_nodes_quantity) ** 0.55
    max_width_height = 700 * nodes_per_map_scale

    if ginsim_width > ginsim_height:
        width = max_width_height
        coordinate_scale = float(width / ginsim_width)
        height = ginsim_height * coordinate_scale
    else:
        height = max_width_height
        coordinate_scale = float(height / ginsim_height)
        width = ginsim_width * coordinate_scale

    width += 160
    height += 50

    # if width > height:
    #     print('Maximum figure dimension', width)
    # else:
    #     print('Maximum figure dimension', height)

    # convert the map nodes to Vega
    net_x_adjustment = - min_x + edge_x_value_adjustment
    net_y_adjustment = - min_y + edge_y_value_adjustment

    node_width_sum = []
    node_height_sum = []
    node_labels = []
    for node in nodes:
        adjusted_x_node = (float(node['x_value']) + net_x_adjustment) * coordinate_scale
        adjusted_y_node = (float(node['y_value']) + net_y_adjustment) * coordinate_scale
        node["node_height"] = float(node["node_height"]) * coordinate_scale
        node["node_width"] = float(node["node_width"]) * coordinate_scale
        node["x_value"] = adjusted_x_node
        node["y_value"] = adjusted_y_node

        node_labels.append({
            'id': node['id'],
            'name': node['name'],
            'text_color': node['text_color'],
            'x': adjusted_x_node + node["node_width"] / 2,
            'y': adjusted_y_node + node["node_height"] / 2
        })

        node_width_sum.append(node["node_width"])
        node_height_sum.append(node["node_height"])

    empirical_width_adjustment = 6 * nodes_per_map_scale ** 0.8
    empirical_height_adjustment = 5 * nodes_per_map_scale ** 0.8
    average_node_width = sum(node_width_sum) / (len(node_width_sum) * 2) + empirical_width_adjustment
    average_node_height = sum(node_height_sum) / (len(node_height_sum) * 2) + empirical_height_adjustment

    # convert regulation paths to Vega
    self_loop_label_y_offset = -33
    edges_label_y_offset = -10 * nodes_per_map_scale
    arc_y_offset = -20 + nodes_per_map_scale ** 2.7
    arc_x_offset = -10
    edge_arc_coordinates = []
    edge_line_coordinates = []
    edge_end_coordinates = []
    regulations_labels = []
    points = []

    for name, value in regulations.items():
        edge_svg_paths = []
        points = value['line_points'].split(' ')
        for point in range(len(points) - 1):
            x1, y1 = points[point].split(',')
            x1 = (float(x1) + net_x_adjustment) * coordinate_scale
            y1 = (float(y1) + net_y_adjustment) * coordinate_scale
            if name in self_loops:
                node_arc_width = 20
                node_arc_radius = 20
                edge_end_x = x1 + arc_x_offset
                edge_end_y = y1 + arc_y_offset
                edge_svg_paths.append({
                    'type': 'arc',
                    'path': "M {} {} A {} {} 0 1 1 {} {}".format(
                        edge_end_x, edge_end_y,
                        node_arc_radius, node_arc_radius,
                        edge_end_x + node_arc_width, edge_end_y,
                    ),
                    'coordinates': [
                        edge_end_x, edge_end_y,
                        node_arc_radius, node_arc_radius,
                        edge_end_x + node_arc_width, edge_end_y,
                    ]
                })
                break

            else:
                if point == 0:
                    x_value = x1
                    y_value = y1
                    cur_x = x1
                    cur_y = y1

                if point + 1 <= len(points) - 1:
                    x2, y2 = points[point + 1].split(',')
                    x2 = (float(x2) + net_x_adjustment) * coordinate_scale
                    y2 = (float(y2) + net_y_adjustment) * coordinate_scale

                    if len(points) == 3:
                        delta_x = x2 - x1
                        delta_y = y2 - y1
                    else:
                        delta_x = x2 - x_value
                        delta_y = y2 - y_value

                    if abs(delta_x) < abs(delta_y):
                        if point + 1 == len(points) - 1:
                            if delta_y < 0:
                                end_offset = (nodes_per_map_scale - 1) * (average_node_height * 0.7)
                            elif delta_y > 0:
                                end_offset = (0.6 - nodes_per_map_scale) * average_node_height * 0.7
                            cur_delta_y = delta_y + end_offset
                        else:
                            cur_delta_y = delta_y
                        edge_svg_paths.append({
                            'type': 'line',
                            'path': 'M {} {} L {} {}'.format(cur_x, cur_y, cur_x, cur_y + cur_delta_y),
                            'coordinates': [cur_x, cur_y, cur_x, cur_y + cur_delta_y],
                        })
                        cur_y += cur_delta_y

                        delta_x = 0
                        edge_end_x = x_value
                        edge_end_y = y_value = y2

                    elif abs(delta_x) > abs(delta_y):
                        if point + 1 == len(points) - 1:
                            if delta_x < 0:
                                end_offset = (nodes_per_map_scale - 1) * (average_node_width / 4)
                            elif delta_x > 0:
                                end_offset = (1 - nodes_per_map_scale) * (average_node_width / 4)
                            cur_delta_x = delta_x + end_offset
                        else:
                            cur_delta_x = delta_x
                        edge_svg_paths.append({
                            'type': 'line',
                            'path': 'M {} {} L {} {}'.format(cur_x, cur_y, cur_x + cur_delta_x, cur_y),
                            'coordinates': [cur_x, cur_y, cur_x + cur_delta_x, cur_y],
                        })
                        cur_x += cur_delta_x

                        delta_y = 0
                        edge_end_y = y_value
                        edge_end_x = x_value = x2

                    else:
                        raise ValueError('The {} edge is inconsistent with a cardinal direction.'.format(name))

                else:
                    raise ValueError('The {} contains an undefined point'.format(name))

                '''if point + 1 == len(points) - 1:
                    if delta_x == 0:
                        edge_end_x = x1
                    elif delta_y == 0:
                        edge_end_y = y1'''

        # establishing the edge ends on the figure
        if value['sign'] == 'positive':
            edge_end_shape = 'triangle'
            edge_end_angle = math.degrees(math.atan2(delta_y, delta_x))
            stroke_width = 1
        elif value['sign'] == 'negative':
            edge_end_shape = 'stroke'
            edge_end_angle = math.degrees(math.atan2(delta_y, delta_x)) + 90
            stroke_width = 5
        elif value['sign'] == 'unknown':
            edge_end_shape = 'circle'
            edge_end_angle = math.degrees(math.atan2(delta_y, delta_x))
            stroke_width = 2

        if delta_x > 0:
            edge_end_x_buffer = -average_node_width
            edge_end_y_buffer = 0
            if edge_end_shape == 'triangle':
                edge_end_angle -= 150
        elif delta_x < 0:
            edge_end_x_buffer = average_node_width
            edge_end_y_buffer = 0
            if edge_end_shape == 'triangle':
                edge_end_angle += 210
        if delta_y > 0:
            edge_end_x_buffer = 0
            edge_end_y_buffer = -average_node_height
            if edge_end_shape == 'triangle':
                edge_end_angle += 90
        elif delta_y < 0:
            edge_end_x_buffer = 0
            edge_end_y_buffer = average_node_height
            if edge_end_shape == 'triangle':
                edge_end_angle += 90

        if name in self_loops:
            labels_y_offset = self_loop_label_y_offset
            edge_ends_y_offset = -5
            edge_ends_x_offset = node_arc_width + 5
            edge_end_angle = -135
        elif name not in self_loops:
            labels_y_offset = edges_label_y_offset
            edge_ends_y_offset = edge_end_y_buffer
            edge_ends_x_offset = edge_end_x_buffer

        regulations_labels.append({'name': name,
                                   'line_color': value['line_color'],
                                   'x': x1,
                                   'y': y1 + labels_y_offset})

        edge_end_coordinates.append({
            'name': name,
            'x': edge_end_x + edge_ends_x_offset,
            'y': edge_end_y + edge_ends_y_offset,
            'edge_end_angle': edge_end_angle,
            'edge_end_shape': edge_end_shape,
            'stroke_width': stroke_width,
            'line_color': value['line_color']
        })

        for edge_svg_path in edge_svg_paths:
            if edge_svg_path['type'] == 'arc':
                edge_arc_coordinates.append({
                    "name": name,
                    'from_node': value['from_node'],
                    'to_node': value['to_node'],
                    'path': edge_svg_path['path'],
                    'x1': edge_svg_path['coordinates'][0],
                    'y1': edge_svg_path['coordinates'][1],
                    'radius': edge_svg_path['coordinates'][2],
                    'x2': edge_svg_path['coordinates'][4],
                    'y2': edge_svg_path['coordinates'][5],
                    'line_color': value['line_color'],
                    'line_width': value['line_width'],
                    'related_nodes': value['associated_nodes']
                })
            else:
                edge_line_coordinates.append({
                    "name": name,
                    'from_node': value['from_node'],
                    'to_node': value['to_node'],
                    'path': edge_svg_path['path'],
                    'x1': edge_svg_path['coordinates'][0],
                    'y1': edge_svg_path['coordinates'][1],
                    'x2': edge_svg_path['coordinates'][2],
                    'y2': edge_svg_path['coordinates'][3],
                    'line_color': value['line_color'],
                    'line_width': value['line_width'],
                    'related_nodes': value['associated_nodes']
                })

    template_filename = pkg_resources.resource_filename(
        'biosimulators_utils',
        os.path.join('viz', 'vega', 'ginml', 'template.json'),
    )
    with open(template_filename, 'r') as file:
        vega = json.load(file)

    vega['width'] = width
    vega['height'] = height + signal_height + signal_padding

    for signal in vega['signals']:
        if signal['name'] == 'MaxX':
            signal['value'] = width

        elif signal['name'] == 'MaxY':
            signal['value'] = height

        elif signal['name'] == 'MinTime':
            signal.pop('value', None)
            signal['sedmlUri'] = ['SedDocument:[0]', 'Simulation:[0]', 'outputStartTime']

        elif signal['name'] == 'MaxTime':
            signal.pop('value', None)
            signal['sedmlUri'] = ['SedDocument:[0]', 'Simulation:[0]', 'outputEndTime']

        elif signal['name'] == 'Time_step':
            signal.pop('value', None)
            signal['sedmlUri'] = ['SedDocument:[0]', 'Simulation:[0]', 'outputStartTime']

            signal['bind']['min'] = {
                'sedmlUri': ['SedDocument:[0]', 'Simulation:[0]', 'outputStartTime'],
            }
            signal['bind']['max'] = {
                'sedmlUri': ['SedDocument:[0]', 'Simulation:[0]', 'outputEndTime'],
            }

        elif signal['name'] == 'Report':
            signal.pop('value', None)
            signal['sedmlUri'] = ['SedDocument:[0]', 'Report:[0]', 'id']

            signal['bind']['options'] = {
                'sedmlUri': ['SedDocument:*', 'Report:*', 'id'],
            }
            signal['bind']['labels'] = {
                'sedmlUri': ['SedDocument:*', 'Report:*', 'name'],
            }

        elif signal['name'] == 'SignalHeight':
            signal['value'] = signal_height

        elif signal['name'] == 'SignalPadding':
            signal['value'] = signal_padding

    for i_entry, entry in enumerate(vega['data']):
        if entry['name'] == 'nodesData':
            entry['values'] = nodes

        elif entry['name'] == 'nodesLabelsData':
            entry['values'] = node_labels

        elif entry['name'] == 'edgesArcData':
            entry['values'] = edge_arc_coordinates

        elif entry['name'] == 'edgesLineData':
            entry['values'] = edge_line_coordinates

        elif entry['name'] == 'edgeEndCoordinatesData':
            entry['values'] = edge_end_coordinates

        elif entry['name'] == 'edgesLabelsData':
            entry['values'] = regulations_labels

        elif entry['name'] == 'nodesValues':
            vega['data'][i_entry] = copy.copy(node_values_data_set)
            vega['data'][i_entry]['name'] = 'nodesValues'

    # save Vega-formatted map
    with open(vega_filename, 'w') as file:
        json.dump(vega, file, indent=indent)
