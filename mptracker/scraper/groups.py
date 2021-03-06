from collections import namedtuple
from pyquery import PyQuery as pq
from mptracker.scraper.common import (Scraper, url_args, GenericModel,
                                      parse_profile_url, parse_date)


Interval = namedtuple('Interval', ['start', 'end', 'group'])


class Group(GenericModel):

    def __repr__(self):
        return "<Group {s.short_name}>".format(s=self)


class Member(GenericModel):

    def get_interval(self):
        return Interval(self.start_date, self.end_date, self.group)


class GroupScraper(Scraper):

    index_url = 'http://www.cdep.ro/pls/parlam/structura.gp'

    def fetch(self):
        index_page = self.fetch_url(self.index_url)
        headline = index_page.find('td.headline')
        parent_table = pq(headline.parents('table')[-2])
        table = list(parent_table.items('table'))[-1]

        url_set = set()
        for link in table.items('tr > td > b > a'):
            url_set.add(link.attr('href'))

        for url in sorted(url_set):
            yield self.fetch_group(url)

    def fetch_group(self, group_url):
        group_page = self.fetch_url(group_url)
        headline = group_page.find('td.headline')
        parent_td = pq(headline.parents('td')[-1])
        mp_tables = list(parent_td.items('table table'))
        short_name = group_page.find('.cale2').text().split('>')[-1].strip()

        group = Group(
            is_independent=False,
            current_members=[],
            former_members=[],
            name=headline.text(),
            short_name=short_name,
        )

        idg = url_args(group_url).get('idg', type=int)
        if idg == 0:
            # group of unaffiliated MPs
            group.is_independent = True
            group.short_name = "Indep."
            group.current_members.extend(
                self.fetch_current_independent_members(mp_tables[0]))

        else:
            group.current_members.extend(
                self.fetch_current_members(mp_tables[0]))

            if len(mp_tables) > 1:
                group.former_members.extend(
                    self.fetch_former_members(mp_tables[-1]))

        for member in group.current_members + group.former_members:
            member.group = group

        return group

    def fetch_current_independent_members(self, table):
        rows = list(table.items('tr'))
        cols = {k: n for n, k in enumerate(self.parse_cols(rows[0]))}
        for row in rows[1:]:
            row_children = row.children()
            name_link = row_children.eq(cols['person']).find('a')

            member = Member(
                mp_name=name_link.text(),
                mp_ident=parse_profile_url(name_link.attr('href')),
                start_date=None,
                end_date=None,
            )

            yield member

    def parse_cols(self, row):
        names = {
            "Funcţia": 'title',
            "Nume şi prenume": 'person',
            "Membru din": 'start_date',
            "Membru până": 'end_date',
        }
        for col in row.items('td'):
            yield names.get(col.text(), '??')

    def fetch_current_members(self, table):
        current_title = None
        rows = list(table.items('tr'))
        cols = {k: n for n, k in enumerate(self.parse_cols(rows[0]))}
        for row in rows[1:]:
            row_children = row.children()
            next_title = row_children.eq(cols['title']).text()
            if next_title:
                current_title = next_title
            name_link = row_children.eq(cols['person']).find('a')

            member = Member(
                title=current_title,
                mp_name=name_link.text(),
                mp_ident=parse_profile_url(name_link.attr('href')),
                start_date=None,
                end_date=None,
            )

            if 'start_date' in cols:
                date_txt = row_children.eq(cols['start_date']).text()
                if date_txt:
                    member.start_date = parse_date(date_txt)

            yield member

    def fetch_former_members(self, table):
        rows = list(table.items('tr'))
        cols = {k: n for n, k in enumerate(self.parse_cols(rows[0]))}
        for row in rows[1:]:
            row_children = row.children()
            name_link = row_children.eq(cols['person']).find('a')

            member = Member(
                mp_name=name_link.text(),
                mp_ident=parse_profile_url(name_link.attr('href')),
                start_date=None,
                end_date=parse_date(row_children.eq(cols['end_date']).text()),
            )

            if 'start_date' in cols:
                start_txt = row_children.eq(cols['start_date']).text()
                if start_txt:
                    member.start_date = parse_date(start_txt)

            yield member
