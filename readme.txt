Used a virtual environment for this

Directory: $ python3 -m venv .

Directory tree:
	+- bin/		------------ contains binaries to setup the environment for the python modules
	+- include/
	+- lib/
	+- lib64/
	+- pyvenv.cfg
	+- readme.txt --------- This file
	+- share
	|
	|
	|
	+- workspace/ --------- all resource/source files will be in this dir
		|
		+- xml_db/ -------- contains every xml file used for each streamer
		|
		|
		+- py_src/--------- contains the source code used to work the program
			|
			+- args.py ------------ thise is a program that reads xml comments for vods
			|
			+- stream_scraper.py ------------------------ this is the main program


cd into the dir tree

$ source bin/activate
	-> This sets up the python environment for this workspace
	-> to deactivate: $ deactivate

Once activated the virtual environment: -------- VERY IMPORTANT TO DO THIS FIRST
	- pip install twitch-python
	- pip install bs4
	- pip install PyQt5 ***** ERROR!!

PyQt5 won't work out of the box, however, as it is a wrapper for Qt5 which is a C++ library
	- this means you need to get the dynamic library for it

$ sudo apt-get install libxcb-xinerama0
	- for linux distros that use aptitude as a package manager
	- just note the name of the library: libxcb-xinerama0

.. also need to make sure to get libGL.so (another dynamic library)

---------------------------------------------------------------------------------------------------------------

How did I find this library? (if you're interested)
	Important build information:
		> pip install PyQt5
		> But will get error! https://askubuntu.com/questions/1298645/shared-library-not-found-for-pyqt5-libxcb-xinerama-so-0-not-found
			--> This is my askubuntu.com forum question, I'd read it to see how I figured everything out
			--> Highly recommend reading it to see the debugging process

---------------------------------------------------------------------------------------------------------------

Now, all the prerequisite libraries have been installed
	- https://doc.qt.io/qt-5/qt5-intro.html
		- c++ library but can search for the classes and they are just wrapped in python
	- https://pypi.org/project/twitch-python/
		- twitch-python module
	- https://www.pythonforbeginners.com/beautifulsoup/beautifulsoup-4-python/
		- just look up tutorials on it if you want to dig in
		- it's a nice way of formatting network/port requests

---------------------------------------------------------------------------------------------------------------

workspace/
	- py_src/ source files
	- xml_db/ where files get written to/read from

---------------------------------------------------------------------------------------------------------------

TWITCH API:
	- https://dev.twitch.tv/docs/api/reference

What we need from twitch api:
	- user online? (stream that we are going to scrape)
	- permissions to read the chat
		- need an OAuth token with this scope 
	- OAuth tokens:
		https://dev.twitch.tv/docs/authentication/#scopes
		https://dev.twitch.tv/docs/authentication
	- read from saved VOD for comments

To obtain OAuth tokens:
	- https://dev.twitch.tv/docs/authentication/#registration
	- https://dev.twitch.tv/
		- create a username/password
		- it NEEDS to have 2 factor authentication (newish thing with twitch.. enjoy the phone number giveaway)
		- Once logged in:
			- click on Applications
			- Register your application
			- Give it a Name
			- give the OAuth URL: http://localhost
			- Category - I gave it like chat bot
			- You're going to get:
				- client-id: "aasl;dkcj;alkhegiohaiotg"
				- client-secret: "lakjcee49790fuoierjf" - random string
				- SAVE THESE
			- Do that twice (I have two sets of OAuth tokens for separate tasks)
				- one will be to read chat
				- one will be to check if users are online
				- two separate scopes

Getting first OAuth token: Checking if a user is online
	- I'm still figuring out how to do this programatically!!!
	- for now, I actually use my URL to query the proper fields and it gives a response
	...
	- https://id.twitch.tv/oauth2/authorize?client_id=<INSERT_ID_NO_QUOTES>&redirect_uri=http://localhost&response_type=token

	When GET'ing this address, you'll be redirected to login with user/password and then it'll redirect you:
		-> Check your URL for this:
		-> localhost/#access_token=<oauth_token>&scope=&token_type=bearer
*******
Authorization: bearer <oauth_token>
******* obtained

for scopes
	chat:edit --> write
	chat:read --> read

	Follow this step by step guide:

1) 1)https://id.twitch.tv/oauth2/authorize

	python import requests
	?client_id=<your client ID>
	&redirect_uri=<your registered redirect URI>
	&response_type=<type> -->2 valid values: token id_token or id_token (return access token and an ID token (JWT) or just an ID token)
	&scope=<space-separated list of scopes, THIS MUST INCLUDE THE openid SCOPE>

	--> headers = {
		"client_id" : "CLIENT ID FROM APPLICATION GENERATED",
		"redirect_uri" : "http://localhost",
		"responise_type" : "code",
		"scope" : "chat:read chat:edit"
	}

	import urllib.request

	url_values = urllib.parse.urlencode(headers)
	bae_url = https://id.twitch.tv/oauth2/authorize
	full_url = base_url + '?' + url_values

	req = requests.head(full_url,allow_redirects=True)
	print(req.url) --> grab this URL from the terminal
	
2)	Copy URL from ^^ and paste in browser, then login to your account
	--> grab the URL that the login page redirects you to once you agree to permissions

3)	headers = {
	"client_id":"<YOUR CLIENT ID>",
	"client_secret":"<YOUR CLIENT SECRET>",
	"code":"<CODE IN URL ABOVE AFTER LOGGED IN>",
	"grant_type":"authorization_code", -- use verbatim "authorization_code"
	"redirect_uri":"http://localhost"
	}

	url_values = urllib.parse.urlencode(headers)

	req = requests.post("https://id.twitch.tv/oauth2/token?"+url_values)

4)	print(req.json()) --> THIS WILL PRINT EVERYTHING YOU NEED
	--> namely: the access_token which represents your OAuth token
					--> YOU NEED TO KEEP THIS SAVED

---------------------------------------------------------------------------------------------------------------

FINISHED AUTHENTICATING FOR API

---------------------------------------------------------------------------------------------------------------

Now, onto the two source code files that will be sent in the workspace/py_src dir

---------------------------------------------------------------------------------------------------------------

ARGS PYTHON MODULE

Purpose: To grab all the files with <!-- --> XML comments in them and read them for VOD ID's
	-> I added this in case of any bugs while grabbing VODs
	-> if error reading the vod, just do the following:

	1) go to the file that has the error
	2) go to the <dateTime> element that has the VOD read error
	3) go to the <live> element (i shouldve put the comment in the dateTime but this is how it goes)
	4) place the comment directly beneath the <live> element like so:

<streams>
	<dateTime value="....">
		<live>
			<!-- VOD: XXXXXXXX-->
			....
		</live>
	</dateTime>
	....
</streams>

	You can only properly run this file from a bash terminal:
		--> I use stdin and piping to read in the files (didn't feel like using python to read through everything)

		$ find /path/to/xml_db/ | xargs grep "<\!" 2>/dev/null | python args.py

	What is this doing?
		first command: finds every file/dir that exists in that path
			-- passes them over to the second command with the pipe '|'
		second command: treats every line as a file to check grep with
			-- grep searches for the regex expression "<\!"
			-- 2>/dev/null redirects all errors to /dev/null (erases them from stdout)
		third command: passes the files that have the xml comments in them into python using sys.stdin


	This python module will reference the VOD id in the comment and fetch it/write it
---------------------------------------------------------------------------------------------------------------

STREAM SCRAPER PYTHON MODULE

this is the bread and butter (so far) of the data collection.

Just a high level overview:
	1) user inputs a stream they want to record (@TODO automate this and make a vector of all followed channels to record)
		-- input = #<stream name in all lowercase, including the '#' at beginning>

	2) the irc is subscribed to and a dictionary data structure begins to be filled
	3) inside a while loop, with a 10 second delay (on a separate thread as the irc subscription)
		... loop checks for live/not live status of channel
		.. if not live, it checks for another minute in case small network error
	4) finished recording live data

	5) writes to XML file (if file already exists it appends new data at top, old data at bottom)

	6) after writing LIVE data to xml, immediately checks the channel's last VOD recorded

	7) does some logic to figure out when data acquisition began (or if it can't find it, then error)
		-> this requires debugging (like commenting <!-- VOD: XXXXXXXX--> in the correct manner and getting back to later)
		-> sometimes VODs don't get created (not often though)

	8) writes VOD data underneath live data

	9) closes files and exits

---------------------------------------------------------------------------------------------------------------

XML FILE STRUCTURE

each xml file represents ONE streamer's database

<streams>
	<dateTime value=""
		<live>
			<user name="USERNAME">
				<comment count="0" global_count="xxx" value="this is a live comment"/>
				....
			</user>
			...
		</live>
		<vod id="XXXXXXXX">
			<user name="USERNAME">
				<comment count="0" global_count="xxx" value="this is a VOD comment"/>
				....
			</user>
			....
		</vod>
		<dataPoints>
		</dataPoints>
	</dateaTime>
	....
</streams>


the dataPoints element has yet to be implemented, but that's just a matter of choosing how to edit the filtering of missing comments/usernames (ie dataPoints represents sample space of banned messages)
	--> WE WANT TO MINIMIZE NOISE AS MUCH AS POSSIBLE
---------------------------------------------------------------------------------------------------------------