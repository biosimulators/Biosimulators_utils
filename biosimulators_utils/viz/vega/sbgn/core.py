""" Utility for converting activity SBGN process description (PD) maps to Vega format

:Author: Andrew Freiburger <afreiburger@uvic.ca>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-08-11
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from math import inf
from xml.etree import ElementTree
import copy
import json
import os
import pkg_resources


__all__ = ['sbgn_pd_map_to_vega']


def sbgn_pd_map_to_vega(glyph_values_data_set, sbgn_filename, vega_output_filename,
                        max_width=700, max_height=700, indent=2):
    """ Convert a process description (PD) map from SBGN to Vega format.

    Args:
        glyph_values_data_set (:obj:`dict`): Vega data set with the predicted dynamics of one or more glyphs. The dictionary should
            have one of the following schemas

            * Contain a key ``values`` whose value is a list of the predicted values of the glyphs. Each element of the list
              should be a dictionary with two keys

                * ``label``: value should be the SBGN ``label`` of the corresponding glyph
                * ``values``: array of the predicted values of the glyph

            * Contain a key ``url`` whose value is a URL where the predicted values of the glyphs can be retrieved in JSON
              format. The data should be in the same format outlined above.
            * Contain a key ``sedmlUri`` whose value is an array which contains two elements that indicate

                * The location of the SED-ML file (within its parent COMBINE/OMEX archive) which will produce
                  the predicted values of the glyphs
                * The id of the SED-ML report which will contain the predicted values of the glyphs for the visualization

        sbgn_filename (:obj:`str`): the name of the SBGN file that will be parsed
        vega_output_filename (:obj:`str`): path to the ginsim simulation data
        max_width (:obj:`int`): maximum diagram width
        max_height (:obj:`int`): maximum diagram height
        indent (:obj:`int` or :obj:`None`, optional): indentation for exported Vega file
    """

    # read the SBGN file
    root = ElementTree.parse(sbgn_filename).getroot()

    # get the default namespace used in the SBGN file
    sbgn_ns = root.tag[1:].partition('}')[0]

    # get the process description map
    map = root.find('{{{}}}map'.format(sbgn_ns))

    # ============================================== PARSE THE GLYPHS (NODES) ===============================================
    glyphs = []
    for glyph_xml in map.findall('{{{}}}glyph'.format(sbgn_ns)):
        # determine the glyph process
        glyph_class = glyph_xml.attrib['class']

        # determine the glyph id and label
        glyph_id = glyph_xml.attrib['id']

        label_xml = glyph_xml.find('{{{}}}label'.format(sbgn_ns))
        if label_xml is not None:
            glyph_label = label_xml.attrib['text']
        else:
            glyph_label = None

        # determine the glyph coordinates and size
        glyph_bounding_box = glyph_xml.find('{{{}}}bbox'.format(sbgn_ns))
        x_coordinate = float(glyph_bounding_box.attrib['x'])
        y_coordinate = float(glyph_bounding_box.attrib['y'])
        glyph_width = float(glyph_bounding_box.attrib['w'])
        glyph_height = float(glyph_bounding_box.attrib['h'])
        glyph_orientation = glyph_xml.attrib.get('orientation', None)

        # organize the aforementioned data
        glyph = {
            'id': glyph_id,
            'label': glyph_label,
            'class': glyph_class,
            'orientation': glyph_orientation,
            'x': x_coordinate,
            'y': y_coordinate,
            'width': glyph_width,
            'height': glyph_height,
        }
        glyphs.append(glyph)

        # parse the sub-glyph port objects
        """
        port_values = child.findall('{{{}}}port'.format(sbgn_ns))
        if port_values:
            for port in port_values:
                port_y = port.attrib['y']
                port_x = port.attrib['x']
                port_id = port.attrib['id']

                # organize the aforementioned data
                glyphs.append({
                    'id': port_id,
                    'process': glyph_class,
                    'x': port_x,
                    'y': port_y,
                    'width': 10,
                    'height': 10,
                })
        """

    # determine the maximum boundaries of the figure
    min_x = inf
    min_y = inf
    max_x = -inf
    max_y = -inf
    for glyph in glyphs:
        min_x = min(min_x, glyph['x'] - glyph['width'] / 2)
        max_x = max(max_x, glyph['x'] + glyph['width'] / 2)
        min_y = min(min_y, glyph['y'] - glyph['height'] / 2)
        max_y = max(max_y, glyph['y'] + glyph['height'] / 2)

    min_x += 15
    max_x += 40
    min_y += 15
    max_y += 20

    sbgn_width = max_x - min_x
    sbgn_height = max_y - min_y

    if sbgn_width / max_width > sbgn_height / max_height:
        width = max_width
        coordinate_scale = width / sbgn_width
        height = sbgn_height * coordinate_scale
    else:
        height = max_height
        coordinate_scale = height / sbgn_height
        width = sbgn_width * coordinate_scale

    # redefine the glyph values
    for glyph in glyphs:
        glyph["x"] = (glyph['x'] - min_x) * coordinate_scale
        glyph["y"] = (glyph['y'] - min_y) * coordinate_scale
        glyph["height"] = glyph["height"] * coordinate_scale
        glyph["width"] = glyph["width"] * coordinate_scale

    # ============================================== PARSE THE ARCS (EDGES) ===============================================

    # parse the arcs
    arcs = []
    for child in map.findall('{{{}}}arc'.format(sbgn_ns)):
        # determine the arc process and general information
        arc_id = child.attrib['id']
        arc_class = child.attrib['class']
        source_glyph = child.attrib['source']
        target_glyph = child.attrib['target']

        # determine the coordinates of the arc
        start_point = child.find('{{{}}}start'.format(sbgn_ns))
        x1 = (float(start_point.attrib['x']) - min_x) * coordinate_scale
        y1 = (float(start_point.attrib['y']) - min_y) * coordinate_scale

        end_point = child.find('{{{}}}end'.format(sbgn_ns))
        x2 = (float(end_point.attrib['x']) - min_x) * coordinate_scale
        y2 = (float(end_point.attrib['y']) - min_y) * coordinate_scale

        # organizing the arc information
        arcs.append({
            "id": arc_id,
            'class': arc_class,
            'source': source_glyph,
            'target': target_glyph,
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
        })

    # ============================================== EXPORT TO VEGA ===============================================
    # import the Vega template
    vega_template_filename = pkg_resources.resource_filename(
        'biosimulators_utils',
        os.path.join('viz', 'vega', 'sbgn', 'pd.template.json'))
    with open(vega_template_filename, 'r') as file:
        vega = json.load(file)
    vega['width'] = width
    vega['height'] = height

    # assign values to the Vega data sets
    signal_name_to_signal = {signal['name']: signal for signal in vega['signals']}
    signal_name_to_signal['sbgnWidth']['value'] = width
    signal_name_to_signal['sbgnHeight']['value'] = height

    signal = signal_name_to_signal['OutputStartTime']
    signal.pop('value', None)
    signal['sedmlUri'] = ['SedDocument:[0]', 'Simulation:[0]', 'outputStartTime']

    signal = signal_name_to_signal['OutputEndTime']
    signal.pop('value', None)
    signal['sedmlUri'] = ['SedDocument:[0]', 'Simulation:[0]', 'outputEndTime']

    signal = signal_name_to_signal['NumberOfSteps']
    signal.pop('value', None)
    signal['sedmlUri'] = ['SedDocument:[0]', 'Simulation:[0]', 'numberOfSteps']

    signal = signal_name_to_signal['Time_step']
    signal['value'] = 0
    signal['bind']['min'] = 0
    signal['bind']['max'] = {
        'sedmlUri': ['SedDocument:[0]', 'Simulation:[0]', 'numberOfSteps'],
    }
    signal['bind']['step'] = 1

    # assign values to the Vega data sets
    data_set_name_to_index = {data_set['name']: i_data_set for i_data_set, data_set in enumerate(vega['data'])}
    vega['data'][data_set_name_to_index['glyphsData']]['values'] = glyphs
    vega['data'][data_set_name_to_index['arcsData']]['values'] = arcs
    vega['data'][data_set_name_to_index['glyphsValues']] = copy.copy(glyph_values_data_set)
    vega['data'][data_set_name_to_index['glyphsValues']]['name'] = 'glyphsValues'

    # export the Vega visualization
    with open(vega_output_filename, 'w') as file:
        json.dump(vega, file, indent=indent)
