""" Methods for working with references (e.g., journal articles, books)

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-09-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import JournalArticle, PubMedCentralOpenAccesGraphic
import Bio.Entrez
import dateutil.parser
import ftplib
import glob
import lxml.etree
import os
import requests
import tarfile

__all__ = ['get_reference', 'get_pubmed_central_open_access_graphics']


def get_reference(pubmed_id=None, doi=None, cross_ref_session=requests):
    """ Get data about a reference by its PubMed id and/or DOI

    Args:
        pubmed_id (:obj:`str`, optional): PubMed id
        doi (:obj:`str`, optional): DOI
        session (:obj:`requests.sessions.Session`, optional): requests session

    Returns:
        :obj:`JournalArticle`: data about a reference
    """
    if pubmed_id is None and doi is None:
        raise ValueError('A PubMed id and/or DOI is needed to get information about a reference.')

    pubmed_ref = get_reference_from_pubmed(pubmed_id=pubmed_id, doi=doi)
    if pubmed_ref:
        doi = doi or pubmed_ref.doi

    if doi is not None:
        doi_ref = get_reference_from_crossref(doi, session=cross_ref_session)

    ref = pubmed_ref or doi_ref
    ref.doi = doi
    if doi_ref:
        if len(doi_ref.authors) >= len(ref.authors):
            ref.authors = doi_ref.authors
        ref.journal = doi_ref.journal
        ref.pages = doi_ref.pages

    return ref


def get_reference_from_pubmed(pubmed_id=None, doi=None):
    """ Get data about a reference by its PubMed id

    Args:
        pubmed_id (:obj:`str`, optional): PubMed id
        doi (:obj:`str`, optional): DOI

    Returns:
        :obj:`JournalArticle`: data about a reference
    """
    if pubmed_id:
        handle = Bio.Entrez.esummary(db="pubmed", id=pubmed_id, retmode="xml")
        records = list(Bio.Entrez.parse(handle))
        handle.close()
        if len(records) == 0:
            raise ValueError('`{}` is not a valid PubMed id.'.format(pubmed_id))
        record = records[0]
        doi = record.get('DOI', None)
    else:
        handle = Bio.Entrez.esearch(db="pubmed", term=doi, retmode="xml")
        record = Bio.Entrez.read(handle)
        handle.close()

        if len(record['IdList']) == 0:
            return None

        pubmed_id = record['IdList'][0]

        handle = Bio.Entrez.esummary(db="pubmed", id=pubmed_id, retmode="xml")
        records = list(Bio.Entrez.parse(handle))
        handle.close()
        if len(records) == 0:
            raise ValueError('`{}` is not a valid PubMed id.'.format(pubmed_id))  # pragma: no cover # shouldn't be reachable
        record = records[0]

    try:
        pub_date = dateutil.parser.parse(record['PubDate'])
        date = '{}-{:02d}-{:02d}'.format(pub_date.year, pub_date.month, pub_date.day)
        year = str(pub_date.year)
    except dateutil.parser._parser.ParserError:
        date = record['PubDate']
        year = date.partition(' ')[0]

    return JournalArticle(
        pubmed_id=pubmed_id,
        pubmed_central_id=record['ArticleIds'].get('pmc', None),
        doi=doi,
        authors=record['AuthorList'],
        title=record['Title'].strip('.'),
        journal=record['FullJournalName'],
        volume=record['Volume'],
        issue=record['Issue'],
        pages=record['Pages'],
        year=year,
        date=date,
    )


def get_reference_from_crossref(id, session=requests):
    """ Get data about a reference by its DOI

    Args:
        id (:obj:`str`): DOI
        session (:obj:`requests.sessions.Session`, optional): requests session

    Returns:
        :obj:`JournalArticle`: data about a reference
    """
    response = session.get('https://api.crossref.org/works/' + id)
    response.raise_for_status()
    record = response.json()['message']

    return JournalArticle(
        pubmed_id=None,
        pubmed_central_id=None,
        doi=id,
        authors=[
            author.get('name', (author.get('given', '') + ' ' + author.get('family', '')).strip())
            for author in record['author']
        ],
        title=record['title'][0].strip('.') if record['title'] else None,
        journal=record['container-title'][0],
        volume=record['volume'],
        issue=record.get('journal-issue', {}).get('issue', None),
        pages=record.get('page', record.get('article-number', None)),
        year=str(record['published']['date-parts'][0][0]),
        date='-'.join('{:02d}'.format(date_part) for date_part in record['published']['date-parts'][0][0:3]),
    )


def get_pubmed_central_open_access_graphics(id, dirname, session=requests, max_num_ftp_tries=3):
    """ Get the open access graphics for a publication in PubMed Central

    Args:
        id (:obj:`str`): PubMed Central id
        dirname (:obj:`str`): path to save images
        session (:obj:`requests.session.Session`): requests session

    Returns:
        :obj:`list` of :obj:`PubMedCentralOpenAccesGraphic`: list of graphics
    """
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    response = session.get('https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=' + id)
    response.raise_for_status()
    root = lxml.etree.fromstring(response.content)
    if root.xpath('/OA/error'):
        return []

    tgz_url = root.xpath("/OA/records/record/link[@format='tgz']")[0].attrib['href']
    tgz_path = tgz_url.partition('ftp://')[2].partition('/')[2]
    tgz_filename = os.path.join(dirname, os.path.basename(tgz_path))

    for iter in range(max_num_ftp_tries):
        if not os.path.isfile(tgz_filename):
            ftp = ftplib.FTP('ftp.ncbi.nlm.nih.gov')
            ftp.login()
            with open(tgz_filename, 'wb') as file:
                ftp.retrbinary('RETR ' + tgz_path, file.write)
            ftp.quit()

        if not os.path.isdir(os.path.join(dirname, id)):
            try:
                with tarfile.open(tgz_filename) as file:
                    file.extractall(path=dirname)
                break
            except tarfile.ReadError:
                os.remove(tgz_filename)

        else:
            break

    nxml_filename = glob.glob(os.path.join(dirname, id, "*.nxml"))[0]
    oa_id = os.path.basename(nxml_filename)[0:-5]

    nxml = lxml.etree.parse(nxml_filename).getroot()
    graphics = []
    for figure in nxml.xpath('*//fig'):
        label = figure.xpath('label')
        if len(label):
            label = label[0]

        caption = figure.xpath('caption')
        if len(caption):
            caption = caption[0]

        graphic = figure.xpath('graphic')
        if len(graphic):
            graphic = graphic[0]

        graphics.append(PubMedCentralOpenAccesGraphic(
            id=oa_id + '/' + figure.attrib['id'],
            label=label.text.strip('.') if label is not None else None,
            caption=''.join([lxml.etree.tostring(child).decode('utf8')
                             for child in caption.getchildren()]) if caption is not None else None,
            filename=os.path.join(dirname, id, graphic.attrib['{{{}}}href'.format(graphic.nsmap['xlink'])] + ".jpg"),
        ))

    return graphics
