from secrets import google_places_key
import plotly.plotly as py
import plotly.graph_objs as go
from bs4 import BeautifulSoup
import requests
import sqlite3
import csv
import json
import sys


DBNAME = 'world_bank.db' # SQLite database
COUNTRIESJSON = 'countries.json' # json data contains countries names and information
CACHE_FNAME = 'WorldBank_data.json' # store the cache files

#[Part 1]######################################################################
# Use cache to avoid sent the same requests many times.
# define functions of API requests that will be used later

try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

# define a function for make requests with caching
def result_from_cache(full_url, params_diction):
    unique_ident = full_url

    if unique_ident in CACHE_DICTION:
        print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    else:
        print("Making a request for new data...")
    # Make the request and cache the new data
        response = requests.get(full_url, params_diction)
        CACHE_DICTION[unique_ident] = json.loads(response.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]

# search for GPS number according to the Alpha2 of country
def get_GPS_of_country(Alpha2):
    result_lst = []

    # search for GPS number according to the name of site we want
    baseurl  = 'http://api.worldbank.org/v2/countries/'
    country_code = Alpha2.lower()
    full_url = baseurl + country_code

    params = {}
    params['format'] = 'json'

    result_dict = result_from_cache(full_url, params)

    Country_name = result_dict[1][0]['name']
    Country_region = result_dict[1][0]['region']['value']
    incomeLevel = result_dict[1][0]['incomeLevel']['value']
    capitalCity = result_dict[1][0]['capitalCity']
    longitude = result_dict[1][0]['longitude']
    latitude = result_dict[1][0]['latitude']

    result_lst = [Country_name, Country_region, incomeLevel, capitalCity, longitude, latitude]

    return result_lst

# search for GDP over 20 years according to the Alpha2 of country
def get_GDP_of_country(Alpha2):
    # indicator : GDP (constant 2010 US$)(NY.GDP.MKTP.KD)
    result_lst = []

    baseurl  = 'http://api.worldbank.org/v2/countries/'
    country_code = Alpha2.lower()
    full_url = baseurl + country_code + '/indicators/NY.GDP.MKTP.KD'
    params = {}
    params['format'] = 'json'
    params['date'] = '1995:2015'

    result_dict = result_from_cache(full_url, params)
    return result_dict

# search for GDP over 20 years according to the Alpha2 of country
def get_GDP_growth_of_country(Alpha2):
    # indicator : GDP growth (annual %)(NY.GDP.MKTP.KD.ZG)

    result_lst = []

    baseurl  = 'http://api.worldbank.org/v2/countries/'
    country_code = Alpha2.lower()
    full_url = baseurl + country_code + '/indicators/NY.GDP.MKTP.KD.ZG'
    params = {}
    params['format'] = 'json'
    params['date'] = '1995:2015'

    result_dict = result_from_cache(full_url, params)
    return result_dict

# search for GNI over 20 years according to the Alpha2 of country
def get_GNI_of_country(Alpha2):
    # indicator :
    # Adjusted net national income per capita (constant 2010 US$)(NY.ADJ.NNTY.PC.KD)
    # Adjusted net national income per capita (current US$)(NY.ADJ.NNTY.PC.CD)
    # Adjusted net national income (annual % growth)(NY.ADJ.NNTY.KD.ZG)
    result_lst = []

    baseurl  = 'http://api.worldbank.org/v2/countries/'
    country_code = Alpha2.lower()
    full_url = baseurl + country_code + '/indicators/NY.ADJ.NNTY.PC.KD'
    params = {}
    params['format'] = 'json'
    params['date'] = '1995:2015'

    result_dict = result_from_cache(full_url, params)
    return result_dict

#[Part 2]######################################################################
# define functions that read data from CSV and JSON into a new database called world_bank.db

# Creates a database called world_bank.db
def create_db():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

    except Error as e:
        print(e)

    drop_table_statement  = '''
        DROP TABLE IF EXISTS 'Data';
        DROP TABLE IF EXISTS 'Countries';
    '''
    cur.executescript(drop_table_statement)

    # create tables
    create_table_statement = '''
    CREATE TABLE 'Data' (
        'Id' INTEGER PRIMARY KEY,
        'Year' INTEGER,
        'Title' TEXT,
        'Value' REAL,
        'CountryId' INTEGER,
        FOREIGN KEY(CountryId) REFERENCES Countries(Id)

    );
    CREATE TABLE 'Countries' (
        'Id' INTEGER PRIMARY KEY,
        'Alpha2' TEXT,
        'Alpha3' TEXT,
        'EnglishName' TEXT,
        'Region' TEXT,
        'Subregion' REAL,
        'Population' INTEGER,
        'IncomeLevel' TEXT,
        'Longitude' REAL,
        'Latitude' REAL
    );

    '''
    cur.executescript(create_table_statement)
    print('db created')
    conn.close()

# insert datas from 'countries.json' and the World Bank API
def populate_db():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    #step 1: write the data from 'countries.json' into db
    with open(COUNTRIESJSON, encoding='utf8') as jsonfile:
        countries_json = json.load(jsonfile)
        for dic in countries_json:
            # insert the value into the table
            insertion_2 = (None, dic['alpha2Code'], dic['alpha3Code'], dic['name'], dic['region'], dic['subregion'], dic['population'], None, None , None)
            statement_2 = """
                INSERT INTO 'Countries'
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cur.execute(statement_2, insertion_2)
            conn.commit()
        print('date inserted from json file')

    #---------------------------------------------
    # step 2: Update the countries data with more information(incomelevel, longitude and latitude)
    # get a list of Alpha2 of countries, and call the function 'get_GPS_of_country()' to get the data.

    lst_a2 = []
    lst_a2_gps = [] # where to save the result from the function "get_GPS_of_country()"
    lst_a2_gdp = [] # where to save the result from the function "get_GDP_of_country()"
    lst_a2_gni = [] # where to save the result from the function "get_GNI_of_country()"
    lst_a2_gdp_growth = [] # where to save the result from the function "get_GNI_of_country()"

    statement_alpha2 = """
        SELECT Alpha2
        FROM Countries
    """
    cur.execute(statement_alpha2) # get all strings of A2 of each country
    conn.commit()

    for row in cur:
        A2 = row[0].lower()
        lst_a2.append(A2)
        try:
            GPS_result = get_GPS_of_country(A2) # get the GPS data of each country by A2
            lst_a2_gps.append((GPS_result[2], GPS_result[4], GPS_result[5], A2.upper()))
        except: # skip the country which don't have data in the API
            continue

    # update the information we get into the table "Countries".
    for ele in lst_a2_gps:
        params = ele
        update = '''
            UPDATE Countries
            SET IncomeLevel = ?,
                Longitude = ?,
                Latitude = ?
            WHERE Alpha2 = ?
        '''
        cur.execute(update, params)
    conn.commit()
    print('GPS data updated')

    #---------------------------------------------
    #step 3: make requests from API to get the information of GDP
    for A2 in lst_a2:
        try:
            GDP_result = get_GDP_of_country(A2) # get the GDP data of each country by A2
            for item in GDP_result[1]:
                if item['value'] != None:
                    lst_a2_gdp.append([item['date'], item['value'] , A2.upper()]) # [year,GDP,A2]
        except: # skip the country which don't have data in the API
            continue
    # change Alpha2 in the list into the countries.Id
    for item in lst_a2_gdp:
        params = (item[2],)
        statement = '''
            SELECT Id
            FROM Countries
            WHERE Alpha2 = ?
        '''
        cur.execute(statement, params)
        result_id = cur.fetchone()[0]
        item[2] = result_id

    # insert the information we get into the table "Data".
    for ele in lst_a2_gdp:
        params = (None, ele[0], 'GDP', ele[1], ele[2])
        statement_gdp = '''
            INSERT INTO 'Data'
            VALUES(?, ?, ?, ?, ?)
        '''
        cur.execute(statement_gdp, params)
    conn.commit()
    print('GDP data updated')
    #---------------------------------------------
    #step 4: make requests from API to get the information of GNI
    for A2 in lst_a2:
        try:
            GNI_result = get_GNI_of_country(A2) # get the GNI data of each country by A2
            for item in GNI_result[1]:
                if item['value'] != None:
                    lst_a2_gni.append([item['date'], item['value'] , A2.upper()]) # [year,GDP,A2]
        except: # skip the country which don't have data in the API
            continue
    # change Alpha2 in the list into the countries.Id
    for item in lst_a2_gni:
        params = (item[2],)
        statement = '''
            SELECT Id
            FROM Countries
            WHERE Alpha2 = ?
        '''
        cur.execute(statement, params)
        result_id = cur.fetchone()[0]
        item[2] = result_id

    # insert the information we get into the table "Data".
    for ele in lst_a2_gni:
        params = (None, ele[0], 'GNI', ele[1], ele[2])
        statement_gni = '''
            INSERT INTO 'Data'
            VALUES(?, ?, ?, ?, ?)
        '''
        cur.execute(statement_gni, params)
    conn.commit()
    print('GNI data updated')

    #---------------------------------------------
    #step 5: make requests from API to get the information of GDP growth
    for A2 in lst_a2:
        try:
            GDP_result = get_GDP_growth_of_country(A2) # get the GDP data of each country by A2
            for item in GDP_result[1]:
                if item['value'] != None:
                    lst_a2_gdp_growth.append([item['date'], item['value'] , A2.upper()]) # [year,GDP,A2]
        except: # skip the country which don't have data in the API
            continue
    # change Alpha2 in the list into the countries.Id
    for item in lst_a2_gdp_growth:
        params = (item[2],)
        statement = '''
            SELECT Id
            FROM Countries
            WHERE Alpha2 = ?
        '''
        cur.execute(statement, params)
        result_id = cur.fetchone()[0]
        item[2] = result_id

    # insert the information we get into the table "Data".
    for ele in lst_a2_gdp_growth:
        params = (None, ele[0], 'GDP_growth', ele[1], ele[2])
        statement_gdp = '''
            INSERT INTO 'Data'
            VALUES(?, ?, ?, ?, ?)
        '''
        cur.execute(statement_gdp, params)
    conn.commit()
    print('GDP_growth data updated')

    #---------------------------------------------
    #step 6: update the incorrect data
    update = '''
        UPDATE 'Data'
        SET Value = 764.029358311631
        WHERE Id = 4509
    '''
    cur.execute(update)
    conn.commit()
    conn.close()

#[Part 3]######################################################################
# define functions that can create different charts by using Plotly

#<<<< get the targeted data of a country from db >
def get_data_for_one(alpha2 = 'AF', title = 'GDP'):
    # params: country code 'Alpha2' and the 'title' of data
    # return: result_dic
    result_dic = {}
    result_lst = [] # store the result (Year, Value)
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    insert = (alpha2, title)

    statement = 'SELECT Year, Value, EnglishName '
    statement += 'FROM Data '
    statement += 'JOIN Countries '
    statement += 'ON countries.Id = [Data].CountryId '
    statement += 'WHERE alpha2 = ? AND Title = ? '
    statement += 'ORDER BY Year ASC'

    cur.execute(statement, insert)
    for row in cur:
        result_lst.append((row[0], round(row[1],2)))
        C_Name = row[2]

    conn.close()
    result_dic['title'] = title
    result_dic['Name'] = C_Name
    result_dic['value'] = result_lst

    return result_dic
#print(get_data_for_one())

#<<<<< plot a line chart of a country >
def plot_for_one(result_dic):
    dic_title = result_dic['title']
    dic_name = result_dic['Name']

    if dic_title == 'GNI':
        f_name = 'GNI' + ' of ' + dic_name
        full_title = 'Adjusted net national income per capita (constant 2010 US$)' + ' of ' + dic_name
    if dic_title == 'GDP_growth':
        f_name = 'GDP_growth' + ' of ' + dic_name
        full_title = 'GDP growth (annual %)' + ' of ' + dic_name
    else:
        f_name = 'GDP' + ' of ' + dic_name
        full_title = 'GDP (constant 2010 US$)' + ' of ' + dic_name

    lst_year = []
    lst_value = []
    for i in result_dic['value']:
        lst_year.append(i[0])
        lst_value.append(i[1])

    trace = go.Scatter(
    x = lst_year,
    y = lst_value,

    name = f_name, # Style name/legend entry with html tags
    connectgaps=True,
        line = dict(
        color = ('rgb(205, 12, 24)'),
        width = 4)
    )

    data = [trace]

    layout = dict(title = full_title,
              xaxis = dict(title = 'Year'),
              yaxis = dict(title = 'Value'),
              )

    fig = dict(data=data, layout=layout)
    py.plot(fig, filename = f_name)
#plot_for_one(get_data_for_one('CA', 'GDP_growth'))

#----------------------------------------
#<<<< get the targeted data in a year of all country from db >
def get_data_for_all(title = 'GDP', year = 2000):
    # params: 'title' of data and a year (within 1995 to 2015)
    # return: result_dic
    result_dic = {}
    result_lst = [] # store the result (IncomeLevel, Value, EnglishName, Alpha3)
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    insert = (title, year)

    statement = 'SELECT IncomeLevel, Value, EnglishName, Alpha3 '
    statement += 'FROM Data '
    statement += 'JOIN Countries '
    statement += 'ON countries.Id = [Data].CountryId '
    statement += 'WHERE Title = ? AND Year = ?'
    # statement += 'LIMIT 10'

    cur.execute(statement, insert)
    for row in cur:
        result_lst.append((row[0], round(row[1],2), row[2], row[3]))

    conn.close()
    result_dic['title'] = title
    result_dic['year'] = year
    result_dic['value'] = result_lst

    return result_dic
#print(get_data_for_all())

#<<<<< plot a line chart of a country in a year>
def plot_for_all(result_dic):
    title = result_dic['title']
    target_year = result_dic['year']
    result_lst = result_dic['value']

    lst_alpha3 = []
    lst_name = []
    lst_value = []

    for lst in result_lst:
        lst_alpha3.append(lst[3])
        lst_name.append(lst[2])
        if title == 'GNI' :
            full_title = 'Adjusted net national income per capita (constant 2010 US$)'
            lst_value.append(round(lst[1],0))
            scale = 'k = thousand'

        if title == 'GDP' :
            full_title = 'GDP (constant 2010 US$)'
            lst_value.append(round(lst[1]/1000000000,2))
            scale = 'Billion (k = thousand)'


    full_title = full_title + ' in ' + str(target_year)
    data = [ dict(
            type = 'choropleth',
            locations = lst_alpha3,
            z = lst_value,
            text = lst_name,
            colorscale = [[0,"rgb(5, 10, 172)"],[0.35,"rgb(40, 60, 190)"],[0.5,"rgb(70, 100, 245)"],\
            [0.6,"rgb(90, 120, 245)"],[0.7,"rgb(106, 137, 247)"],[1,"rgb(220, 220, 220)"]],
            autocolorscale = False,
            reversescale = True,
            marker = dict(
                line = dict (
                    color = 'rgb(180,180,180)',
                    width = 0.5
                ) ),
            colorbar = dict(
                autotick = False,
                tickprefix = '$',
                title = scale),

          ) ]


    layout = dict(
        title = full_title,
        geo = dict(
            showframe = False,
            showcoastlines = False,
            projection = dict(type = 'Mercator')
        )
    )

    fig = dict( data=data, layout=layout )
    py.plot( fig, validate=False, filename=full_title )
#plot_for_all(get_data_for_all(title = 'GNI'))

#[Part 4]######################################################################
# Part 4: Implement logic to process user commands

# this is where to decide which command runs according to the user input
def process_command(command):
    pass

def load_help_text():
    with open('help.txt') as f:
        return f.read()

########################################################################
# Part 3: Implement interactive prompt. We've started for you!
def interactive_prompt():
    pass
    # help_text = load_help_text()
    # response = ''
    # while response != 'exit':
    #     response = input('Enter a command: ')
    #     response = response.strip()
    #
    #     if response == 'exit':
    #         print("bye")
    #         break
    #
    #     if response == 'help':
    #         print(help_text)
    #         continue

# data of country_code
# http://www.nationsonline.org/oneworld/country_code_list.htm


# Make sure nothing runs or prints out when this file is run as a module
if __name__=="__main__":
    pass
    # create_db()
    # populate_db()
    #interactive_prompt()
