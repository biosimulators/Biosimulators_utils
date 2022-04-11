""" Data model for COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..utils.core import are_lists_equal, none_sorted
from ..data_model import Person  # noqa: F401
import abc
import datetime  # noqa: F401
import enum

__all__ = [
    'CombineArchiveBase',
    'CombineArchive',
    'CombineArchiveContent',
    'CombineArchiveContentFormat',
    'CombineArchiveContentFormatPattern',
]


class CombineArchiveBase(abc.ABC):
    """ A COMBINE/OMEX archive """
    pass


class CombineArchive(CombineArchiveBase):
    """ A COMBINE/OMEX archive

    Attributes:
        contents (:obj:`list` of :obj:`CombineArchiveContent`): contents of the archive
    """

    def __init__(self, contents=None):
        """
        Args:
            contents (:obj:`list` of :obj:`CombineArchiveContent`, optional): contents of the archive
        """
        self.contents = contents or []

    def get_master_content(self):
        """ Get the master content of an archive

        Returns:
            :obj:`list` of :obj:`CombineArchiveContent`: master content
        """
        master_content = []
        for content in self.contents:
            if content.master:
                master_content.append(content)
        return master_content

    def to_tuple(self):
        """ Tuple representation of a COMBINE/OMEX archive

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of a COMBINE/OMEX archive
        """
        contents = tuple(none_sorted(content.to_tuple() for content in self.contents))
        return (contents)

    def is_equal(self, other):
        """ Determine if two content items are equal

        Args:
            other (:obj:`CombineArchiveContent`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two archives are equal
        """
        return self.__class__ == other.__class__ \
            and are_lists_equal(self.contents, other.contents)


class CombineArchiveContent(CombineArchiveBase):
    """ A content item (e.g., file) in a COMBINE/OMEX archive

    Attributes:
        location (:obj:`str`): path to the content
        format (:obj:`str`): URL for the specification of the format of the content
        master (:obj:`bool`): :obj:`True`, if the content is the "primary" content of the parent archive
    """

    def __init__(self, location=None, format=None, master=False):
        """
        Args:
            location (:obj:`str`, optional): path to the content
            format (:obj:`str`, optional): URL for the specification of the format of the content
            master (:obj:`bool`, optional): :obj:`True`, if the content is the "primary" content of the parent archive
        """
        self.location = location
        self.format = format
        self.master = master

    def to_tuple(self):
        """ Tuple representation of a content item of a COMBINE/OMEX archive

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of a content item of a COMBINE/OMEX archive
        """
        return (self.location, self.format, self.master)

    def is_equal(self, other):
        """ Determine if two content items are equal

        Args:
            other (:obj:`CombineArchiveContent`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two content items are equal
        """
        return self.__class__ == other.__class__ \
            and self.location == other.location \
            and self.format == other.format \
            and self.master == other.master


class CombineArchiveContentFormat(str, enum.Enum):
    """ Format for the content of COMBINE/OMEX archives """
    ACTIONSCRIPT = 'http://purl.org/NET/mediatypes/text/x-actionscript'
    ADOBE_FLASH = 'http://purl.org/NET/mediatypes/application/x-shockwave-flash'
    AI = 'http://purl.org/NET/mediatypes/application/pdf'
    BioPAX = 'http://identifiers.org/combine.specifications/biopax'
    BMP = 'http://purl.org/NET/mediatypes/image/bmp'
    BNGL = 'http://purl.org/NET/mediatypes/text/bngl+plain'
    BOURNE_SHELL = 'http://purl.org/NET/mediatypes/text/x-sh'
    C = 'http://purl.org/NET/mediatypes/text/x-c'
    CellML = 'http://identifiers.org/combine.specifications/cellml'
    CopasiML = 'http://purl.org/NET/mediatypes/application/x-copasi'
    CPP_HEADER = 'http://purl.org/NET/mediatypes/text/x-c++hdr'
    CPP_SOURCE = 'http://purl.org/NET/mediatypes/text/x-c++src'
    CSS = 'http://purl.org/NET/mediatypes/text/css'
    CSV = 'http://purl.org/NET/mediatypes/text/csv'
    DLL = 'http://purl.org/NET/mediatypes/application/vnd.microsoft.portable-executable'
    DOC = 'http://purl.org/NET/mediatypes/application/msword'
    DOCX = 'http://purl.org/NET/mediatypes/application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    EPS = 'http://purl.org/NET/mediatypes/application/postscript'
    Escher = 'http://purl.org/NET/mediatypes/application/escher+json'
    GENESIS = 'http://purl.org/NET/mediatypes/text/x-genesis'
    GIF = 'http://purl.org/NET/mediatypes/image/gif'
    GINML = 'http://purl.org/NET/mediatypes/application/ginml+xml'
    GMSH_MESH = 'http://purl.org/NET/mediatypes/model/mesh'
    GRAPHML = 'http://purl.org/NET/mediatypes/application/graphml+xml'
    HDF5 = 'http://purl.org/NET/mediatypes/application/x-hdf'
    HOC = 'http://purl.org/NET/mediatypes/text/x-hoc'
    HTML = 'http://purl.org/NET/mediatypes/text/html'
    ICO = 'http://purl.org/NET/mediatypes/image/x-icon'
    INI = 'http://purl.org/NET/mediatypes/text/x-ini'
    IPython_Notebook = 'http://purl.org/NET/mediatypes/application/x-ipynb+json'
    JAVA_ARCHIVE = 'http://purl.org/NET/mediatypes/application/java-archive'
    JAVA_CLASS = 'http://purl.org/NET/mediatypes/application/java-vm'
    JAVA_SOURCE = 'http://purl.org/NET/mediatypes/text/x-java'
    JAVASCRIPT = 'http://purl.org/NET/mediatypes/text/javascript'
    JPEG = 'http://purl.org/NET/mediatypes/image/jpeg'
    JSON = 'http://purl.org/NET/mediatypes/application/json'
    Kappa = 'http://purl.org/NET/mediatypes/text/x-kappa'
    LEMS = 'http://purl.org/NET/mediatypes/application/lems+xml'
    MAPLE_WORKSHEET = 'http://purl.org/NET/mediatypes/application/x-maple'
    MARKDOWN = 'http://purl.org/NET/mediatypes/text/markdown'
    MASS = 'http://purl.org/NET/mediatypes/application/mass+json'
    MATHEMATICA_NOTEBOOK = 'http://purl.org/NET/mediatypes/application/vnd.wolfram.mathematica'
    MATLAB = 'http://purl.org/NET/mediatypes/text/x-matlab'
    MATLAB_DATA = 'http://purl.org/NET/mediatypes/application/x-matlab-data'
    MATLAB_FIGURE = 'http://purl.org/NET/mediatypes/application/matlab-fig'
    MorpheusML = 'http://purl.org/NET/mediatypes/application/morpheusml+xml'
    NCS = 'http://purl.org/NET/mediatypes/text/x-ncs'
    NeuroML = 'http://identifiers.org/combine.specifications/neuroml'
    NEURON_SESSION = 'http://purl.org/NET/mediatypes/text/x-nrn-ses'
    NMODL = 'http://purl.org/NET/mediatypes/text/x-nmodl'
    NuML = 'http://purl.org/NET/mediatypes/application/numl+xml'
    ODE = 'http://purl.org/NET/mediatypes/text/x-ode'
    ODT = 'http://purl.org/NET/mediatypes/application/vnd.oasis.opendocument.text'
    OMEX = 'http://identifiers.org/combine.specifications/omex'
    OMEX_MANIFEST = 'http://identifiers.org/combine.specifications/omex-manifest'
    OMEX_METADATA = 'http://identifiers.org/combine.specifications/omex-metadata'
    OWL = 'http://purl.org/NET/mediatypes/application/rdf+xml'
    PDF = 'http://purl.org/NET/mediatypes/application/PDF'
    PERL = 'http://purl.org/NET/mediatypes/text/x-perl'
    pharmML = 'http://purl.org/NET/mediatypes/application/pharmml+xml'
    PHP = 'http://purl.org/NET/mediatypes/application/x-httpd-php'
    PNG = 'http://purl.org/NET/mediatypes/image/png'
    POSTSCRIPT = 'http://purl.org/NET/mediatypes/application/postscript'
    PPT = 'http://purl.org/NET/mediatypes/application/vnd.ms-powerpoint'
    PPTX = 'http://purl.org/NET/mediatypes/application/vnd.openxmlformats-officedocument.presentationml.presentation'
    PSD = 'http://purl.org/NET/mediatypes/image/vnd.adobe.photoshop'
    Python = 'http://purl.org/NET/mediatypes/application/x-python-code'
    QUICKTIME = 'http://purl.org/NET/mediatypes/video/quicktime'
    R = 'http://purl.org/NET/mediatypes/text/x-r'
    R_Project = 'http://purl.org/NET/mediatypes/application/x-r-project'
    RBA = 'http://purl.org/NET/mediatypes/application/rba+zip'
    RDF_XML = 'http://purl.org/NET/mediatypes/application/rdf+xml'
    RST = 'http://purl.org/NET/mediatypes/text/x-rst'
    RUBY = 'http://purl.org/NET/mediatypes/text/x-ruby'
    SBGN = 'http://identifiers.org/combine.specifications/sbgn'
    SBML = 'http://identifiers.org/combine.specifications/sbml'
    SBOL = 'http://identifiers.org/combine.specifications/sbol'
    SBOL_VISUAL = 'http://identifiers.org/combine.specifications/sbol-visual'
    Scilab = 'http://purl.org/NET/mediatypes/application/x-scilab'
    SED_ML = 'http://identifiers.org/combine.specifications/sed-ml'
    SHOCKWAVE_FLASH = 'http://purl.org/NET/mediatypes/application/x-shockwave-flash'
    SimBiology_Project = 'http://purl.org/NET/mediatypes/application/x-sbproj'
    SLI = 'http://purl.org/NET/mediatypes/text/x-sli'
    Smoldyn = 'http://purl.org/NET/mediatypes/text/smoldyn+plain'
    SO = 'http://purl.org/NET/mediatypes/application/x-sharedlib'
    SQL = 'http://purl.org/NET/mediatypes/application/sql'
    SVG = 'http://purl.org/NET/mediatypes/image/svg+xml'
    SVGZ = 'http://purl.org/NET/mediatypes/image/svg+xml-compressed'
    TEXT = 'http://purl.org/NET/mediatypes/text/plain'
    TIFF = 'http://purl.org/NET/mediatypes/image/tiff'
    TSV = 'http://purl.org/NET/mediatypes/text/tab-separated-values'
    VCML = 'http://purl.org/NET/mediatypes/application/vcml+xml'
    Vega = 'http://purl.org/NET/mediatypes/application/vnd.vega.v5+json'
    Vega_Lite = 'http://purl.org/NET/mediatypes/application/vnd.vegalite.v3+json'
    WEBP = 'http://purl.org/NET/mediatypes/image/webp'
    XML = 'http://purl.org/NET/mediatypes/application/xml'
    XPP = 'http://purl.org/NET/mediatypes/text/x-ode'
    XPP_AUTO = 'http://purl.org/NET/mediatypes/text/x-ode-auto'
    XPP_SET = 'http://purl.org/NET/mediatypes/text/x-ode-set'
    XLS = 'http://purl.org/NET/mediatypes/application/vnd.ms-excel'
    XLSX = 'http://purl.org/NET/mediatypes/application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    XSL = 'http://purl.org/NET/mediatypes/application/xslfo+xml'
    XUL = 'http://purl.org/NET/mediatypes/text/xul'
    XYZ = 'http://purl.org/NET/mediatypes/chemical/x-xyz'
    YAML = 'http://purl.org/NET/mediatypes/application/x-yaml'
    ZGINML = 'http://purl.org/NET/mediatypes/application/zginml+zip'
    ZIP = 'http://purl.org/NET/mediatypes/application/zip'
    OTHER = 'http://purl.org/NET/mediatypes/application/octet-stream'


class CombineArchiveContentFormatPattern(str, enum.Enum):
    """ Format for the content of COMBINE/OMEX archives """
    ACTIONSCRIPT = r'^https?://purl\.org/NET/mediatypes/text/x-actionscript$'
    ADOBE_FLASH = r'^https?://purl\.org/NET/mediatypes/(application/x-shockwave-flash|application/vnd\.adobe\.flash-movie)$'
    AI = r'^https?://purl\.org/NET/mediatypes/(application/pdf|application/postscript)$'
    BioPAX = r'^https?://identifiers\.org/combine\.specifications/biopax($|\.)'
    BMP = r'^https?://purl\.org/NET/mediatypes/image/bmp$'
    BNGL = r'^https?://purl\.org/NET/mediatypes/text/bngl\+plain($|\.)'
    BOURNE_SHELL = r'^https?://purl\.org/NET/mediatypes/(text/x-sh|application/x-sh)$'
    C = r'^https?://purl\.org/NET/mediatypes/text/x-c$'
    CellML = r'^https?://identifiers\.org/combine\.specifications/cellml($|\.)'
    CPP_HEADER = r'^https?://purl\.org/NET/mediatypes/text/x-c\+\+hdr$'
    CPP_SOURCE = r'^https?://purl\.org/NET/mediatypes/text/x-c\+\+src$'
    CopasiML = r'^https?://purl\.org/NET/mediatypes/application/x-copasi$'
    CSS = r'^https?://purl\.org/NET/mediatypes/text/css$'
    CSV = r'^https?://purl\.org/NET/mediatypes/text/csv$'
    DLL = r'^https?://purl\.org/NET/mediatypes/application/vnd\.microsoft\.portable-executable$'
    DOC = r'^https?://purl\.org/NET/mediatypes/application/msword$'
    DOCX = r'^https?://purl\.org/NET/mediatypes/application/vnd\.openxmlformats-officedocument\.wordprocessingml\.document$'
    EPS = r'^https?://purl\.org/NET/mediatypes/(application/postscript|application/eps|application/x-eps|image/eps|image/x-eps)$'
    Escher = r'^https?://purl\.org/NET/mediatypes/application/escher\+json$'
    GENESIS = r'^https?://purl\.org/NET/mediatypes/text/x-genesis$'
    GIF = r'^https?://purl\.org/NET/mediatypes/image/gif$'
    GINML = r'^https?://purl\.org/NET/mediatypes/application/ginml\+xml$'
    GMSH_MESH = r'^https?://purl\.org/NET/mediatypes/model/mesh$'
    GRAPHML = r'^https?://purl\.org/NET/mediatypes/(application/graphml\+xml|application/x-graphml\+xml)$'
    HDF5 = r'^https?://purl\.org/NET/mediatypes/application/x-hdf5?$'
    HOC = r'^https?://purl\.org/NET/mediatypes/text/x-hoc$'
    HTML = r'^https?://purl\.org/NET/mediatypes/(text/html|application/xhtml\+xml)$'
    ICO = r'^https?://purl\.org/NET/mediatypes/(image/x-icon|image/vnd\.microsoft\.icon)$'
    INI = r'^https?://purl\.org/NET/mediatypes/text/x-ini$'
    IPython_Notebook = r'^https?://purl\.org/NET/mediatypes/application/x-ipynb\+json$'
    JAVA_ARCHIVE = (
        r'^https?://purl\.org/NET/mediatypes/('
        r'application/java-archive'
        r'|application/x-java-archive'
        r'|application/jar'
        r'|application/x-jar'
        r')$'
    )
    JAVA_CLASS = r'^https?://purl\.org/NET/mediatypes/(application/java-vm|application/x-java-vm|application/java|application/x-java)$'
    JAVA_SOURCE = r'^https?://purl\.org/NET/mediatypes/(text/x-java|text/x-java-source)$'
    JAVASCRIPT = r'^https?://purl\.org/NET/mediatypes/(text/javascript|text/x-javascript|application/javascript|application/x-javascript)$'
    JPEG = r'^https?://purl\.org/NET/mediatypes/image/jpeg$'
    JSON = r'^https?://purl\.org/NET/mediatypes/application/json$'
    Kappa = r'^https?://purl\.org/NET/mediatypes/text/x-kappa$'
    LEMS = r'^https?://purl\.org/NET/mediatypes/application/lems\+xml$'
    MAPLE_WORKSHEET = r'^https?://purl\.org/NET/mediatypes/application/x-maple$'
    MARKDOWN = r'^https?://purl\.org/NET/mediatypes/text/markdown$'
    MASS = r'^https?://purl\.org/NET/mediatypes/application/mass\+json$'
    MATHEMATICA_NOTEBOOK = r'^https?://purl\.org/NET/mediatypes/application/vnd\.wolfram\.mathematica$'
    MATLAB = r'^https?://purl\.org/NET/mediatypes/text/x-matlab$'
    MATLAB_DATA = r'^https?://purl\.org/NET/mediatypes/application/x-matlab-data$'
    MATLAB_FIGURE = r'^https?://purl\.org/NET/mediatypes/application/matlab-fig$'
    MorpheusML = r'^https?://purl\.org/NET/mediatypes/application/morpheusml\+xml$'
    NCS = r'^https?://purl\.org/NET/mediatypes/text/x-ncs$'
    NeuroML = r'^https?://identifiers\.org/combine\.specifications/neuroml($|\.)'
    NEURON_SESSION = r'^https?://purl\.org/NET/mediatypes/text/x-nrn-ses$'
    NMODL = r'^https?://purl\.org/NET/mediatypes/text/x-nmodl$'
    NuML = r'^https?://purl\.org/NET/mediatypes/application/numl\+xml$'
    ODE = r'^https?://purl\.org/NET/mediatypes/text/x-(ode|xpp)$'
    ODT = r'^https?://purl\.org/NET/mediatypes/application/vnd\.oasis\.opendocument\.text$'
    OMEX = r'^https?://identifiers\.org/combine\.specifications/omex($|\.)'
    OMEX_MANIFEST = r'^https?://identifiers\.org/combine\.specifications/omex-manifest($|\.)'
    OMEX_METADATA = r'^https?://identifiers\.org/combine\.specifications/omex-metadata($|\.)'
    OWL = r'^https?://purl\.org/NET/mediatypes/application/rdf\+xml$'
    PDF = r'^https?://purl\.org/NET/mediatypes/application/pdf$'
    PERL = r'^https?://purl\.org/NET/mediatypes/(text/x-perl|application/x-perl)$'
    pharmML = r'^https?://purl\.org/NET/mediatypes/application/pharmml\+xml$'
    PHP = r'^https?://purl\.org/NET/mediatypes/(application/x-httpd-php|application/x-httpd-php-source|application/x-php|text/x-php)$'
    PNG = r'^https?://purl\.org/NET/mediatypes/image/png$'
    POSTSCRIPT = r'^https?://purl\.org/NET/mediatypes/application/postscript$'
    PPT = r'^https?://purl\.org/NET/mediatypes/application/vnd\.ms-powerpoint$'
    PPTX = r'^https?://purl\.org/NET/mediatypes/application/vnd\.openxmlformats-officedocument\.presentationml\.presentation$'
    PSD = (
        r'^https?://purl\.org/NET/mediatypes/('
        r'image/vnd\.adobe\.photoshop'
        r'|image/psd'
        r'|image/x-psd'
        r'|application/photoshop'
        r'|application/x-photoshop'
        r'|application/psd'
        r'|application/x-psd'
        r')$'
    )
    Python = r'^https?://purl\.org/NET/mediatypes/application/x-python-code$'
    QUICKTIME = r'^https?://purl\.org/NET/mediatypes/(video/quicktime|image/mov)$'
    R = r'^https?://purl\.org/NET/mediatypes/text/x-r$'
    R_Project = r'^https?://purl\.org/NET/mediatypes/application/x-r-project$'
    RBA = r'^https?://purl\.org/NET/mediatypes/application/rba\+zip$'
    RDF_XML = r'^https?://purl\.org/NET/mediatypes/application/rdf\+xml$'
    RST = r'^https?://purl\.org/NET/mediatypes/text/x-rst$'
    RUBY = r'^https?://purl\.org/NET/mediatypes/text/x-ruby$'
    SBGN = r'^https?://identifiers\.org/combine\.specifications/sbgn($|\.)'
    SBML = r'^https?://identifiers\.org/combine\.specifications/sbml($|\.)'
    SBOL = r'^https?://identifiers\.org/combine\.specifications/sbol($|\.)'
    SBOL_VISUAL = r'^https?://identifiers\.org/combine\.specifications/sbol-visual($|\.)'
    Scilab = r'^https?://purl\.org/NET/mediatypes/application/x-scilab$'
    SED_ML = r'^https?://identifiers\.org/combine\.specifications/sed\-?ml($|\.)'
    SHOCKWAVE_FLASH = r'^https?://purl\.org/NET/mediatypes/(application/x-shockwave-flash|application/vnd\.adobe\.flash-movie)$'
    SimBiology_Project = r'^https?://purl\.org/NET/mediatypes/application/x-sbproj$'
    SLI = r'^https?://purl\.org/NET/mediatypes/text/x-sli$'
    Smoldyn = r'^https?://purl\.org/NET/mediatypes/text/smoldyn\+plain$'
    SO = r'^https?://purl\.org/NET/mediatypes/application/x-sharedlib$'
    SQL = r'^https?://purl\.org/NET/mediatypes/application/sql$'
    SVG = r'^https?://purl\.org/NET/mediatypes/image/svg\+xml$'
    SVGZ = r'^https?://purl\.org/NET/mediatypes/image/svg\+xml-compressed$'
    TEXT = r'^https?://purl\.org/NET/mediatypes/text/plain$'
    TIFF = r'^https?://purl\.org/NET/mediatypes/image/tiff$'
    TSV = r'^https?://purl\.org/NET/mediatypes/text/tab-separated-values$'
    Vega = r'^https?://purl\.org/NET/mediatypes/application/vnd\.vega\.v5\+json$'
    Vega_Lite = r'^https?://purl\.org/NET/mediatypes/application/vnd\.vegalite\.v3\+json$'
    VCML = r'^https?://purl\.org/NET/mediatypes/application/vcml\+xml$'
    WEBP = r'^https?://purl\.org/NET/mediatypes/image/webp$'
    XLS = r'^https?://purl\.org/NET/mediatypes/application/vnd\.ms-excel$'
    XLSX = r'^https?://purl\.org/NET/mediatypes/application/vnd\.openxmlformats-officedocument\.spreadsheetml\.sheet$'
    XML = r'^https?://purl\.org/NET/mediatypes/application/xml$'
    XPP = r'^https?://purl\.org/NET/mediatypes/text/x-(ode|xpp)$'
    XPP_AUTO = r'^https?://purl\.org/NET/mediatypes/text/x-(ode|xpp)-auto$'
    XPP_SET = r'^https?://purl\.org/NET/mediatypes/text/x-(ode|xpp)-set$'
    XSL = r'^https?://purl\.org/NET/mediatypes/(application/xslfo\+xml|text/xsl)$'
    XUL = r'^https?://purl\.org/NET/mediatypes/text/xul$'
    XYZ = r'^https?://purl\.org/NET/mediatypes/chemical/x-xyz$'
    YAML = r'^https?://purl\.org/NET/mediatypes/application/x-yaml$'
    ZGINML = r'^https?://purl\.org/NET/mediatypes/application/zginml\+zip$'
    ZIP = r'^https?://purl\.org/NET/mediatypes/application/zip$'
    OTHER = r'^https?://purl\.org/NET/mediatypes/application/octet-stream$'
