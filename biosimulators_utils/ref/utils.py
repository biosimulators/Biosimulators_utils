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
import shutil
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

    if doi is None:
        doi_ref = None
    else:
        doi_ref = get_reference_from_crossref(doi, session=cross_ref_session)

    ref = pubmed_ref or doi_ref
    if ref:
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
        record = get_entrez_record('pubmed', pubmed_id)
        doi = record.get('DOI', None)
        if doi:
            doi = str(doi)
    elif doi:
        record = search_entrez_records("pubmed", doi)

        if len(record.get('IdList', [])) == 0:
            return None

        pubmed_id = str(record['IdList'][0])

        record = get_entrez_record('pubmed', pubmed_id)
    else:
        return None

    try:
        pub_date = dateutil.parser.parse(record['PubDate'])
        date = '{}-{:02d}-{:02d}'.format(pub_date.year, pub_date.month, pub_date.day)
        year = str(pub_date.year)
    except dateutil.parser._parser.ParserError:
        date = str(record['PubDate'])
        year = date.partition(' ')[0]

    pubmed_central_id = get_pubmed_central_id(pubmed_id)

    return JournalArticle(
        pubmed_id=pubmed_id,
        pubmed_central_id=pubmed_central_id,
        doi=doi,
        authors=[str(author) for author in record['AuthorList']],
        title=str(record['Title']).strip('.') if record['Title'] else None,
        journal=str(record['FullJournalName']) if record['FullJournalName'] else None,
        volume=str(record['Volume']) if record['Volume'] else None,
        issue=str(record['Issue']) if record['Issue'] else None,
        pages=str(record['Pages']) if record['Pages'] else None,
        year=year,
        date=date,
    )


def get_pubmed_central_id(pubmed_id):
    """ Get the PubMed Central id for a PubMed record

    Args:
        pubmed_id (:obj:`str`): PubMed id

    Returns:
        :obj:`str`: PubMed Central id
    """
    record = search_entrez_records('pmc', f'{pubmed_id}[pmid]')
    id_list = record.get('IdList', [])
    if id_list:
        record = get_entrez_record('pmc', id_list[0])
        return str(record['ArticleIds']['pmcid'])
    return None


def search_entrez_records(db, term):
    """ Search an Entrez database for a term

    Args:
        db (:obj:`str`): database such as `pmc` for PubMed Central
        term (:obj:`str`): term to search the database
    """
    if not isinstance(term, str) or not term:
        raise TypeError('Search term must be a non-empty string')
    handle = Bio.Entrez.esearch(db=db, term=term, retmode="xml")
    record = Bio.Entrez.read(handle)
    handle.close()
    return record


def get_entrez_record(db, id):
    """ Get a record from an Entrez database

    Args:
        db (:obj:`str`): database such as `pmc` for PubMed Central
        id (:obj:`str`): id of the record
    """
    if not isinstance(id, str):
        raise TypeError('Id must be a string')
    handle = Bio.Entrez.esummary(db=db, id=id, retmode="xml")
    try:
        records = list(Bio.Entrez.parse(handle))
    except RuntimeError:
        raise ValueError('`{}` is not a valid id for a record of `{}`.'.format(id, db))
    handle.close()
    if len(records) != 1:
        raise ValueError('No record for `{}` from `{}` could be obtained.'.format(id, db))
    return records[0]


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
            for author in record.get('author', [])
        ],
        title=record['title'][0].strip('.') if record['title'] else None,
        journal=record['container-title'][0],
        volume=record['volume'],
        issue=record.get('journal-issue', {}).get('issue', None),
        pages=record.get('page', record.get('article-number', None)),
        year=str(record['published']['date-parts'][0][0]),
        date='-'.join('{:02d}'.format(date_part) for date_part in record['published']['date-parts'][0][0:3]),
    )


def get_pubmed_central_open_access_graphics(id, dirname, session=requests):
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

    download_pubmed_central_record(id, tgz_path, tgz_filename, dirname)

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


def download_pubmed_central_record(id, ftp_path, local_filename, local_dirname, max_num_ftp_tries=3):
    """ Download and unpack the files for a PubMed Central record

    Args:
        id (:obj:`str`): PubMed Central id
        ftp_path (:obj:`str`) path to tar file for record within ftp.ncbi.nlm.nih.gov
        local_filename (:obj:`str`) local path to save tar file
        local_dirname (:obj:`str`): local directory to unpack the contents of the tar file
        max_num_ftp_tries (:obj:`int`, optional): maximum number of times to retry downloading the record
    """
    for iter in range(max_num_ftp_tries):
        # download record
        if not os.path.isfile(local_filename):
            ftp = ftplib.FTP('ftp.ncbi.nlm.nih.gov')
            ftp.login()
            with open(local_filename, 'wb') as file:
                ftp.retrbinary('RETR ' + ftp_path, file.write)
            ftp.quit()

        # unpack record
        if not os.path.isdir(os.path.join(local_dirname, id)):
            try:
                with tarfile.open(local_filename) as file:
                    file.extractall(path=local_dirname)
                return
            except tarfile.ReadError:
                os.remove(local_filename)
                if os.path.isdir(os.path.join(local_dirname, id)):
                    shutil.rmtree(os.path.join(local_dirname, id))

    if not os.path.isdir(os.path.join(local_dirname, id)):
        raise Exception('PubMed Central record `{}` could not be downloaded in {} attempts'.format(id, max_num_ftp_tries))
