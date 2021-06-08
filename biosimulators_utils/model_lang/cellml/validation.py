""" Utilities for validating CellML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-10
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import libcellml
import lxml.etree
import os
import pkg_resources


def validate_model(filename, name=None, resolve_imports=True):
    """ Check that a file is a valid CellML model

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages
        resolve_imports (:obj:`bool`, optional): whether to resolve imports

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`tuple`:

                * :obj:`libcellml.model.Model`: model
                * :obj:`lxml.etree._ElementTree`: model
    """
    errors = []
    warnings = []
    model = None

    if not os.path.isfile(filename):
        errors.append(['`{}` is not a file.'.format(filename)])
        return (errors, warnings, (model, None))

    try:
        doc = lxml.etree.parse(filename)
    except lxml.etree.XMLSyntaxError as exception:
        errors.append(['`{}` is not a valid XML file.'.format(filename), [[str(exception)]]])
        return (errors, warnings, (model, None))

    root = doc.getroot()
    default_ns = root.nsmap.get(None, '')
    if default_ns.startswith('http://www.cellml.org/cellml/1.0'):
        v_errors, v_warnings, model = validate_model_version_1_0(filename, doc, resolve_imports=resolve_imports)

    elif default_ns.startswith('http://www.cellml.org/cellml/1.1'):
        v_errors, v_warnings, model = validate_model_version_1_1(filename, doc, resolve_imports=resolve_imports)

    elif default_ns.startswith('http://www.cellml.org/cellml/2'):
        v_errors, v_warnings, model = validate_model_version_2(filename, doc, resolve_imports=resolve_imports)

    else:
        v_errors = [[(
            '`{}` could not be validated. The default namespace must be the namespace of a version of a CellML, not `{}`.'
        ).format(filename, default_ns)]]
        v_warnings = []

    errors.extend(v_errors)
    warnings.extend(v_warnings)

    return (errors, warnings, (model, root))


def validate_model_version_1_0(filename, doc, resolve_imports=True):
    """ Check that a file is a valid CellML 2.0 model

    Args:
        filename (:obj:`str`): path to model
        doc (:obj:`lxml.etree._ElementTree`): XML document for file
        resolve_imports (:obj:`bool`, optional): whether to resolve imports

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`None`
    """

    # ``cellml1.0.rnc`` and ``mathml2.rnc`` were obtained from https://www.cellml.org/tools/validation
    # ``cellml1.0.rng`` and ``mathml2.rng`` were created from ``cellml1.0.rnc`` and and ``mathml2.rnc`` with:
    #
    #     ```
    #     java -jar /home/jonrkarr/.local/lib/python3.9/site-packages/jingtrang/trang.jar \
    #         biosimulators_utils/model_lang/cellml/cellml1.0.rnc \
    #         biosimulators_utils/model_lang/cellml/cellml1.0.rng
    #     java -jar /home/jonrkarr/.local/lib/python3.9/site-packages/jingtrang/trang.jar \
    #         biosimulators_utils/model_lang/cellml/mathml2.rnc \
    #         biosimulators_utils/model_lang/cellml/mathml2.rng
    #     ```

    errors = []
    warnings = []

    schema_filename = pkg_resources.resource_filename('biosimulators_utils',
                                                      os.path.join("model_lang", "cellml", "cellml1.0.rng"))
    schema_doc = lxml.etree.parse(schema_filename)
    schema = lxml.etree.RelaxNG(schema_doc)

    if not schema.validate(doc):
        for error in schema.error_log.filter_levels([lxml.etree.ErrorLevels.ERROR, lxml.etree.ErrorLevels.FATAL]):
            errors.append([
                '{}.{}: {}'.format(error.line, error.column, error.message)
            ])

        for warning in schema.error_log.filter_levels(lxml.etree.ErrorLevels.WARNING):
            warnings.append([
                '{}.{}: {}'.format(warning.line, warning.column, warning.message)
            ])

    return (errors, warnings, None)


def validate_model_version_1_1(filename, doc, resolve_imports=True):
    """ Check that a file is a valid CellML 2.0 model

    Args:
        filename (:obj:`str`): path to model
        doc (:obj:`lxml.etree._ElementTree`): XML document for file
        resolve_imports (:obj:`bool`, optional): whether to resolve imports

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`None`
    """
    errors = []
    warnings = []

    warnings.append(['Validation is not available for CellML 1.1 files.'])

    return (errors, warnings, None)


def validate_model_version_2(filename, doc, resolve_imports=True):
    """ Check that a file is a valid CellML 2.0 model

    Args:
        filename (:obj:`str`): path to model
        doc (:obj:`lxml.etree._ElementTree`): XML document for file
        resolve_imports (:obj:`bool`, optional): whether to resolve imports

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`libcellml.model.Model`: model
    """
    errors = []
    warnings = []

    # read model
    parser = libcellml.Parser()
    with open(filename, 'r') as file:
        model = parser.parseModel(file.read())

    for i_error in range(parser.errorCount()):
        error = parser.error(i_error)
        errors.append([error.description()])

    for i_warning in range(parser.warningCount()):
        warning = parser.warning(i_warning)
        warnings.append([warning.description()])

    if errors:
        return (errors, warnings, model)

    # import imported models
    if resolve_imports:
        importer = libcellml.Importer()
        if not importer.resolveImports(model, os.path.dirname(filename) + os.path.sep):
            for i_error in range(importer.errorCount()):
                error = importer.error(i_error)
                errors.append([error.description()])

            for i_warning in range(importer.warningCount()):
                warning = importer.warning(i_warning)
                warnings.append([warning.description()])

        if errors:
            return (errors, warnings, model)

    # validate model
    validator = libcellml.Validator()
    validator.validateModel(model)

    for i_error in range(validator.errorCount()):
        error = validator.error(i_error)
        errors.append([error.description()])

    for i_warning in range(validator.warningCount()):
        warning = validator.warning(i_warning)
        warnings.append([warning.description()])

    return (errors, warnings, model)
