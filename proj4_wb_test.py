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

class Get_Data_Search_one(unittest.TestCase):

    def test_get_data_for_one(self):
        results = get_data_for_one('CA','GDP')
        self.assertEqual(results['Name'], 'Canada')

        results = get_data_for_one('LY','gdp_growth')
        self.assertEqual(results['title'], 'gdp_growth')

        results = get_data_for_one('TW','GNI')
        self.assertEqual(results['value'], [])


        results = get_data_for_one('TR','GDP')
        self.assertEqual(results['value'][0][0], 1995)

class Get_Data_Search_all(unittest.TestCase):
    def test_get_data_for_all(self):
        results = get_data_for_all('GDP' , 2011)
        self.assertEqual(results['title'], 'GDP')

        results = get_data_for_all('GNI' , 1995)
        self.assertTrue(results['year'],  1995)

        results = get_data_for_all('GDP' , 2014)
        self.assertEqual(len(results['value'][0][3]), 3)

        results = get_data_for_all('GNI' , 1999)
        self.assertLessEqual(len(results['value']), 250)

unittest.main()
