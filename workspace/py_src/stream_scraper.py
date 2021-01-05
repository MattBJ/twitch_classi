import sys


import twitch

# dictionary: {
#	user1	: [] comment / global_comment_count element list (to know chronological order of live feed)
#	user2	: []
#	...
#	userN 	: []
# }

#########################3
# check readme.txt for XML file layout

def My_Message_Handler(message,user_dictionary):
	print("{}\t({})\n{}: {}".format(message.channel,My_Message_Handler.global_comment_count,message.sender,message.text))

	if(message.sender not in user_dictionary):
		user_dictionary[message.sender] = [[message.text,My_Message_Handler.global_comment_count]]
	else:
		user_dictionary[message.sender].append([message.text,My_Message_Handler.global_comment_count])
	My_Message_Handler.global_comment_count += 1


channel_name = input("Input channel name (all lower):\nFormat: #<channel_name>\n")

c_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
c_token = "Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
import urllib.request
import bs4
import json
headers = {
	'client-id'		:	c_id,
	'Authorization'	:	c_token
}

url = "https://api.twitch.tv/helix/search/channels"
query_values = {
	'query' : channel_name[1:]
}
url_values = urllib.parse.urlencode(query_values)
full_url = url + '?' + url_values # --> important


##########################################
def get_stream_status(full_url,headers):
	req = urllib.request.Request(full_url,headers=headers)
	page = urllib.request.urlopen(req)
	soup = bs4.BeautifulSoup(page,"html.parser")
	packet = json.loads(soup.prettify())
	return [packet['data'][0]['is_live'],packet]

def get_date_time(packet):
	return packet['data'][0]['started_at']

is_live,first_packet = get_stream_status(full_url,headers)
date_time = "n/a"
if(is_live):
	# grab date time
	date_time = get_date_time(first_packet)

##########################################

user_dictionary = {}

My_Message_Handler.global_comment_count = 0


My_Chat = twitch.Chat(channel=channel_name,nickname='<your_twitch_username>',oauth='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
My_Chat.subscribe(on_next= lambda message: My_Message_Handler(message,user_dictionary),
					on_completed=print("mission completed!")
					)

import time

while(is_live):
	is_live = get_stream_status(full_url,headers)[0]
	if(is_live):
		time.sleep(10) # every 10 seconds it checks live status
		# delay for a bit
	else:
		# check for 60 seconds, if consecutively offline then assume channel is done streaming
		for i in range(6):
			is_live = get_stream_status(full_url,headers)[0]
			if(is_live):
				break
			time.sleep(10)

My_Chat.irc.leave_channel(channel_name)


My_Chat.irc.active = False
My_Chat.__del__()
#My_Chat.dispose()
print(My_Chat.irc.active)
# welp.. still don't know how to properly do it BUT it is writing!
My_Chat.irc.join(100) #can't join..
print("EOF")

################################################################################################################################################################
# XML 					WRITING 					SECTION
################################################################################################################################################################

from PyQt5.QtCore import QXmlStreamWriter # Reader
from PyQt5.QtCore import QFile
from PyQt5.QtCore import QIODevice

from PyQt5.QtCore import QXmlStreamReader
from PyQt5.QtCore import QXmlStreamAttributes
tmp_suffix = "_tmp"
file_prefix = "../xml_db/"
xml_filename = channel_name[1:] + "_stream_data"
xml_ext = ".xml"
outFile = QFile(file_prefix + xml_filename + xml_ext)
exist_bool = False
if(outFile.exists()):
	exist_bool = True
	inFile = QFile(file_prefix + xml_filename + xml_ext)
	outFile = QFile(file_prefix + xml_filename + tmp_suffix + xml_ext)

if(exist_bool):
	if(not inFile.open(QIODevice.ReadOnly)):
		print("FILE OPEN ERROR")
	reader = QXmlStreamReader(inFile)
else:
	reader = None
if(not outFile.open(QIODevice.WriteOnly)):
	print("FILE OPEN ERROR")

print("\nwriting to file {} from live recording...\n".format(outFile))

writer = QXmlStreamWriter(outFile)
writer.setAutoFormatting(True)

writer.writeStartDocument()
####################################################
writer.writeStartElement("streams") # ROOT NODE --> Must have
####################################################
writer.writeStartElement("dateTime")
writer.writeAttribute("value",date_time)
writer.writeStartElement("live")

for user in list(user_dictionary.keys()):
	writer.writeStartElement("user")
	writer.writeAttribute("name",user)
	count = 0
	# comment object: [MESSAGE, GLOBAL COUNT]
	for comment_obj in user_dictionary[user]:
		# new child element
		writer.writeStartElement("comment")
		attr = QXmlStreamAttributes()
		attr.append("count",str(count))
		attr.append("global_count",str(comment_obj[1]))
		attr.append("value",comment_obj[0])
		writer.writeAttributes(attr)
		writer.writeEndElement() # end Comment child element
		count += 1
		# 
	writer.writeEndElement() # end User child element
writer.writeEndElement() # end Live
writer.writeEndElement() # end Date element
#### --> everything above gets written to a document regardless, at the top
if(exist_bool):
	# This appends the old document at the end of the new dataset (<date><live>..</live></date>) created
	######
	while(not reader.atEnd()):
		reader.readNext()
		if(reader.isStartElement()):
			if(reader.name() == "streams"):
				# found the root node, don't rewrite this
				continue
			writer.writeStartElement(reader.name())
			if(reader.name() == "dateTime"): # value = <month_day_year>
				read_date_time = reader.attributes().value("value")
				writer.writeAttribute("value",read_date_time)
			elif(reader.name() == "live"): # no attributes
				pass # empty element
			elif(reader.name() == "vod"): # id attribute
				read_vod_id = reader.attributes().value("id")
				writer.writeAttribute("id",read_vod_id)
			elif(reader.name() == "dataPoints"): # no attributes rn
				pass # don't know yet
			elif(reader.name() == "user"): # name = username
				read_username = reader.attributes().value("name")
				writer.writeAttribute("name",read_username)
			elif(reader.name() == "comment"): # count, value
				read_count = reader.attributes().value("count")
				read_comment = reader.attributes().value("value")
				read_global_count = reader.attributes().value("global_count")
				attr = QXmlStreamAttributes()
				attr.append("count",read_count)
				attr.append("value",read_comment)
				writer.writeAttributes(attr)
		if(reader.isEndElement()):
			if(reader.name() == "streams"):
				continue
			writer.writeEndElement() # ends all elements EXCEPT root node

	if(reader.hasError()):
		print("READER LOOP TERMINATED: READER HAS ERROR")
		# print()
####################################################
writer.writeEndElement() # END THE ROOT NODE --> Streams
####################################################
writer.writeEndDocument() # finish the document

outFile.close()
if(exist_bool):
	inFile.close()

print("\nFinished writing to file {}".format(outFile))

if(exist_bool):
	inFile.remove() # ===>> DANGEROUS
	outFile.rename(inFile.fileName())

############################################################################################################
# VOD PART
############################################################################################################

# using this to sort a dictionary
def takeThird(elem):
	return elem[2]

# sorted list:
# [
#	['username','message',GLOBAL COUNT = 0],
#	['username','message',1],
#	...
#	['user','text',END_COUNT]
# ]

sorted_comment_obj_list = []

for key in user_dictionary.keys():
	for x in user_dictionary[key]:
		# x = ['message',global_count]
		sorted_comment_obj_list.append([key] + x)
		# sorted list = [['user','comment','GLOBAL COUNT']]

# order this list

sorted_comment_obj_list.sort(key=takeThird) # uses 3rd element in each list ele to sort, ASCENDING
# ^^^ will use this to find

# every comment grabbed from VOD check against first 5 elements in sorted list

def VOD_Live_check(Live_List,VOD_Ele):
	# Live_List: 5 elements --> ['username','message',index] 0-4
	# VOD_Ele: ['username','message']
	for idx in Live_List:
		if(idx[:-1] == VOD_Ele):
			return [True,idx[-1]] # returns the global counter too!
	return [False,None]

# going to do this three times in a row:
	# twitch = spammy, so a user will most certainly spam the same message at different times
	# So to minimize this, want to find 3 users to corrsepond with
		# each with a 5 input buffer


helix = twitch.Helix(
	'n7x8q0zray37mdyak98i7j3rlniuv8', # c_id registered for OAuth token that can read comments
	'c89tngxeotv63bggyac6ulf3ua9m61' # c_secret ^^^^
	)

a = helix.user(channel_name[1:])
vod = a.videos(first=1)
b = vod._next_videos_page()

VOD_Title = b[0].data['title']
vod_id = b[0].data['url'].split('/')[-1]

user_dictionary = {} # reset to empty

# this represents passing of the check 3 times
full_pass = 0
live_idx = 0 # start at first recorded LIVE comment
first_list = []
global_comment_count = 0
for comment in helix.video(vod_id).comments:
	if(full_pass == 3):
		if(comment.commenter.display_name.lower() not in user_dictionary):
			user_dictionary[comment.commenter.display_name.lower()] = [[comment.message.body,global_comment_count]]
		else:
			user_dictionary[comment.commenter.display_name.lower()].append([comment.message.body,global_comment_count])
		global_comment_count += 1
		continue # don't need to bother with following logic, already passed checks
	results = VOD_Live_check(
		sorted_comment_obj_list[live_idx:(live_idx+5)], # Live_List
		[comment.commenter.display_name.lower(),comment.message.body] # VOD_Ele
		)
	if(results[0]): # Found one of them!
		live_idx = results[1] # get the index into the sorted list
		first_list.append(sorted_comment_obj_list[live_idx][:-1])
		full_pass += 1
		if(full_pass == 3):
			# put in the 3 comments that have been recorded
			for x in first_list:
				if(x[0] not in user_dictionary):
					user_dictionary[x[0]] = [[x[1],global_comment_count]]
				else:
					user_dictionary[x[0]].append([x[1],global_comment_count])
				global_comment_count += 1
	elif(full_pass):
		# if results don't turn true BUT full_pass has incremented, then it needs to be reset
		# This should never happen!
		if(full_pass == 2):
			print("Holy shit it did it, found 2 but didn't find 3rd user/comment combo")
		# reset the sequence
		first_list = [] # empty the list again
		full_pass = 0
		live_idx = 0 # reset this too

sorted_comment_obj_list = [] # just to free space


if(full_pass != 3):
	print("Could not find one of the first 5 comments in entire VOD with corresponding 3 sequence check\n \
		exiting system..")
	print("VOD ID checked: " + vod_id)
	sys.exit(0)

exist_bool = False
if(outFile.exists()):
	exist_bool = True
	inFile = QFile(file_prefix + xml_filename + xml_ext)
	outFile = QFile(file_prefix + xml_filename + tmp_suffix + xml_ext)

if(exist_bool):
	if(not inFile.open(QIODevice.ReadOnly)):
		print("FILE READ OPEN ERROR # 2")
	reader = QXmlStreamReader(inFile)
else:
	reader = None
if(not outFile.open(QIODevice.WriteOnly)):
	print("File write open error # 2")

writer = QXmlStreamWriter(outFile)
writer.setAutoFormatting(True)

writer.writeStartDocument()

date_found_flag = False

if(not exist_bool):
	print("@TODO: Implement xml writing version if file doesnt exist")
	print("ERROR: READING VOD HAPPENS AFTER XML FILE CREATED -- BUT FILE IS MISSING")
else:
	# --> write this dictionary under a new child element <VOD> child of <Date> element, when Date attribute 'value' corresponds to user inputted value
	while(not reader.atEnd()):
		reader.readNext()
		if(reader.isStartElement()):
			writer.writeStartElement(reader.name()) # starts all elements that reader has
			if(reader.name() == "dateTime"): # one attribute
				# IMPORTANT --> change read_date only here *************************************
				read_date_time = reader.attributes().value("value")
				writer.writeAttribute("value",read_date_time)
			elif(reader.name() == "live"): # no attributes
				pass
			elif(reader.name() == "vod"): # no attributes.. actually maybe an ID
				read_vod_id = reader.attributes().value("id")
				writer.writeAttribute("id",read_vod_id)
			elif(reader.name() == "dataPoint"): # no attributes
				pass
			elif(reader.name() == "user"): # name = username
				read_username = reader.attributes().value("name")
				writer.writeAttribute("name",read_username)
			elif(reader.name() == "comment"): # count, value
				read_count = reader.attributes().value("count")
				read_comment = reader.attributes().value("value")
				read_global_count = reader.attributes().value("global_count")
				attr = QXmlStreamAttributes()
				attr.append("count",read_count)
				attr.append("global_count",read_global_count)
				attr.append("value",read_comment)
				writer.writeAttributes(attr)
		if(reader.isEndElement()):
			if(reader.name() == "dateTime"): # check if it matches up with inputted date
				if(read_date_time == date_time): # this is the place to input everything!
					date_found_flag = True
					####################################################
					# LOGIC HERE:
					writer.writeStartElement("vod")
					writer.writeAttribute("id",vod_id)
					for user in list(user_dictionary.keys()):
						writer.writeStartElement("user")
						writer.writeAttribute("name",user)
						count = 0
						for comment_obj in user_dictionary[user]:
							# comment_obj = ['message',GLOBAL_COUNT]
							writer.writeStartElement("comment")
							attr = QXmlStreamAttributes()
							attr.append("count",str(count))
							attr.append("global_count",str(comment_obj[1]))
							attr.append("value",comment_obj[0])
							writer.writeAttributes(attr)
							count += 1
							writer.writeEndElement() # ends the comment element
						writer.writeEndElement() # ends user element
					writer.writeEndElement() # ends the VOD element
					####################################################
			writer.writeEndElement() # ends all other elements
			pass
	if(reader.hasError()):
		print("READER HAS ERROR")
		print(reader.error())
		print(reader.errorString())
writer.writeEndDocument() # finish the document

if(not date_found_flag):
	print("ERROR: Couldn't find inputted date live stream recorded data")
	print("Date input: {}".format(date_time))
outFile.close()
if(exist_bool):
	inFile.close()

if(exist_bool):
	inFile.remove()
	outFile.rename(inFile.fileName())