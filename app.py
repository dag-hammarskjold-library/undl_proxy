from .config import DevelopmentConfig
from .db import get_session
from .marc_xml import MARCXmlParse
from .models import SearchMetadata
from flask import Flask, render_template, request, abort, Response
from io import BytesIO
from logging import getLogger
from pymarc import marcxml
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, InterfaceError
from urllib import request as req
from urllib.error import HTTPError, URLError
import json
import re
import ssl

session = get_session()

app = Flask(__name__)
subject_re = re.compile(r"""
        ^\d{6,7}\s(?:unbis[nt])*\s*(.+)$|
        ^([a-zA-Z ]+)\sunbis[nt]\s\d+$|
        ^unbist\s([a-zA-Z ]+)\s\(DHLAUTH\)\d+$|
        ([a-zA-Z ]+)\sunbist\s\(DHLAUTH\)\d+$""", re.X)
reldoc_re = re.compile(r'^([a-zA-Z0-9\/]+)(\(\d{4}\))$')
base_url = 'http://dag.un.org'
path = '/docs'
logger = getLogger(__name__)

app.config.from_object(DevelopmentConfig)


@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(e)
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    app.logger.error(e)
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        # undl URL
        raw_query = request.form.get('undl-query', None)
        num_records = request.form.get('num-records', None)
        display_fields = request.form.getlist('display-fields', None)
        query = ''
        records = num_records
        metadata = []
        # see if there is an output format -- make sure we're getting MARCXML
        m = re.search(r'of=([a-zA-Z]{2,})', raw_query)
        if m:
            query = re.sub(r'of=([a-zA-Z]{2,})', "of=xm", raw_query)
        else:
            query = raw_query + "&of=xm"
        # check num records in group, set to 10 if not set by user
        m = re.search(r'rg=\d+', query)
        if m:
            query = re.sub(r'rg=\d+', "rg={}".format(records), query)
        else:
            query = query + "&rg={}".format(records)
        # only get metadata per user request
        collection = _fetch_metadata(query)
        search_md = session.query(SearchMetadata).filter_by(undl_url=query).first()
        if not search_md:
            try:
                search_md = SearchMetadata(undl_url=query)
                session.add(search_md)
                session.commit()
            except InterfaceError as ex:
                logger.error("Interface error: {}".format(ex))
                abort(500)

            except (IntegrityError, SQLAlchemyError) as ex:
                logger.error("Could not insert/update: {}".format(ex))
                abort(500)

        for record in collection:
            metadata.append(_get_marc_metadata_as_json(record, display_fields))
        pretty_json = json.dumps(metadata, sort_keys=True, indent=2, separators=(',', ': '))
        pretty_xml = _get_marc_metadata_as_xml(collection, display_fields)
        search_md.json = pretty_json
        search_md.xml = pretty_xml
        session.commit()
        return render_template(
            'result.html',
            context={
                "pretty_json": pretty_json,
                "pretty_xml": pretty_xml,
                "result": metadata,
                "query": query}
        )

    elif request.method == 'GET':
        record = request.args.get('record', None)
        if record:
            sm = session.query(SearchMetadata).get(record)
            print(sm)
            if sm:
                return render_template("search_metadata.html", context={"obj": sm.to_dict()})
            else:
                return render_template('index.html')
        else:
            return render_template('index.html')


@app.route('/search', defaults={'path': ''})
@app.route('/search/<path:undl_url>')
def index2(undl_url):
    # undl_url = request.args.get('undl_url', None)
    p = request.args.get('p', None)  # search Pattern
    c = request.args.getlist('c', None)  # collection list
    f = request.args.get('f', None)  # field to search within
    rg = request.args.get('rg', None)  # records in groups of
    sf = request.args.get('sf', None)  # sort field
    so = request.args.get('so', None)  # sort order
    rm = request.args.get('rm', None)  # ranking method
    of = request.args.get('of', None)  # output format
    ot = request.args.get('ot', None)  # output only these MARC tags
    em = request.args.get('em', None)  # output only part of the page.
    sc = request.args.get('sc', None)  # split by collection
    jrec = request.args.get('jrec', None)  # jump to record
    recid = request.args.get('recid', None)  # record id
    d1 = request.args.get('d1', None)  # date 1 as YYYY-mm-dd HH:mm:DD
    d1y = request.args.get('d1y', None)  # date 1 year
    d1m = request.args.get('d1m', None)  # date 1 month
    d1d = request.args.get('d1d', None)  # date 1 day
    d2 = request.args.get('d2', None)  # date 2 as YYYY-mm-dd HH:mm:DD
    d2y = request.args.get('d2y', None)  # date 2 year
    d2m = request.args.get('d2m', None)  # date 2 month
    d2d = request.args.get('d2d', None)  # date 2 day
    dt = request.args.get('dt', None)  # date type -- c=creation, m=modification

    # print("Url: {}".format(url))
    print("Pattern: {}".format(p))
    print("Collection: {}".format(c))
    print("Field: {}".format(f))
    print("Records in Group: {}".format(rg))
    print("Sort Field: {}".format(sf))
    print("Sort Order: {}".format(so))
    print("Ranking Method: {}".format(rm))
    print("Output Format: {}".format(of))
    print("Output Tags: {}".format(ot))
    print("Part of the page: {}".format(em))
    print("Split Collection: {}".format(sc))
    print("Jump to Record: {}".format(jrec))
    print("Record ID: {}".format(recid))
    print("Date 1: {}".format(d1))
    print("Date 1 year: {}".format(d1y))
    print("Date 1 month: {}".format(d1m))
    print("Date 1 day: {}".format(d1d))
    print("Date 2: {}".format(d2))
    print("Date 2 year: {}".format(d2y))
    print("Date 2 month: {}".format(d2m))
    print("Date 2 day: {}".format(d2d))
    print("Date Type: {}".format(dt))
    return undl_url


@app.route("/list")
def list_records():
    context = {}
    searches = session.query(SearchMetadata).all()
    for search in searches:
        context[search.undl_url] = search.to_dict()

    return render_template("list.html", context=context)


@app.route("/xml/")
def show_xml():
    rec_id = request.args.get('rec_id')
    sm = session.query(SearchMetadata).get(int(rec_id))
    if sm:
        if sm.xml:
            return Response(sm.xml, mimetype='text/xml')
        else:
            return "No XML for record {}".format(rec_id)
    else:
        return "Invalid Record ID"


@app.route("/json/")
def show_json():
    rec_id = request.args.get('rec_id')
    sm = session.query(SearchMetadata).get(int(rec_id))
    if sm:
        if sm.json:
            return Response(sm.json, mimetype='text/json')
        else:
            return "No JSON for record {}".format(rec_id)
    else:
        return "Invalid Record ID"


def _fetch_metadata(url):
    """
    @args: url, UNDL url given by user
    raises: 500 error if url can not be retrieved
    parse xml of response and return array of pymarc records
    """
    try:
        resp = req.urlopen(url, context=ssl._create_unverified_context())
    except (HTTPError, URLError) as e:
        logger.error("Error: {}".format(e))
        abort(500)

    if resp.status != 200:
        logger.error("Could not get {}, status: {}".format(url, resp.status))
        abort(500)
    else:
        raw_xml = resp.read()
        xml_doc = BytesIO(raw_xml)
        r = marcxml.parse_xml_to_array(xml_doc, False, 'NFC')
        return r


def _get_marc_metadata_as_json(record, fields):
    '''
    check what fields have been requested
    for each field, set dictionary key to field name
        set dictionary value to MARCXmlParse's value for name

    '''
    parser = MARCXmlParse(record)
    ctx = {}
    if 'agenda' in fields:
        ctx['agenda'] = parser.agenda()
    if 'author' in fields:
        ctx['author'] = parser.author()
    if 'authority_authors' in fields:
        ctx['authority_authors'] = parser.authority_authors()
    if 'document_symbol' in fields:
        ctx['document_symbol'] = parser.document_symbol()
    if 'imprint' in fields:
        ctx['imprint'] = parser.imprint()
    if 'notes' in fields:
        ctx['notes'] = parser.notes()
    if 'publisher' in fields:
        ctx['publisher'] = parser.publisher()
    if 'pubyear' in fields:
        ctx['pubyear'] = parser.pubyear()
    if 'pub_date' in fields:
        ctx['pub_date'] = parser.pub_date()
    if 'related_documents' in fields:
        ctx['related_documents'] = parser.related_documents()
    if 'subjects' in fields:
        ctx['subjects'] = parser.subjects()
    if 'summary' in fields:
        ctx['summary'] = parser.summary()
    if 'title' in fields:
        ctx['title'] = parser.title()
    if 'title_statement' in fields:
        ctx['title_statement'] = parser.title_statement()
    if 'voting_record' in fields:
        ctx['voting_record'] = parser.voting_record()

    return ctx


def _get_marc_metadata_as_xml(collection, fields):
    """
    create new XML doc
    loop over all records in an array of pymarc records
    check requested fields, for each field
    create a new subtag

    """
    from xml.etree import ElementTree as ET
    from xml.dom import minidom

    def prettify(elem):
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    records = ET.Element('records')

    for record in collection:
        parser = MARCXmlParse(record)
        record = ET.SubElement(records, 'record')

        if 'agenda' in fields:
            agenda = ET.SubElement(record, 'agenda')
            agenda.text = parser.agenda()

        if 'author' in fields:
            author = ET.SubElement(record, 'author')
            author.text = parser.author()

        if 'authority_authors' in fields:
            authority_authors = ET.SubElement(record, 'authority_authors')
            for auth_data in parser.authority_authors():
                authority_authors.text = auth_data

        if 'document_symbol' in fields:
            document_symbol = ET.SubElement(record, "document_symbol")
            document_symbol.text = parser.document_symbol()

        if 'imprint' in fields:
            imprint = ET.SubElement(record, "imprint")
            imprint.text = parser.imprint()

        if 'notes' in fields:
            notes = ET.SubElement(record, "notes")
            for note_data in parser.notes():
                note = ET.SubElement(notes, "note")
                note.text = note_data

        if 'publisher' in fields:
            publisher = ET.SubElement(record, 'publisher')
            publisher.text = parser.publisher()

        if 'pubyear' in fields:
            pubyear = ET.SubElement(record, 'pubyear')
            pubyear.text = parser.pubyear()

        if 'pub_date' in fields:
            pubdate = ET.SubElement(record, 'pubdate')
            pubdate.text = parser.pub_date()
        if 'related_documents' in fields:
            related_documents = ET.SubElement(record, 'related_documents')
            for doc in parser.related_documents():
                related_document = ET.SubElement(related_documents, 'related_document')
                related_document.text = doc

        if 'subjects' in fields:
            subjects = ET.SubElement(record, 'subjects')
            for subj in parser.subjects():
                subject = ET.SubElement(subjects, "subject")
                subject.text = subj

        if 'summary' in fields:
            summary = ET.SubElement(record, "summary")
            summary.text = parser.summary()

        if 'title' in fields:
            title = ET.SubElement(record, "title")
            title.text = parser.title()

        if 'title_statement' in fields:
            title_statement = ET.SubElement(record, 'title_statement')
            title_statement.text = parser.title_statement()

        if 'voting_record' in fields:
            voting_record = ET.SubElement(record, 'voting_record')
            for elem in parser.voting_record():
                vote = ET.SubElement(voting_record, 'vote')
                vote.text = elem

    return prettify(records)


class PageNotFoundException(Exception):
    pass


# class MARCXmlParse:
#     '''
#         given an XML record
#         use pymarc to pull out fields:
#             author
#             notes
#             publisher
#             pubyear
#             subjects
#             title
#             document symbol
#             related documents
#     '''
#     def __init__(self, record):
#         self.record = record

#     def author(self):
#         return self.record.author()

#     def authority_authors(self):
#         authors = []
#         for auth in self.record.authority_authors():
#             authors.append(Field.format_field(auth))
#         return authors

#     def title(self):
#         return self.record.title()

#     def subjects(self):
#         subjs = {}
#         for sub in self.record.subjects():
#             logger.debug("Subject: {}".format(sub.value()))
#             m = subject_re.match(sub.value())
#             # kludge!
#             # want cleaner way to show subjects
#             if m:
#                 s = m.group(1)
#                 if not m.group(1):
#                     s = m.group(2)
#                     if not m.group(2):
#                         s = m.group(3)
#                         if not m.group(3):
#                             s = m.group(4)
#                 if s:
#                     search_string = parse.quote_plus(s)
#                     query = "f1=subject&as=1&sf=title&so=a&rm=&m1=p&p1={}&ln=en".format(search_string)
#                     subjs[s] = "https://digitallibrary.un.org/search?ln=en&" + query
#         logger.debug(subjs)
#         return subjs

#     def agenda(self):
#         # FIXME -- these are not showing up
#         return self.record.agenda()

#     def notes(self):
#         return [note.value() for note in self.record.notes()]

#     def publisher(self):
#         return self.record.publisher()

#     def pubyear(self):
#         return self.record.pubyear()

#     def pub_date(self):
#         return self.record.pub_date()

#     def document_symbol(self):
#         return self.record.document_symbol()

#     def related_documents(self):
#         '''
#         tricky edge case:
#         S/RES/2049(2012) is a valid symbol
#         S/RES/2273(2016) is NOT a valie symbol
#         but "S/RES/2273 (2016)" is a valid symbol
#         We want to try both?
#         '''
#         docs = {}
#         for rel_doc in self.record.related_documents():
#             app.logger.debug("Related Doc: {}".format(rel_doc.value()))
#             m = reldoc_re.match(rel_doc.value())
#             if m:
#                 rel_string = m.group(1) + '%20' + m.group(2)
#                 docs[rel_doc.value()] = base_url + path + '/{}'.format(rel_string)
#             else:
#                 docs[rel_doc.value()] = base_url + path + '/{}'.format(rel_doc.value())
#         return docs

#     def summary(self):
#         return self.record.summary()

#     def title_statement(self):
#         return [ts.value() for ts in self.record.title_statement()]

#     def imprint(self):
#         for f in self.record.imprint():
#             return f.value()

#     def voting_record(self):
#         votes = []
#         for vote in self.record.voting_record():
#             votes.append(Field.format_field(vote))
#         return votes
