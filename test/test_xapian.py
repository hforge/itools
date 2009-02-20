# -*- coding: UTF-8 -*-
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
from datetime import date
from random import sample
import unittest
from unittest import TestCase
import re

# Import from itools
from itools import vfs
from itools.xapian import make_catalog, Catalog, CatalogAware, StartQuery
from itools.xapian import AndQuery, RangeQuery, PhraseQuery, NotQuery
from itools.datatypes import String, Unicode, Boolean, Integer
from itools.xapian.catalog import _index, _decode

# Import from xapian
from xapian import Document as XapianDocument



def split(field_cls, value):
    xdoc = XapianDocument()
    _index(xdoc, field_cls, value, '')
    words = []
    for term_list_item in xdoc:
        if issubclass(field_cls, Unicode):
            term = unicode(term_list_item.term, 'utf-8')
        else:
            term = term_list_item.term
        for termpos in term_list_item.positer:
            words.append((termpos, term))
    words.sort()
    words = [ word[1] for word in words ]

    return words



class FieldsTestCase(TestCase):

    def test_boolean_true(self):
        words = split(Boolean, True)
        self.assertEqual(words, ['1'])


    def test_boolean_false(self):
        words = split(Boolean, False)
        self.assertEqual(words, ['0'])


    def test_string(self):
        value = 'Hello World'
        words = split(String, value)

        self.assertEqual(words, ['Hello World'])


    def test_integer(self):
        for value in sample(xrange(1000000000), 255):
            words = split(Integer, value)
            self.assertEqual(len(words), 1)
            word = words[0]
            self.assertEqual(type(word), str)
            self.assertEqual(_decode(Integer, word), value)

    def test_unicode(self):
        value = (u'Celle-ci consiste dans les differents Privileges, dont'
                 u' quelques-uns jouissent, au préjudice des autres,')
        expected = [u'celle', u'ci', u'consiste', u'dans', u'les',
            u'differents', u'privileges', u'dont', u'quelques', u'uns',
            u'jouissent', u'au', u'préjudice', u'des', u'autres']

        words = split(Unicode, {'fr': value})
        self.assertEqual(words, expected)


    def test_text_russian(self):
        text = u'Это наш дом'
        words = split(Unicode, {'ru': text})
        self.assertEqual(words, [u'это', u'наш',  u'дом'])


    def test_text_cjk(self):
        text = u'東京都ルパン上映時間'
        expected = [u'東京', u'京都', u'都ル', u'ルパ', u'パン',
                    u'ン上', u'上映', u'映時', u'時間']

        words = split(Unicode, {'ja': text})
        self.assertEqual(words, expected)

        text = u'東京'
        expected = [u'東京']

        words = split(Unicode, {'ja': text})
        self.assertEqual(words, expected)

        text = u'東京      '
        expected = [u'東京']

        words = split(Unicode, {'ja': text})
        self.assertEqual(words, expected)

        text = u'会議室を出る時、エアコンを消しましたか。'
        expected = [u'会議', u'議室', u'室を', u'を出', u'出る',
                    u'る時', u'エア', u'アコ', u'コン',
                    u'ンを', u'を消', u'消し', u'しま', u'まし',
                    u'した', u'たか']

        words = split(Unicode, {'ja': text})
        self.assertEqual(words, expected)

        text = (u'처음 계획에 의하면, 웸블리 스타디움은 '
                u'2000년 크리스마스 ')
        expected = [u'처음', u'계획에', u'의하면', u'웸블리', u'스타디움은',
                    u'2000년', u'크리스마스']

        words = split(Unicode, {'ko': text})
        self.assertEqual(words, expected)

        # FIXME regression
        # This test is broken because _index_cjk function
        # does not handle correctly cjk and ASCI content anymore.
        #text = u'法国空中客车总部（A380，A330及A340）'
        #expected = [u'法国', u'国空', u'空中', u'中客', u'客车', u'车总',
        #            u'总部', u'a380', u'a330及a340']

        #words = split(Unicode, {'ja': text})
        #self.assertEqual(words, expected)


    # FIXME regression
    # This test is broken because
    # 1) _index_cjk function does not handle correctly cjk and ASCI content
    # anymore.
    # 2) Xapian does not handle correctly cjk punctuation.
    #def test_text_cjk_english(self):
    #    # english
    #    text = (u'For example, "Can\'t Buy Me Love" becomes'
    #            u'「キャント・バイ・ミー・ラヴ」 (Kyanto·bai·mī·ravu).')
    #    expected = [u'for', u'example', u'can', u't', u'buy', u'me', u'love',
    #                u'becomes', u'キャ', u'ャン', u'ント', u'バイ', u'ミー',
    #                u'ラヴ', u'kyanto', u'bai', u'mī', u'ravu']

    #    words = split(Unicode, {'en': text})
    #    self.assertEqual(words, expected)

    #    # japanese
    #    text = (u'For example, "Can\'t Buy Me Love" becomes'
    #            u'「キャント・バイ・ミー・ラヴ」 (Kyanto·bai·mī·ravu).')
    #    expected = [u'for', u'example', u'can', u't', u'buy', u'me', u'love',
    #                u'becomes', u'キャ', u'ャン', u'ント', u'バイ', u'ミー',
    #                u'ラヴ', u'kyanto', u'bai', u'mī', u'ravu']

    #    words = split(Unicode, {'ja': text})
    #    self.assertEqual(words, expected)

    #    # english
    #    text = (u'that "東" means "East" and "北" means "North", '
    #            u'"南" means "South" and "西" "West". That '
    #            u'"関西地方 Kansai-chihō" means Kansai region.')
    #    expected = [u'that', u'東', u'means', u'east', u'and', u'北',
    #                u'means', u'north', u'南', u'means', u'south',
    #                u'and', u'西', u'west', u'that', u'関西地方',
    #                u'kansai', u'chihō', u'means', u'kansai', u'region']

    #    words = split(Unicode, {'en': text})
    #    self.assertEqual(words, expected)

    #    # japanese
    #    text = (u'that "東" means "East" and "北" means "North", '
    #            u'"南" means "South" and "西" "West". That '
    #            u'"関西地方 Kansai-chihō" means Kansai region.')
    #    expected = [u'that', u'東', u'means', u'east', u'and', u'北',
    #                u'means', u'north', u'南', u'means', u'south',
    #                u'and', u'西', u'west', u'that', u'関西',
    #                u'西地', u'地方', u'kansai', u'chihō', u'means',
    #                u'kansai', u'region']

    #    words = split(Unicode, {'ja': text})
    #    self.assertEqual(words, expected)

    #    text = u'East equals 東'
    #    expected = [u'east', u'equals', u'東']

    #    words = split(Unicode, {'ja': text})
    #    self.assertEqual(words, expected)

    #    text = u'East equals 東.'
    #    expected = [u'east', u'equals', u'東']

    #    words = split(Unicode, {'ja': text})
    #    self.assertEqual(words, expected)

    #    text = u'East equals 東。'
    #    expected = [u'east', u'equals', u'東']

    #    words = split(Unicode, {'ja': text})
    #    self.assertEqual(words, expected)

    #    # hangul
    #    text = u'웸블리 경기장(영어: Wembley Stadium)은 영국 런던 웸블리에'
    #    expected = [u'웸블리', u'경기장', u'영어', u'wembley', u'stadium',
    #                u'은', u'영국', u'런던', u'웸블리에']

    #    words = split(Unicode, {'ko': text})
    #    self.assertEqual(words, expected)

    #    text = (u'예를 들면 Paris-Roubaix, Tour of Flanders, '
    #            u'Liege Bastogne-Liege 등이다.')
    #    expected = [u'예를', u'들면', u'paris', u'roubaix', u'tour',
    #                u'of', u'flanders', u'liege', u'bastogne',
    #                u'liege', u'등이다']

    #    words = split(Unicode, {'ko': text})
    #    self.assertEqual(words, expected)

    #    # chinese
    #    text = (u'首頁 arrow English Version .... 2008 '
    #            u'東吳大學GIS技術支援中心.')
    #    expected = [u'首頁', u'arrow', u'english', u'version', u'2008',
    #                u'東吳', u'吳大', u'大學', u'學g', u'gi', u'is', u's技',
    #                u'技術', u'術支', u'支援', u'援中', u'中心']

    #    words = split(Unicode, {'zh': text})
    #    self.assertEqual(words, expected)


    # FIXME regression
    # Xapian does not handle correctly cjk punctuation.
    # here -> 〰; 〤; 〴; 〇
    #def test_text_cjk_stop_words(self):
    #    text = (u'파리〃(프랑스어: Paris, 문〈화어: 빠리)는 프랑스「의 '
    #            u'수도로, 프랑스 북부 일』드 프랑스 지방의 중〒앙에 있다. '
    #            u'센 강 중류〰에 있으며, 면적은 105㎢. 인구〤는 1999년 '
    #            u'기준〴으로 213만 명이다. 파리？시의 행정 구역》은 '
    #            u'1~20구로 나뉘어〇있다.')

    #    expected = [u'파리', u'프랑스어', u'paris', u'문', u'화어',
    #                u'빠리', u'는', u'프랑스', u'의', u'수도로',
    #                u'프랑스', u'북부', u'일', u'드', u'프랑스',
    #                u'지방의', u'중', u'앙에', u'있다', u'센', u'강',
    #                u'중류', u'에', u'있으며', u'면적은', u'105',
    #                u'인구', u'는', u'1999년', u'기준', u'으로',
    #                u'213만', u'명이다', u'파리', u'시의', u'행정',
    #                u'구역', u'은', u'1', u'20구로', u'나뉘어',
    #                u'있다']

    #    words = split(Unicode, {'ko': text})
    #    self.assertEqual(words, expected)


class CatalogTestCase(TestCase):

    def setUp(self):
        # Make the catalog
        catalog = make_catalog('tests/catalog', Document.fields)
        # Index
        fables = vfs.open('fables')
        for name in fables.get_names():
            uri = fables.get_reference().resolve2(name)
            document = Document(uri)
            catalog.index_document(document)
        # Save
        catalog.save_changes()


    def tearDown(self):
        vfs.remove('tests/catalog')


    def test_everything(self):
        catalog = Catalog('tests/catalog', Document.fields)
        # Simple Search, hit
        results = catalog.search(data=u'lion')
        self.assertEqual(len(results), 4)
        documents = [ x.name for x in results.get_documents(sort_by='name') ]
        self.assertEqual(documents, ['03.txt', '08.txt', '10.txt', '23.txt'])
        # Simple Search, miss
        self.assertEqual(len(catalog.search(data=u'tiger')), 0)
        # Unindex, Search, Abort, Search
        catalog.unindex_document('03.txt')
        results = catalog.search(data=u'lion')
        self.assertEqual(len(catalog.search(data=u'lion')), 3)
        catalog.abort_changes()
        self.assertEqual(len(catalog.search(data=u'lion')), 4)
        # Query on indexed boolean
        self.assertEqual(len(catalog.search(about_wolf=True)), 5)
        # Query on stored boolean
        results = catalog.search(about_wolf=True)
        longer_stories = 0
        for result in results.get_documents():
            if result.is_long:
                longer_stories += 1
        self.assertEqual(longer_stories, 0)
        # Phrase Query
        results = catalog.search(data=u'this is a double death')
        self.assertEqual(len(results), 1)
        # Range Query
        query = RangeQuery('name', '03.txt', '06.txt')
        results = catalog.search(query)
        self.assertEqual(len(results), 4)
        # Not Query (1/2)
        query = NotQuery(PhraseQuery('data', 'lion'))
        results = catalog.search(query)
        self.assertEqual(len(results), 27)
        # Not Query (2/2)
        query1 = PhraseQuery('data', 'mouse')
        query2 = NotQuery(PhraseQuery('data', 'lion'))
        query = AndQuery(query1, query2)
        results = catalog.search(query)
        self.assertEqual(len(results), 2)


    def test_unique_values(self):
        catalog = Catalog('tests/catalog', Document.fields)
        values = catalog.get_unique_values('title')
        self.assert_('pearl' in values)
        self.assert_('motorola' not in values)



class UnicodeTestCase(TestCase):

    def test_everything(self):

        # In memory catalog
        cat = make_catalog(None, Document_2.fields)

        # Some data
        cat.index_document(Document_2(1, u'foo à €'))
        cat.index_document(Document_2(2, u'aabà'))
        cat.index_document(Document_2(3, u'aabàà'))
        cat.index_document(Document_2(4, u'aac'))

        # A simple search
        self.assertEqual(len(cat.search(data=u'à')),1)

        # Start
        q = StartQuery('data', u'aabà')
        r = [ doc.id for doc in cat.search(q).get_documents() ]
        self.assertEqual(r, [2, 3])



class Document(CatalogAware):

    fields = {'name': String(is_key_field=True, is_stored=True,
                             is_indexed=True),
              'title': Unicode(is_stored=True, is_indexed=True),
              'data': Unicode(is_indexed=True),
              'size': Integer(is_indexed=True),
              'about_wolf': Boolean(is_indexed=True),
              'is_long': Boolean(is_indexed=False, is_stored=True)}


    def __init__(self, uri):
        self.uri = uri


    def get_catalog_values(self):
        data = vfs.open(self.uri).read()

        indexes = {}
        indexes['name'] = self.uri.path[-1]
        indexes['title'] = data.splitlines()[0]
        indexes['data'] = data
        indexes['size'] = len(data)
        indexes['about_wolf'] = re.search('wolf', data, re.I) is not None
        indexes['is_long'] = len(data) > 1024
        return indexes



class Document_2(CatalogAware):

    fields = {'id': Integer(is_key_field=True, is_stored=True,
                            is_indexed=True),
              'data': Unicode(is_stored=True, is_indexed=True)}


    def __init__(self, id, data):
        self.id = id
        self.data = data


    def get_catalog_values(self):
        return {'id': self.id, 'data': self.data}



if __name__ == '__main__':
    unittest.main()
