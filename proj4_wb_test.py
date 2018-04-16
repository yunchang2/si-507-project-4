import unittest
from proj4_wb import *

# proj4_wb_test.py

class TestDatabase(unittest.TestCase):

    def test_data_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = 'SELECT DISTINCT Year FROM Data'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn((2010,), result_list)
        self.assertEqual(len(result_list), 21)

        sql = '''
            SELECT Year, Title, Value, CountryId
            FROM Data
            WHERE Title="GNI" AND CountryId = 43
            ORDER BY Year DESC
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        #print(result_list)
        self.assertEqual(len(result_list), 21)
        self.assertEqual(result_list[3][0], 2012)

        conn.close()

    def test_country_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT EnglishName
            FROM Countries
            WHERE Region="Americas"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Canada',), result_list)
        self.assertEqual(len(result_list), 57)

        sql = '''
            SELECT COUNT(*)
            FROM Countries
        '''
        results = cur.execute(sql)
        count = results.fetchone()[0]
        self.assertEqual(count, 250)

        conn.close()

    def test_joins(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT Value
            FROM Data
                JOIN Countries
                ON Countries.Id=Data.CountryId
            WHERE Alpha2 ="BR"
                AND Year= 2000
        '''
        results = cur.execute(sql)
        result_list = results.fetchone()
        self.assertEqual(result_list[0], 1538707417435.78)
        conn.close()

# class TestBarSearch(unittest.TestCase):
#
#     def test_bar_search(self):
#         results = process_command('bars ratings top=1')
#         self.assertEqual(results[0][0], 'Chuao')
#
#         results = process_command('bars cocoa bottom=10')
#         self.assertEqual(results[0][0], 'Guadeloupe')
#
#         results = process_command('bars sellcountry=CA ratings top=5')
#         self.assertEqual(results[0][3], 4.0)
#
#         results = process_command('bars sourceregion=Africa ratings top=5')
#         self.assertEqual(results[0][3], 4.0)

# class TestCompanySearch(unittest.TestCase):
#
#     def test_company_search(self):
#         results = process_command('companies region=Europe ratings top=5')
#         self.assertEqual(results[1][0], 'Idilio (Felchlin)')
#
#         results = process_command('companies country=US bars_sold top=5')
#         self.assertTrue(results[0][0] == 'Fresco' and results[0][2] == 26)
#
#         results = process_command('companies cocoa top=5')
#         self.assertEqual(results[0][0], 'Videri')
#         self.assertGreater(results[0][2], 0.79)
#
# class TestCountrySearch(unittest.TestCase):
#
#     def test_country_search(self):
#         results = process_command('countries sources ratings bottom=5')
#         self.assertEqual(results[1][0],'Uganda')
#
#         results = process_command('countries sellers bars_sold top=5')
#         self.assertEqual(results[0][2], 764)
#         self.assertEqual(results[1][0], 'France')
#
# class TestRegionSearch(unittest.TestCase):
#
#     def test_region_search(self):
#         results = process_command('regions sources bars_sold top=5')
#         self.assertEqual(results[0][0], 'Americas')
#         self.assertEqual(results[3][1], 66)
#         self.assertEqual(len(results), 4)
#
#         results = process_command('regions sellers ratings top=10')
#         self.assertEqual(len(results), 5)
#         self.assertEqual(results[0][0], 'Oceania')
#         self.assertGreater(results[3][1], 3.0)

unittest.main()
