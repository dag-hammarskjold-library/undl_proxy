from .config import DevelopmentConfig
from .db import get_session
from .marc_xml import MARCXmlParse
from .models import SearchMetadata
from flask import Flask, render_template, request, abort, Response, send_file
from io import BytesIO, StringIO
from logging import getLogger
from pymarc import marcxml
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, InterfaceError
from urllib import request as req
from urllib.error import HTTPError, URLError
import json
import re
import ssl
import csv

session = get_session()

app = Flask(__name__)

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
        records = 10  # set a default
        if not raw_query:
            return "Please supply a URL"
        if not display_fields:
            display_fields = [
                'agenda', 'author',
                'authority_authors', 'document_symbol', 'imprint', 'notes',
                'publisher', 'pubdate', 'pubyear', 'related_documents',
                'subjects', 'summary', 'title', 'voting_record'
            ]
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

        # insert or update SearchMetadata
        search_md, metadata = _update_record_for_url(query, display_fields)

        return render_template(
            'result.html',
            context={
                "search_metadata_id": search_md.id,
                "result": metadata,
                "query": raw_query
            }
        )

    elif request.method == 'GET':
        # either requesting Form or requesting a record by ID
        record = request.args.get('record', None)
        if record:
            sm = session.query(SearchMetadata).get(record)
            if sm:
                ctx = _parse_query(sm.undl_url)
                return render_template(
                    "search_metadata.html",
                    context={
                        "obj": sm.to_dict(),
                        "params": ctx
                    }
                )
            else:
                abort(404)
        else:
            return render_template('index.html')


@app.route('/nav/')
def nav():
    return render_template('nav.html')


# @app.route('/search', defaults={'path': ''})
# @app.route('/search/<path:undl_url>')
def _parse_query(undl_url):
    ctx = {}
    from urllib.parse import parse_qs
    res = parse_qs(undl_url)
    ctx['pattern'] = res.get('p', None)  # search Pattern
    ctx['pattern1'] = res.get('p1', None)
    ctx['collection'] = res.get('c', None)  # collection list
    ctx['collection1'] = res.get('cc', None)  # collection list
    ctx['search_field'] = res.get('f', None)  # search field
    ctx['search_field1'] = res.get('f1', None)  # search field
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
    # logger.info("Pattern: {}".format(p))
    # logger.info("Pattern: {}".format(p1))
    # logger.info("Collection: {}".format(c))
    # logger.info("Collection: {}".format(cc))
    # logger.info("Field: {}".format(f))
    # logger.info("Field: {}".format(f1))
    logger.info("Records in Group: {}".format(rg))
    logger.info("Sort Field: {}".format(sf))
    logger.info("Sort Order: {}".format(so))
    logger.info("Ranking Method: {}".format(rm))
    logger.info("Output Format: {}".format(of))
    logger.info("Output Tags: {}".format(ot))
    logger.info("Part of the page: {}".format(em))
    logger.info("Split Collection: {}".format(sc))
    logger.info("Jump to Record: {}".format(jrec))
    logger.info("Record ID: {}".format(recid))
    logger.info("Date 1: {}".format(d1))
    logger.info("Date 1 year: {}".format(d1y))
    logger.info("Date 1 month: {}".format(d1m))
    logger.info("Date 1 day: {}".format(d1d))
    logger.info("Date 2: {}".format(d2))
    logger.info("Date 2 year: {}".format(d2y))
    logger.info("Date 2 month: {}".format(d2m))
    logger.info("Date 2 day: {}".format(d2d))
    logger.info("Date Type: {}".format(dt))

    return ctx


@app.route("/list")
def list_records():
    context = {}
    searches = session.query(SearchMetadata).all()
    for search in searches:
        context[search.undl_url] = search.undl_url

    return render_template("list.html", context=context)


@app.route("/xml/")
def show_xml():
    rec_id = request.args.get('rec_id')
    refresh = request.args.get('refresh')
    sm = session.query(SearchMetadata).get(int(rec_id))
    if sm:
        if sm.xml and not refresh:
            return Response(sm.xml, mimetype='text/xml')
        elif refresh == "true":
            sm, _ = _update_record_for_url(sm.undl_url, sm.display_fields.split(','))
            return Response(sm.xml, mimetype='text/xml')
        else:
            return "No XML for record {}".format(rec_id)
    else:
        abort(404)


@app.route("/json/")
def show_json():
    rec_id = request.args.get('rec_id')
    refresh = request.args.get('refresh')
    sm = session.query(SearchMetadata).get(int(rec_id))
    if sm:
        if sm.json and not refresh:
            return Response(sm.json, mimetype='text/json')
        elif refresh == 'true':
            sm, _ = _update_record_for_url(sm.undl_url, sm.display_fields.split(','))
            return Response(sm.json, mimetype='text/json')
        else:
            return "No JSON for record {}".format(rec_id)
    else:
        abort(404)


@app.route("/csv/")
def show_csv():
    rec_id = request.args.get('rec_id')
    refresh = request.args.get('refresh')

    def write_to_csv(sm):
        if not sm.json:
            abort(500)
        data = json.loads(sm.json)
        t_file = StringIO()
        processed_data = []
        header = []
        for item in data:
            reduced_item = reduce_item("Data", item)
            header += reduced_item.keys()
            processed_data.append(reduced_item)
        header = list(set(header))
        header.sort()
        writer = csv.DictWriter(t_file, header, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in processed_data:
            writer.writerow(row)

        return t_file

    sm = session.query(SearchMetadata).get(int(rec_id))
    if sm:
        if sm.json and not refresh:
            t_file = write_to_csv(sm)
            return send_file(t_file,
                     attachment_filename="data_{}.csv".format(rec_id),
                     as_attachment=True)
        elif refresh == 'true':
            sm, _ = _update_record_for_url(sm.undl_url, sm.display_fields.split(','))
            t_file = write_to_csv(sm)
            mem = BytesIO()
            mem.write(t_file.getValue().encode('utf-8'))
            mem.seek(0)
            t_file.close()
            return send_file(mem,
                     attachment_filename="data_{}.csv".format(rec_id),
                     as_attachment=True, mimetype='text/csv')
        else:
            return "No JSON for record {}".format(rec_id)
    else:
        abort(404)


def _update_record_for_url(url, display_fields):
    """
    given a url and display fields, update (or create) a SearchMetadata obj
    """
    metadata = []
    collection = _fetch_metadata(url)
    search_md = session.query(SearchMetadata).filter_by(undl_url=url).first()
    if not search_md:
        try:
            fields = ','.join(display_fields)
            search_md = SearchMetadata(undl_url=url)
            search_md.display_fields = fields
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

    return search_md, metadata


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
        Note: switch pubdate and pubyear

    '''
    parser = MARCXmlParse(record)
    ctx = {}
    ctx['title'] = parser.title()
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
        ctx['pubyear'] = parser.pub_date()
    if 'pubdate' in fields:
        ctx['pubdate'] = parser.pubyear()
    if 'related_documents' in fields:
        ctx['related_documents'] = parser.related_documents()
    if 'subjects' in fields:
        ctx['subjects'] = parser.subjects()
    if 'summary' in fields:
        ctx['summary'] = parser.summary()
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


def to_string(s):
    try:
        return str(s)
    except:
        # Change the encoding type if needed
        return s.encode('utf-8')


def reduce_item(key, value):
    reduced_item = {}

    # Reduction Condition 1
    if type(value) is list:
        i = 0
        for sub_item in value:
            reduce_item(key + '_' + to_string(i), sub_item)
            i = i + 1

    # Reduction Condition 2
    elif type(value) is dict:
        sub_keys = value.keys()
        for sub_key in sub_keys:
            reduce_item(key + '_' + to_string(sub_key), value[sub_key])

    # Base Condition
    else:
        reduced_item[to_string(key)] = to_string(value)

    return reduced_item


class PageNotFoundException(Exception):
    pass
