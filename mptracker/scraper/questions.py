""" Fetch and parse questions & interpellations """

import sys
import re
from datetime import datetime
from path import path
from flask import json
from pyquery import PyQuery as pq
from mptracker.scraper.common import (Scraper, pqitems, get_cached_session,
                                      get_cdep_id)


with open(path(__file__).parent / 'question_exceptions.json') as f:
    exceptions = json.load(f)
    url_skip = set(exceptions['url_skip'])


class Question:

    def __str__(self):
        return ("<Question type={o.q_type}"
                         " number={o.number!r}"
                         " date={o.date_record}"
                         " person_name={o.person_name!r}"
                         " person_cdep_id={o.person_cdep_id}"
                         ">").format(o=self)


class QuestionScraper(Scraper):

    title_pattern = re.compile(r'^(?P<type>Întrebarea|Interpelarea) nr\.')
    types = {
        'Întrebarea': 'question',
        'Interpelarea': 'interpelation',
    }

    def normalize_space(self, text):
        return re.sub(r'\s+', ' ', text)

    def parse_date_dmy(self, text):
        return datetime.strptime(text, '%d-%m-%Y').date()

    def person_from_td(self, td):
        for link in pqitems(td, 'a'):
            href = link.attr('href')
            if href.startswith('http://www.cdep.ro/pls/'
                               'parlam/structura.mp?'):
                return link.text(), get_cdep_id(href)

    def get_question(self, href):
        page = self.fetch_url(href)
        heading = page('#pageHeader .pageHeaderLinks').text()
        heading_m = self.title_pattern.match(heading)
        assert heading_m is not None, "Could not parse heading %r" % heading
        question = Question()
        question.q_type = self.types[heading_m.group('type')]

        question.url = href
        question.title = page('.headline').text()

        rows = pqitems(page, '#pageContent > dd > table > tr')
        assert (self.normalize_space(next(rows).text()) ==
                'Informaţii privind interpelarea')

        question.pdf_url = None
        question.addressee = []
        question.method = None

        label_text = None

        for row in rows:
            norm_text = self.normalize_space(row.text())
            if norm_text == '':
                continue
            elif norm_text == 'Informaţii privind răspunsul':
                break

            [label, value] = [pq(el) for el in row[0]]
            new_label_text = label.text()
            if new_label_text:
                label_text = new_label_text
            else:
                if label_text != 'Destinatari:':
                    continue

            if label_text == 'Nr.înregistrare:':
                question.number = value.text()
            elif label_text == 'Data înregistrarii:':
                question.date = self.parse_date_dmy(value.text())
            elif label_text == 'Mod adresare:':
                question.method = value.text()
            elif label_text in ['Destinatar:', 'Destinatari:']:
                ministry_el = list(pqitems(value, 'b'))[0]
                question.addressee.append(ministry_el.text())
            elif label_text == 'Adresant:' or label_text == 'Adresanţi:':
                (question.person_name, question.person_cdep_id) = \
                    self.person_from_td(value)
            elif label_text == 'Textul intervenţiei:':
                link = list(pqitems(value, 'a'))[-1]
                assert link.text() == "fişier PDF"
                question.pdf_url = link.attr('href')

        question_id = '{q.date}-{q.number}'.format(q=question)
        patch = exceptions['patch'].get(question_id, {})
        for k in patch:
            setattr(question, k, patch[k])

        return question

    def run(self, year):
        index = self.fetch_url('http://www.cdep.ro/pls/parlam/'
                               'interpelari.lista?tip=&dat={year}&idl=1'
                               .format(year=year))
        for link in pqitems(index, '#pageContent table a'):
            href = link.attr('href')
            if href in url_skip:
                continue
            assert href.startswith('http://www.cdep.ro/pls/'
                                   'parlam/interpelari.detalii')

            yield self.get_question(href)


def scrape_question_list():
    import csv
    questions_scraper = QuestionScraper(get_cached_session())
    out = csv.writer(sys.stdout)
    out.writerow(['person_name', 'person_cdep_id', 'number', 'date', 'type',
                  'title', 'url', 'pdf_url', 'addressee'])
    for question in questions_scraper.run(2013):
        out.writerow([
            question.person_name,
            question.person_cdep_id,
            question.number,
            question.date,
            question.q_type,
            question.title,
            question.url,
            question.pdf_url,
            question.addressee,
        ])


def scrape_pdf(url):
    print(url)
    session = get_cached_session('question-pdf')
    pdf_content = session.get(url).content
    print(len(pdf_content), 'bytes')


def main():
    cmd = sys.argv[1]
    if cmd == 'list':
        scrape_question_list()
    elif cmd == 'pdf':
        scrape_pdf(sys.argv[2])
    else:
        raise RuntimeError('Unknown command %r' % cmd)


if __name__ == '__main__':
    main()
