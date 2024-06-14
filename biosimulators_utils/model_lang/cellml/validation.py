""" Utilities for validating CellML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-10
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...config import Config, get_config  # noqa: F401
import libcellml
import lxml.etree
import os
import pkg_resources


def validate_model(filename, name=None, resolve_imports=True, config=None):
    """ Check that a file is a valid CellML model

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages
        resolve_imports (:obj:`bool`, optional): whether to resolve imports
        config (:obj:`Config`, optional): whether to fail on missing includes

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
        v_errors, v_warnings, model = validate_model_version_1_0(filename, doc, resolve_imports=resolve_imports, config=config)

    elif default_ns.startswith('http://www.cellml.org/cellml/1.1'):
        v_errors, v_warnings, model = validate_model_version_1_1(filename, doc, resolve_imports=resolve_imports, config=config)

    elif default_ns.startswith('http://www.cellml.org/cellml/2'):
        v_errors, v_warnings, model = validate_model_version_2(filename, doc, resolve_imports=resolve_imports, config=config)

    else:
        v_errors = [[(
            '`{}` could not be validated. The default namespace must be the namespace of a version of a CellML, not `{}`.'
        ).format(filename, default_ns)]]
        v_warnings = []

    errors.extend(v_errors)
    warnings.extend(v_warnings)

    return (errors, warnings, (model, root))


def validate_doc_against_schema(doc, schema):
    errors = []
    warnings = []
    if not schema.validate(doc):
        for error in schema.error_log.filter_levels([lxml.etree.ErrorLevels.ERROR, lxml.etree.ErrorLevels.FATAL]):
            errors.append([
                '{}.{}: {}'.format(error.line, error.column, error.message)
            ])

        for warning in schema.error_log.filter_levels(lxml.etree.ErrorLevels.WARNING):
            warnings.append([
                '{}.{}: {}'.format(warning.line, warning.column, warning.message)
            ])

    return errors, warnings


def validate_model_version_1_0(filename, doc, resolve_imports=True, config=None):
    """ Check that a file is a valid CellML 2.0 model

    Args:
        filename (:obj:`str`): path to model
        doc (:obj:`lxml.etree._ElementTree`): XML document for file
        resolve_imports (:obj:`bool`, optional): whether to resolve imports
        config (:obj:`Config`, optional): whether to fail on missing includes

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

    schema_filename = pkg_resources.resource_filename('biosimulators_utils',
                                                      os.path.join("model_lang", "cellml", "cellml1.0.rng"))
    schema_doc = lxml.etree.parse(schema_filename)
    schema = lxml.etree.RelaxNG(schema_doc)

    errors, warnings = validate_doc_against_schema(doc, schema)

    return (errors, warnings, None)


def validate_model_version_1_1(filename, doc, resolve_imports=True, config=None):
    """ Check that a file is a valid CellML 2.0 model

    Args:
        filename (:obj:`str`): path to model
        doc (:obj:`lxml.etree._ElementTree`): XML document for file
        resolve_imports (:obj:`bool`, optional): whether to resolve imports
        config (:obj:`Config`, optional): whether to fail on missing includes
    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`None`
    """
    # ``cellml_1_1_original.xsd`` was obtained from https://www.cellml.org/tools/cellml_1_1_schema
    # `cellml_1_1.xsd`` was created by were directly downloading all referenced namspaces from
    # https://www.cellml.org/tools/cellml_1_1_schema/common,
    # https://www.cellml.org/tools/cellml_1_1_schema/content,
    # https://www.cellml.org/tools/cellml_1_1_schema/presentation
    # The original ``cellml_1_1.xsd`` was modified to change the http sources to local sources.
    # Additionally, the following two lines were removed from the ``cellml_1_1_original.xsd``: 113, 309
    # These lines added the following to the definitions of "Component" and "Role":  <any namespace="##other" processContents="skip"/>
    # This caused lxml to fail to parse the schema due to it being nondeterministic.
    # In its place, <any namespace="http://www.w3.org/1999/02/22-rdf-syntax-ns#"  processContents="skip" />
    # was added to allow using RDF syntax in the schema. The RDF is not validated.
    # Finally, in common/common-attribs.xsd the type of the attribute "id" was changed from "ID" to "string".
    # This was done to allow using numbers as ids for equations as described in the CellML primer.

    schema_filename = pkg_resources.resource_filename('biosimulators_utils',
                                                      os.path.join("model_lang", "cellml", "cellml_1_1.xsd"))

    xml_schema_doc = lxml.etree.parse(schema_filename)

    schema = lxml.etree.XMLSchema(xml_schema_doc)

    errors, warnings = validate_doc_against_schema(doc, schema)

    return (errors, warnings, None)


def validate_model_version_2(filename, doc, resolve_imports=True, config=None):
    """ Check that a file is a valid CellML 2.0 model

    Args:
        filename (:obj:`str`): path to model
        doc (:obj:`lxml.etree._ElementTree`): XML document for file
        resolve_imports (:obj:`bool`, optional): whether to resolve imports
        config (:obj:`Config`, optional): whether to fail on missing includes

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`libcellml.model.Model`: model
    """
    config = config or get_config()

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
    if resolve_imports and config.VALIDATE_IMPORTED_MODEL_FILES:
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
