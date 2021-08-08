""" Methods for validating XPP files

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-08-06
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import collections
import os
import subprocess
import tempfile


def validate_model(filename, name=None):
    """ Check that a model is valid

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`dict`: values of parameters of initial conditions of variables
    """
    errors = []
    warnings = []
    simulation = None

    # check model file exists and is valid
    if not isinstance(filename, str):
        errors.append(['`{}` is not a path to an XPP file.'.format(filename)])
        return (errors, warnings, simulation)

    if not os.path.isfile(filename):
        errors.append(['XPP file `{}` does not exist.'.format(filename)])
        return (errors, warnings, simulation)

    var_param_fid, var_param_filename = tempfile.mkstemp()
    os.close(var_param_fid)

    result = subprocess.run(
        ['xppaut', filename, '-qics', '-qpars', '-outfile', var_param_filename, '-quiet', '0'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    stdout = result.stdout.decode(errors='ignore').strip()

    if result.returncode != 0:
        errors.append(['`{}` could not be validated.'.format(filename), [[stdout]]])

    elif 'ERROR' in stdout:
        errors.append(['`{}` is not a valid XPP file.'.format(filename), [[stdout]]])

    else:
        result = subprocess.run(
            ['xppaut', filename, '-qics', '-qpars', '-outfile', var_param_filename, '-quiet', '1'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        stdout = result.stdout.decode(errors='ignore').strip()
        if stdout:
            warnings.append([
                'The XPP file may be not be formulated correctly',
                [
                    [line] for line in stdout.split('\n')
                ],
            ])

        simulation = {
            'parameters': collections.OrderedDict(),
            'initial_conditions': collections.OrderedDict(),
            'simulation_method': {},
        }
        block = None
        with open(var_param_filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('#'):
                    if line == '#Parameters query:':
                        block = 'parameters'
                    if line == '#Initial conditions query:':
                        block = 'initial_conditions'
                elif block:
                    id, _, value = line.partition(' ')
                    simulation[block][id] = float(value)

        with open(filename, 'r') as file:
            for line in file:
                if line.startswith('@'):
                    line = line[1:]
                    i_comment = line.find('#')
                    if i_comment > -1:
                        line = line[0:i_comment]
                    for cmd in line.split(','):
                        parts = cmd.split('=')
                        if len(parts) > 1:
                            key = parts[0].lstrip()
                            val = parts[1].rstrip()
                            if ' ' not in key and ' ' not in val:
                                key = key.lower()
                                if key == 'nout':
                                    key = 'njmp'
                                simulation['simulation_method'][key] = val
                if line.startswith('d') and not ('=' in line and (' ' not in line or line.find('=') < line.find(' '))):
                    # check for "done" line; note just the singular character ``d`` defines the "done" line
                    break

        t_0 = simulation['simulation_method'].get('t0', 0.)
        try:
            t_0 = float(t_0)
        except ValueError:
            errors.append(['T0 must be a float, not `{}`'.format(t_0)])

        duration = simulation['simulation_method'].get('total', 20.)
        try:
            duration = float(duration)
        except ValueError:
            errors.append(['TOTAL must be a float, not `{}`'.format(duration)])

        d_t = simulation['simulation_method'].get('dt', 0.05)
        try:
            d_t = float(d_t)
        except ValueError:
            errors.append(['DT must be a float, not `{}`'.format(d_t)])

        n_jmp = simulation['simulation_method'].get('njmp', 1)
        try:
            n_jmp = float(n_jmp)
            if n_jmp != int(n_jmp) or n_jmp < 1:
                errors.append(['NJMP must be a positive integer, not `{}`'.format(n_jmp)])
        except ValueError:
            errors.append(['NJMP must be a positive integer, not `{}`'.format(n_jmp)])

        if not errors:
            number_of_steps = duration / (d_t * n_jmp)
            if (number_of_steps % 1.) > 1e-8:
                errors.append([
                    'Number of steps must be an integer',
                    [
                        ['t0: {}'.format(t_0)],
                        ['total: {}'.format(duration)],
                        ['dt: {}'.format(d_t)],
                        ['njmp: {}'.format(n_jmp)],
                    ],
                ])

    os.remove(var_param_filename)

    return (errors, warnings, simulation)
