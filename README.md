# si-507-project-4
Final project for SI 507

#[Data resources]#############################
1. The Economic data in this project is from API of THE WORLD BANK. 
  This API required no authorizaion.
  The link of the API is: 
  https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structure

2. Use the Flicker API to get photos. 
  This API required API key. The example of the secrets.py that contains the API key for the program is provided. 
  The link of the API is: 
  https://www.flickr.com/services/api/

3. Web scraping of Financial Times news. 
  The link of the Webpage is: 
  https://www.ft.com/search


#[How to run the function]#############################

First, when you run the program, you can choose whether to build the new database or not. 
If it is your first time to run the program, please enter "Yes".

Then, you will enter the home layer of the program, you will be required to type in some commands to run the program. 
At the home layer, you can choose three types of functions to run. ("a", "b" or "c")
You also can use some command to get extra supports.(such as "help" or "exit")

The explanation of the commands are following:

Commands available for specific layers:

[Home] --------------------

[a] -->	[Economic charts]

	Description: Search for Economic Data of countries from the World Bank database.

	Options:

	[a] *** Line chart
	<Description>: Get a line chart of a country's GDP/GNI/GDP_growth from 1995 to 2015.
	<User Input>: a 2-letter country code, data type (GDP/GNI/GDP_growth)


	[b] *** World map
	<Description>: Get the world map of GDP/GNI of all countries at a specific year.
	<User Input>: data type (GDP/GNI/GDP_growth), a 4 digit year (between 1995 to 2015)


[b] -->	[Financial times news search]

	<Description>: You can search for latest ten news in FTimes website regarding to 
	the country you want to look for.
	
	<User Input>: a 2-letter country code


[c] -->	[Flicker Photo search]

	Description: You can search for ten photos of a country that have a tag 
	you want.

	<User Input>: a 2-letter country code, a tag for the photo

---------------------------------------------------

Command available for all layers: 

[code]
	Description: Open a website that listing all countries names and their 2-letter 
	Alpha2 code. This allows user to find the 2-letter country code of a specific 
	country.


[Help]
	Description: Open the help.txt to see the description of the program

[back]	
	Description: Go back to home layer.

[exit]
	Description: Leave the program.












  
#[How the function is constructed]#############################
  
