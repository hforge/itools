# -*- coding: UTF-8 -*-
# Copyright (C) 2002, 2006-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2004 Thierry Fromon <from.t@free.fr>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@oursours.net>
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
from decimal import Decimal
from unittest import TestCase, main
from sys import version_info

# Import from itools
from itools.i18n import is_similar, get_most_similar, guess_language
from itools.i18n import AcceptLanguageType, format_number



############################################################################
# Language negotiation
############################################################################
class QualityAcceptLanguageTestCase(TestCase):

    def setUp(self):
        self.al = AcceptLanguageType.decode("da, en-gb;q=0.8")


    def test_da(self):
        self.assertEqual(self.al.get_quality('da'), (Decimal('1.0'), 0))


    def test_en_gb(self):
        self.assertEqual(self.al.get_quality('en-gb'), (Decimal('0.8'), 0))


    def test_en(self):
        self.assertEqual(self.al.get_quality('en')[0], Decimal('0.0'))


    def test_en_us(self):
        self.assertEqual(self.al.get_quality('en-us')[0], Decimal('0.0'))


    def test_encode(self):
        out = AcceptLanguageType.encode(self.al)
        self.assertEqual(out, "da, en-gb;q=0.8")



class SelectLanguageAcceptLanguageTestCase(TestCase):

    def setUp(self):
        self.al = AcceptLanguageType.decode("pt, en-gb;q=0.8")


    def testNone(self):
        """When none of the languages is acceptable."""
        self.assertEqual(self.al.select_language(['en-us', 'fr']), None)
        self.assertEqual(self.al.select_language(['en-us', 'en']), None)


    def testImplicit(self):
        """When the prefered language is not explictly set."""
        self.assertEqual(self.al.select_language(['fr', 'pt-br']), 'pt-br')


    def testSeveral(self):
        """When there're several accepted languages with the same quality.
        """
        self.assertEqual(self.al.select_language(['pt-br', 'pt']), 'pt')



class ChangeAcceptLanguageTestCase(TestCase):

    def setUp(self):
        self.al = AcceptLanguageType.decode("da, en-gb;q=0.8")


    def testChange(self):
        al = AcceptLanguageType.decode("da, en-gb;q=0.8")
        al.set('es', 5.0)

        self.assertEqual(al.get_quality('es'), (Decimal('5.0'), 0))



############################################################################
# Fuzzy matching
############################################################################
class IsSimilarTestCase(TestCase):

    def test_different(self):
        a = "Good morning"
        b = "How do you do?"
        self.assertEqual(is_similar(a, b), False)


    def test_not_so_far(self):
        a = "Good morning"
        b = "Good afternoon"
        self.assertEqual(is_similar(a, b), False)


    def test_close(self):
        a = "You are wonderful"
        b = "You're wonderful"
        self.assertEqual(is_similar(a, b), True)


    def test_bingo(self):
        a = "In the middle of nowhere"
        b = "In the middle of nowhere"
        self.assertEqual(is_similar(a, b), True)



class MostSimilarTestCase(TestCase):

    database = ['Good morning', 'Good afternoon', 'Good night',
                'This is strange', 'Why not?', 'Freedom as in speak',
                'Where is my cat?', 'It is all about confidence']

    def test_good_evening(self):
        a = 'Good evening'
        most_similar = get_most_similar(a, *self.database)
        self.assertEqual(most_similar, 'Good morning')


    def test_where_is_my_dog(self):
        a = 'Where is my dog?'
        most_similar = get_most_similar(a, *self.database)
        self.assertEqual(most_similar, 'Where is my cat?')


    def test_free_beer(self):
        a = 'Free beer'
        most_similar = get_most_similar(a, *self.database)
        self.assertEqual(most_similar, 'Freedom as in speak')



############################################################################
# Language guessing
############################################################################
class OracleTestCase(TestCase):

    def test_spain_long(self):
        text = u"""Nueva coordinadora de Humanidades. En sustitución de la
        doctora Olga Hansberg, el pasado martes 17 tomó posesión como
        coordinadora de Humanidades de la UNAM la doctora Mari Carmen Serra
        Puche. Con la doctora Serra se inicia un nuevo ciclo del cual se espera
        que las ciencias sociales y las humanidades sean lo que deben ser: la
        inteligencia y el alma de la UNAM.

        En la ceremonia de toma de posesión de la doctora Serra estuvo presente
        el rector Juan Ramón de la Fuente, quien sostuvo que la máxima casa de
        estudios está preparada para enfrentar los nuevos retos que deberá
        enfrentar la institución en la perspectiva de la reforma. La comunidad
        académica tiene plena confianza en que la nueva coordinadora será punto
        de equilibrio y unión para que se produzcan una serie de cambios en
        este subsistema universitario. Por lo pronto y para que no digan que
        no se reconoce hay que decir que las autoridades ya anunciaron que el
        Centro de Estudios sobre la Universidad (CESU) y el Instituto de
        Investigaciones Económicas tendrán nuevas instalaciones, decisión que
        está más que justificada y, repito, se agradece."""
        self.assertEqual(guess_language(text), 'es')


    def test_spain_short(self):
        text = u"""Nueva coordinadora de Humanidades. En sustitución de la
        doctora Olga Hansberg, el pasado martes 17 tomó posesión como
        coordinadora de Humanidades de la UNAM la doctora Mari Carmen Serra
        Puche."""
        self.assertEqual(guess_language(text), 'es')


    def test_spain_very_sort(self):
        text = """Nueva coordinadora de Humanidades."""
        self.assertEqual(guess_language(text), 'es')


    def test_french_long(self):
        text = u"""Le piège de la guerre coloniale se referme sur les
        envahisseurs de lIrak. Comme les troupes françaises embourbées jadis
        en Algérie, les Britanniques au Kenya, les Belges au Congo et les
        Portugais en Guinée-Bissau (voire aujourdhui les Israéliens à Gaza),
        les forces
        américaines constatent que leur écrasante supériorité ne suffit pas à
        leur épargner enlèvements, embuscades et autres attentats mortels Pour
        les soldats sur le terrain, loccupation de lIrak se transforme en une
        descente aux enfers."""
        self.assertEqual(guess_language(text), 'fr')


    def test_french_short(self):
        text = u"""un dossier spécial consacré à la « révolution de velours »
        géorgienne sur le site de lagence Radio Free Europe fondée par le
        Congrès des Etats-Unis."""
        self.assertEqual(guess_language(text), 'fr')


    def test_french_very_sort(self):
        text = u"""Les déclarations du président Vladimir Poutine"""
        self.assertEqual(guess_language(text), 'fr')


    def test_english_long(self):
        text = """INDIA SOFTWARE REVENUE UP: India's revenue from exports of
        software and back-office services grew more than 30 percent during the
        fiscal year ended in March despite a backlash in the United States
        against outsourcing, a trade group said.
        .
        Those revenues rose to $12.5 billion in the latest fiscal year from
        $9.6 billion a year earlier, said Kiran Karnik, president of the
        National Association of Software and Service Companies.
        .
        U.S. companies account for 70 percent of the revenue. Karnik forecast
        growth of 30 percent to 32 percent in the current"""
        self.assertEqual(guess_language(text), 'en')


    def test_english_short(self):
        text = """The French, too, paid much attention to French-German
        reconciliation and interpreted the ceremonies as a celebration of
        European integration and peace."""
        self.assertEqual(guess_language(text), 'en')


    def test_english_very_sort(self):
        text = """But from a cloudless blue sky"""
        self.assertEqual(guess_language(text), 'en')



############################################################################
# Format number
############################################################################
class FormatNumberTestCase(TestCase):
    x = '123456.789'
    accept = AcceptLanguageType.decode('en;q=1.0')


    def test_format_decimal(self):
        x = Decimal(self.x)
        n = format_number(x, accept=self.accept)
        self.assertEqual(n, u"123,456.79")


    def test_format_int(self):
        x = int(float(self.x))
        n = format_number(x, accept=self.accept)
        self.assertEqual(n, u"123,456.00")


    def test_format_float(self):
        x = float(self.x)
        if version_info[:2] == (2, 6):
            self.assertRaises(TypeError, format_number, x)
        else:
            n = format_number(x, accept=self.accept)
            self.assertEqual(n, u"123,456.79")


    def test_format_es(self):
        x = Decimal(self.x)
        accept = AcceptLanguageType.decode('es;q=1.0')
        n = format_number(x, accept=accept)
        self.assertEqual(n, u"123.456,79")


    def test_format_fr(self):
        x = Decimal(self.x)
        accept = AcceptLanguageType.decode('fr;q=1.0')
        n = format_number(x, accept=accept)
        self.assertEqual(n, u"123 456,79")


    def test_places(self):
        x = Decimal(self.x)
        n = format_number(x, places=3, accept=self.accept)
        self.assertEqual(n, u"123,456.789")


    def test_currency(self):
        x = Decimal(self.x)
        n = format_number(x, curr=u"$", accept=self.accept)
        self.assertEqual(n, u"123,456.79$")
        n = format_number(x, curr=u" €", accept=self.accept)
        self.assertEqual(n, u"123,456.79 €")


    def test_sign(self):
        x = Decimal(self.x)
        n = format_number(x, pos=u"+", accept=self.accept)
        self.assertEqual(n, u"+123,456.79")
        x = -x
        n = format_number(x, accept=self.accept)
        self.assertEqual(n, u"-123,456.79")


    def test_sign_currency(self):
        x = -Decimal(self.x)
        n = format_number(x, curr=u"$", accept=self.accept)
        self.assertEqual(n, u"-123,456.79$")



if __name__ == '__main__':
    main()
