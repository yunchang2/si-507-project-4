from secrets import *
import plotly.plotly as py
import plotly.graph_objs as go
from bs4 import BeautifulSoup
import webbrowser
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
        #print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    else:
        #print("Making a request for new data...")
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
def get_data_for_one(alpha2, title):
    # params: country code 'Alpha2' and the 'title' of data
    # return: result_dic
    C_Name = None
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
#print(get_data_for_one('CA','GDP'))

#<<<<< plot a line chart of a country >
def plot_for_one(result_dic):
    dic_value = result_dic['value']
    dic_title = result_dic['title']
    dic_name = result_dic['Name']

    if dic_title == 'GNI':
        f_name = 'GNI' + ' of ' + dic_name
        full_title = 'Adjusted net national income per capita (constant 2010 US$)' + ' of ' + dic_name

    elif dic_title == 'GDP_growth':
        f_name = 'GDP_growth' + ' of ' + dic_name
        full_title = 'GDP growth (annual %)' + ' of ' + dic_name

    elif dic_title == 'GDP':
        f_name = 'GDP' + ' of ' + dic_name
        full_title = 'GDP (constant 2010 US$)' + ' of ' + dic_name

    else:
        return ("Error in plotting for one country")

    lst_year = []
    lst_value = []


    for i in dic_value:
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
    py.plot(fig, filename = dic_title)

# result = get_data_for_one('EG', 'GNI')
# plot_for_one(result)

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

        elif title == 'GDP' :
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
#plot_for_all(get_data_for_all(title = 'GNI', year = 2015))

#[Part 4]######################################################################
# perform web scraping from the Financial Times website
# get the recent headline of news of a country

def get_FTimes_page(Alpha2):
    # change the two-letter Alpha2 to the country name
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    params = (Alpha2 ,)
    statement = '''
        SELECT EnglishName
        FROM Countries
        WHERE Alpha2 = ?
    '''
    cur.execute(statement, params)
    result_name = cur.fetchone()[0]
    # ---------financial time web scraping
    baseurl = 'https://www.ft.com'
    catalog_url = baseurl + '/search'
    query = {'q': result_name} # use the country name to search for a news
    page_text = requests.get(catalog_url, params = query).text

    page_soup = BeautifulSoup(page_text, 'html.parser')
    # print(page_soup.prettify().encode(sys.stdin.encoding, "replace").decode(sys.stdin.encoding))

    content_headline = page_soup.find_all(class_='o-teaser__heading')
    # print(len(content_headline))

    num = 1
    for tr in content_headline[0:10]: # only get top 10 news
        details_url = tr.find('a')['href']
        print(num, '.', tr.text.strip())
        print(baseurl + details_url)
        num += 1
        print('-'*20)
    # ---------financial time web scraping
#get_FTimes_page('US')

#[Part 5]######################################################################
# define a function for make requests from flickr API
# to get the photos from Flickr of a country

# get the ids of photos that contains the country name as tag
def  get_flickr_data(Alpha2, tag_for_search = 'National flag'):
    lst_photo_id = []
    # change the two-letter Alpha2 to the country name
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    params = (Alpha2 ,)
    statement = '''
        SELECT EnglishName
        FROM Countries
        WHERE Alpha2 = ?
    '''
    cur.execute(statement, params)
    tag = cur.fetchone()[0]

    baseurl = "https://api.flickr.com/services/rest/"
    params_diction = {}
    params_diction["api_key"] = FLICKR_KEY
    params_diction["tags"] = tag + ', ' + tag_for_search
    params_diction["per_page"] = 10
    params_diction["tag_mode"] = "all"
    params_diction["method"] = "flickr.photos.search"
    params_diction["format"] = "json"

    unique_ident = "https://api.flickr.com/services/rest/" + tag

    if unique_ident in CACHE_DICTION:
        #print("Getting cached data...")
        result = CACHE_DICTION[unique_ident]
    else:
        #print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(baseurl, params_diction)
        flickr_text = resp.text
        flickr_text_fixed = flickr_text[14:-1]
        CACHE_DICTION[unique_ident] = json.loads(flickr_text_fixed)

        dumped_json_cache= json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        result = CACHE_DICTION[unique_ident]

    for i in result['photos']['photo']:
        lst_photo_id.append(i['id'])
    return(lst_photo_id)

# use the id of a photo to search for its URL
def  get_flickr_photo_info(id_num, tag):
    baseurl = "https://api.flickr.com/services/rest/"
    params_diction = {}
    params_diction["api_key"] = FLICKR_KEY
    params_diction["photo_id"] = id_num
    params_diction["method"] = "flickr.photos.getInfo"
    params_diction["format"] = "json"

    unique_ident = baseurl + id_num + tag

    if unique_ident in CACHE_DICTION:
        #print("Getting cached data...")
        result =  CACHE_DICTION[unique_ident]
    else:
        #print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(baseurl, params_diction)
        flickr_text = resp.text
        flickr_text_fixed = flickr_text[14:-1]
        CACHE_DICTION[unique_ident] = json.loads(flickr_text_fixed)

        dumped_json_cache= json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        result =  CACHE_DICTION[unique_ident]
    photo_url = result['photo']['urls']['url'][0]['_content']
    return(photo_url)

# lst_US = get_flickr_data('US')
# for i in lst_US:
#     print(get_flickr_photo_info(i, 'university of michigan'))


#[Part 6]######################################################################
# Part 6: Implement logic to process user commands

#-------------the function for supporting the users

def get_lst_a2(): # get a list contains the 2-letter alpha2 codes of all countries
    lst_a2 = []
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement_alpha2 = """
        SELECT Alpha2
        FROM Countries
    """
    cur.execute(statement_alpha2) # get all strings of A2 of each country
    conn.commit()

    for row in cur:
        A2 = row[0].lower()
        lst_a2.append(A2)
    conn.close()
    return lst_a2

def open_web_code():
    webbrowser.open_new('https://www.worldatlas.com/aatlas/ctycodes.htm')

def load_help_text():
    with open('help.txt') as f:
        return f.read()

#-------------the function only print
def print_command_main():
    print("============[Home]============")
    print("a. Search for Economic Data of countries.")
    print("b. Search for Financial Time news of a country.")
    print("c. Search for Flicker photos of a country.")
    print(' ')
    print("Please enter a/b/c/code/help/exit to choose the function you want to use.")

def print_command_2():
    print(' ')
    print("==========[Economic charts]===========")
    print('Welcome to search for the economic data from the World Bank database.')
    print('-'*10)
    print('You can see two types of charts of economic data here.')
    print('The first type is line chart. The second type is world map.')
    print('-'*10)
    print('The economic data are three types: GDP/GNI/GDP_growth.')
    print("The available data starts from 1995 to 2015. Some countries don't have complete data.")
    print('-'*10)
    print('The command "back" allows you to go back to [Home].')
    print('If you have any question, please enter "help" to see more detailed info.')
    print(' ')

def print_command_3():
    print(' ')
    print("==========[Financial times news search]===========")
    print('Welcome to search for news of a coutry in Financial Times!')
    print('-'*10)
    print('You can search for latest ten news in FTimes website regarding to the country you want to look for.')
    print('There is only one input for the search.')
    print('-'*10)
    print('Just enter a two-leter country code.')
    print('-'*10)
    print('Besides, the command "back" allows you to go back to [Home].')
    print(' ')

def print_command_4():
    print(' ')
    print("==========[Flicker Photo search]===========")
    print('Welcome to search for the Photos in Flicker!')
    print('-'*10)
    print('You can search for ten photos of a country that have a tag you want.')
    print('There are two user input for the search.')
    print('-'*10)
    print('First, enter a two-leter country code.')
    print('Second, enter the tag you want for the photo. For example, you can enter "National Flag" as a tag.')
    print('-'*10)
    print('The command "back" allows you to go back to [Home].')
    print(' ')

#-------------the function for running the commands
def command_econ():
    response_econ = ''
    lst_a2 = get_lst_a2()
    first_enter = True
    if first_enter == True:
        print_command_2()
        first_enter = False

    while response_econ != 'back':
        print('-'*20)
        print(' ')
        print("==========[Economic charts]===========")
        print(' ')
        print("a. Get a line chart of a country's GDP/GNI/GDP_growth from 1995 to 2015.")
        print("b. Get the world map of GDP/GNI of all countries at a specific year.")
        print(' ')
        print("Please enter a/b/code/help/back to choose the function you want to use.")
        print(' ')
        response_econ = input('Enter a command (a/b/code/help/back): ')
        response_econ = response_econ.strip()
        print(' ')

        if response_econ == "code":
            open_web_code()
            continue

        if response_econ == 'help': # open the help.txt
            print(load_help_text())
            continue

        if response_econ == "back":
            print ("Go back to home page.")
            print(' ')
            break

        #-------------------------------------------------------
        # choose the function to plot Line chart for a country
        if response_econ == "a":

            response_alpha2 = input('Enter a 2-letter code of a country: ')
            response_alpha2 = response_alpha2.strip()
            if response_alpha2.lower() not in lst_a2:
                print(' ')
                print('<<Invalid input. Please enter the correct command.>>')
                print('<<Please check the 2-letter country code you enter is correct. >>')
                continue

            response_alpha2 = response_alpha2.upper()

            response_title = input('Enter a data type(GDP/GNI/GDP_growth): ')
            response_title = response_title.strip()
            lst_title = ['GDP', 'GNI', 'GDP_growth']

            if str(response_title) not in ['GDP', 'GNI', 'GDP_growth']:
                print(' ')
                print('<<Invalid input. Please enter the correct command.>>')
                continue

            try:
                result_data = get_data_for_one(response_alpha2, response_title)
                plot_for_one(result_data)

            except:
                print(' ')
                print('<<The country you enter do not have data in the World Bank. >>')
                print('<<Please enter another country code.>>')

            continue

        #------------------------------------------------------
        # choose the function to plot world map

        if response_econ == "b":
            response_title = input('Enter a data type (GDP or GNI): ')
            response_title = response_title.strip()

            if str(response_title) not in ['GDP', 'GNI']:
                print(' ')
                print('<<Invalid input. Please enter the correct command.>>')
                continue

            start_year = 1995
            lst_year = []
            while start_year < 2016:
                lst_year.append(start_year)
                start_year += 1
            #print(lst_year)

            response_year = input('Enter a 4 digit year (between 1995 to 2015): ')
            if int(response_year) not in lst_year:
                print(' ')
                print('<<Invalid input. Please enter the correct year between 1995 to 2015.>>')
                continue

            try:
                result_data = get_data_for_all(response_title, response_year)
                plot_for_all(result_data)

            except:
                print(' ')
                print('<<The country you enter do not have data in the World Bank. >>')
                print('<<Please enter another country code.>>')

            continue

        else:
            print(' ')
            print('<<Invalid input. Please enter the correct command.>>')
            print(' ')
            continue

def command_ft():
    response_ft = ''
    lst_a2 = get_lst_a2()
    first_enter = True
    if first_enter == True:
        print_command_3()
        first_enter = False

    while response_ft != 'back':
        print('-'*20)
        print(' ')
        print("==========[Financial times news search]===========")
        print(' ')
        print("Please enter 2-letter country code. ( or enter code/help/back for other selections.)")
        print(' ')
        response_ft = input('Enter a command: ')
        print(' ')

        if response_ft.lower() in lst_a2:
            response_ft = response_ft.upper()
            print(' ')
            result = get_FTimes_page(response_ft)
            print(result)
            continue

        if response_ft == "code":
            open_web_code()
            continue

        if response_ft == 'help': # open the help.txt
            print(load_help_text())
            continue

        if response_ft == "back":
            print ("Go back to home page.")
            print(' ')
            break

        else:
            print('<<Invalid input. Please enter the correct command.>>')
            print('<<Please also check the 2-letter country code you enter is correct. >>')
            print(' ')
            continue

def command_flicker():
    response_flicker = ''
    lst_a2 = get_lst_a2()
    first_enter = True
    if first_enter == True:
        print_command_4()
        first_enter = False

    while response_flicker != 'back':
        print('-'*20)
        print("==========[Flicker photo search]===========")
        print("Please enter 2-letter country code. ( or enter code/help/back for other selections.)")
        print(' ')
        response_flicker = input('Enter a command: ')
        print(' ')
        if response_flicker == "code":
            open_web_code()
            continue

        if response_flicker == 'help': # open the help.txt
            print(load_help_text())
            continue

        if response_flicker == "back":
            print ("Go back to home page.")
            print(' ')
            break

        if response_flicker.lower() in lst_a2:
            num = 1
            response_flicker = response_flicker.upper()
            print(' ')
            response_flicker_tag = input('Enter a tag for photo search: ')
            print(' ')
            lst_id = get_flickr_data(response_flicker, response_flicker_tag)
            for i in lst_id:
                print(str(num) + '. ' + get_flickr_photo_info(i, response_flicker_tag))
                num += 1
                # print the result url
            continue

        else:
            print('<<Invalid input. Please enter the correct command.>>')
            print('<<Please also check the 2-letter country code you enter is correct. >>')
            print(' ')
            continue


#[Part 7]######################################################################
# Part 7: Implement interactive prompt.
# Where to decide which command runs according to the user input.
# here is the home layer of the code.
# the user have six choices here: a/b/c/code/help/exit
def interactive_prompt():
    first_enter = True
    help_text = load_help_text()
    response = ''

    if first_enter == True:
        print(' ')
        print('Welcome to this program to search for economic data of different countries!')
        print('You can also find the latest news or Flicker photos of a country.')
        print(' ')
        print('If you have any question, please enter "help" to see detailed info.')
        print('If you want to search 2-letter country code, please enter "code".')
        print('If you want to leave, please enter "exit".')
        print(' ')
        print("Let's starts!")
        first_enter = False


    while response != 'exit':
        print_command_main()
        print("="*20)
        response = input('Enter a command: ')
        print(" "*20)
        response = response.strip()
        response = response.lower()

        if response == 'exit': # leave the program
            print("bye")
            break

        if response == 'help': # open the help.txt
            print(load_help_text())
            continue

        if response == 'code': # open the website to search for country code
            print('Open the website to search for a 2-letter country code.')
            open_web_code()

        # choose one of the three functions and call it
        if response == 'a':
            command_econ() # fucntion to plot economic data
            continue
        if response == 'b':
            command_ft() # fucntion for webscraping
            continue
        if response == 'c':
            command_flicker() # search for photos in flicker
            continue

        else: # invalid input
            print('<<Invalid input. Please enter the correct command.>>')
            print(' ')
            continue


if __name__=="__main__":
    user_input = input('Do you want to create a new database? Please reply "Yes" or "No": ' )
    if user_input == 'Yes':
        create_db()
        populate_db()
        interactive_prompt()

    elif user_input == 'No':
        try:
            interactive_prompt()
        except:
            print('<<Please build a new database!>>')
            print('<<Please enter this program again!>>')


    else:
        print('<<Invalid input. Please enter the correct command.>>')
        print('<<Please enter this program again!>>')
