from pymarc.field import Field
from logging import getLogger
from urllib import parse
from flask import Flask
from .config import DevelopmentConfig

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

base_url = app.config.get('BASE_URL')
path = app.config.get('PATH')


logger = getLogger(__name__)

subject_re = app.config.get('SUBJECT_RE')
reldoc_re = app.config.get('RELDOC_RE')


class MARCXmlParse:
    '''
        given an XML record
        use pymarc to pull out fields:
            author
            notes
            publisher
            pubyear
            subjects
            title
            document symbol
            related documents
    '''
    def __init__(self, record):
        self.record = record

    def author(self):
        return self.record.author()

    def authority_authors(self):
        authors = []
        for auth in self.record.authority_authors():
            authors.append(Field.format_field(auth))
        return authors

    def title(self):
        return self.record.title()

    def subjects(self):
        subjs = {}
        for sub in self.record.subjects():
            logger.debug("Subject: {}".format(sub.value()))
            m = subject_re.match(sub.value())
            # kludge!
            # want cleaner way to show subjects
            if m:
                s = m.group(1)
                if not m.group(1):
                    s = m.group(2)
                    if not m.group(2):
                        s = m.group(3)
                        if not m.group(3):
                            s = m.group(4)
                if s:
                    search_string = parse.quote_plus(s)
                    query = "f1=subject&as=1&sf=title&so=a&rm=&m1=p&p1={}&ln=en".format(search_string)
                    subjs[s] = "https://digitallibrary.un.org/search?ln=en&" + query
        logger.debug(subjs)
        return subjs

    def agenda(self):
        # FIXME -- these are not showing up
        return self.record.agenda()

    def notes(self):
        return [note.value() for note in self.record.notes()]

    def publisher(self):
        return self.record.publisher()

    def pubyear(self):
        return self.record.pubyear()

    def pub_date(self):
        return self.record.pub_date()

    def document_symbol(self):
        return self.record.document_symbol()

    def related_documents(self):
        '''
        tricky edge case:
        S/RES/2049(2012) is a valid symbol
        S/RES/2273(2016) is NOT a valie symbol
        but "S/RES/2273 (2016)" is a valid symbol
        We want to try both?
        '''
        docs = {}
        for rel_doc in self.record.related_documents():
            app.logger.debug("Related Doc: {}".format(rel_doc.value()))
            m = reldoc_re.match(rel_doc.value())
            if m:
                rel_string = m.group(1) + '%20' + m.group(2)
                docs[rel_doc.value()] = base_url + path + '/{}'.format(rel_string)
            else:
                docs[rel_doc.value()] = base_url + path + '/{}'.format(rel_doc.value())
        return docs

    def summary(self):
        return self.record.summary()

    def title_statement(self):
        return [ts.value() for ts in self.record.title_statement()]

    def imprint(self):
        for f in self.record.imprint():
            return f.value()

    def voting_record(self):
        votes = []
        for vote in self.record.voting_record():
            votes.append(Field.format_field(vote))
        return votes
