
# calling this with a pipe!

# find ../xml_db | xargs grep "<\!" 2>/dev/null | python args.py

# finds all the files that have a comment in them and passes them as sys.stdin inputs!

# ONLY COMMENTING VODS INSIDE <live> elements that are missing vods
	# note... should probably just do this in <dateTime> elements instead
	# @TODO ------------------------------------------------------------------------------

import sys
import re

filesIn = []
for line in sys.stdin:
	# sys.stdout.write(line)
	filesIn.append(line.split(':')[0])

# for file in filesIn:
# 	print(file)

from PyQt5.QtCore import QXmlStreamWriter # Reader
from PyQt5.QtCore import QFile
from PyQt5.QtCore import QIODevice

from PyQt5.QtCore import QXmlStreamReader
from PyQt5.QtCore import QXmlStreamAttributes

filesOut = []
for file in filesIn:
	tmp = file.split('.xml')[0]
	filesOut.append(tmp + '_tmp.xml')
# 	tmp = file.split('.xml')
# 	filesOut.append()

for file in filesOut:
	print(file)

# these are files that have a commented VOD in them
# the commented VOD will be after the "live" section

# sys.exit(0)

import twitch

def VOD_Live_check(Live_List,VOD_Ele):
	# Live_List: 5 elements --> ['username','message',index] 0-4
	# VOD_Ele: ['username','message']
	# print(len(Live_List))
	# print(Live_List)
	# print(VOD_Ele)
	print("---------------\nLL:\n{}\nVOD_ELE:\n{}\n---------------".format(Live_List,VOD_Ele))
	for idx in Live_List:
		if(idx[:-1] == VOD_Ele):
			# print("VOD_Ele:\n{}\nLive_List_Ele:\n{}\n-------------".format(VOD_Ele,idx))
			return [True,idx[-1]] # returns the global counter too!
	return [False,None]

def get_VOD_dict(vod_id,live_list):
	# step 1: create an ordered list from the dictionary using the global counter


	# step 2: open the VOD and obtain vod list
	c_id="n7x8q0zray37mdyak98i7j3rlniuv8"
	c_secret= "c89tngxeotv63bggyac6ulf3ua9m61"
	helix = twitch.Helix(c_id,c_secret)

	# ['user','message'] ==> Going to be grabbed in order so no counter needed

	# step 3: only start grabbing when data collection event happens
	user_dictionary = {}
	full_pass = 0
	live_idx = 0
	first_list = []
	global_comment_count = 0
	for comment in helix.video(vod_id).comments:
		# print(live_idx)
		if(full_pass == 3):
			if(comment.commenter.display_name.lower() not in user_dictionary):
				user_dictionary[comment.commenter.display_name.lower()] = [[comment.message.body,global_comment_count]]
			else:
				user_dictionary[comment.commenter.display_name.lower()].append([comment.message.body,global_comment_count])
			global_comment_count += 1
			continue
		results = VOD_Live_check(
			live_list[live_idx:(live_idx+5)],
			[comment.commenter.display_name.lower(),comment.message.body]
			)
		if(results[0]):
			try:
				input()
			except(EOFError):
				input()
			live_idx = results[1]
			# print("Debug first_list.append(live_list[live_idx][:-1])\ntype(live_idx) = {}\nlive_list[0] = {}".format(type(live_idx),live_list[0]))
			first_list.append(live_list[live_idx][:-1]) # don't include live's global count
			full_pass += 1
			print(full_pass)
			if(full_pass == 3):
				for x in first_list:
					if(x[0] not in user_dictionary):
						user_dictionary[x[0]] = [[x[1],global_comment_count]]
					else:
						user_dictionary[x[0]].append([x[1],global_comment_count])
					global_comment_count += 1
		elif(full_pass):
			first_list = []
			full_pass = 0
			live_idx = 0

	if(full_pass != 3):
		print("ERROR: full pass from live -- VOD failed\nsystem exiting...")
		sys.exit(0)

	return user_dictionary

def takeThird(elem):
	return elem[2]

for fileIdx in range(len(filesIn)):
	# use fileIdx to index into filesIn and filesOut
	fileRead = QFile(filesIn[fileIdx])
	fileWrite = QFile(filesOut[fileIdx])

	if(not fileRead.open(QIODevice.ReadOnly)):
		print("Error opening fileRead: {}".format(filesIn[fileIdx]))
	if(not fileWrite.open(QIODevice.WriteOnly)):
		print("Error opening fileWrite: {}".format(filesOut[fileIdx]))

	reader = QXmlStreamReader(fileRead)
	writer = QXmlStreamWriter(fileWrite)

	writer.setAutoFormatting(True)
	writer.writeStartDocument()
	vod_id = None
	missing_vod = False
	while(not reader.atEnd()):
		reader.readNext()
		if(reader.isStartElement()):
			writer.writeStartElement(reader.name())
			if(reader.name() == "dateTime"):
				read_dateTime = reader.attributes().value("value")
				writer.writeAttribute("value",read_dateTime)
			elif(reader.name() == "live"):
				# reset the bool for every live element start
				# the comment with a vod ID is always after a <live>
				# so reset the flag after <live> detected
				# if flag turns true, can start building a live_recording_dict
				# to pass into the get_VOD_dict function
				missing_vod = False
				vod_id = None # reset the vod_id as well
			elif(reader.name() == "vod"):
				read_vod_id = reader.attributes().value("id")
				writer.writeAttribute("id",read_vod_id)
			elif(reader.name() == "user"):
				read_user = reader.attributes().value("name")
				writer.writeAttribute("name",read_user)
			elif(reader.name() == "comment"):
				read_count = reader.attributes().value("count")
				read_global_count = reader.attributes().value("global_count")
				read_comment = reader.attributes().value("value")
				attr = QXmlStreamAttributes()
				attr.append("count",read_count)
				attr.append("global_count",read_global_count)
				attr.append("value",read_comment)
				writer.writeAttributes(attr)

				# check for flag
				if(missing_vod):
					# inside the <live> element that's missing a vod
					if(read_user not in live_user_dict):
						live_user_dict[read_user] = [[read_comment,read_global_count]]
					else:
						live_user_dict[read_user].append([read_comment,read_global_count])
					# 	{
						# 'userName' : [["Sup mf'", 123],["adios",1299]]
						# ...
					#	}

			# elif()
		elif(reader.isEndElement()):
			# if(reader.name() == "live"):

			if(reader.name() == "dateTime"):
				# print(live_user_dict)
				if(missing_vod):
					# Logic for writing the VOD data!
					sorted_comment_obj_list = []
					for key in live_user_dict.keys():
						for x in live_user_dict[key]:
							sorted_comment_obj_list.append([key,x[0],int(x[1])])
					# sorted: [['user','comment','GLOBAL COUNT']]
					sorted_comment_obj_list.sort(key=takeThird)
					# now live recording is sorted by capture order
					# print("{}\nlength:{}".format(sorted_comment_obj_list,len(sorted_comment_obj_list)))
					# sys.exit(0)
					vod_user_dict = get_VOD_dict(vod_id,sorted_comment_obj_list)
					# value: [['comment',GLOBAL COUNT],...]


					sorted_comment_obj_list = None # empty it after using it

					# now write for the vod element

					writer.writeStartElement("vod")
					writer.writeAttribute("value",vod_id)

					# write all user and comment elements
					for key in vod_user_dict:
						writer.writeStartElement("user")
						writer.writeAttribute("name",key)
						count = 0
						for comment_obj in vod_user_dict[key]:
							writer.writeStartElement("comment")
							attr = QXmlStreamAttributes()
							attr.append("count",str(count))
							attr.append("global_count",str(comment_obj[1]))
							attr.append("value",comment_obj[0])
							writer.writeAttributes(attr)
							writer.writeEndElement()
							count += 1
						writer.writeEndElement() # end user element

					writer.writeEndElement() # end the vod element

			writer.writeEndElement() # ends all elements

		elif(reader.isComment()): # not going to be writing the comment again
			# live_user_dict = {}
			# missing_vod = True # found the 
			pattern = "[0-9]{9}" # 9 numbers in the VOD
			vod_id = re.search(pattern,reader.text()).group()
			if(vod_id): # found a vod pattern
				print("Found vod: {}".format(vod_id))
				missing_vod = True
				live_user_dict = {}
			# print(vod)
	if(reader.hasError()):
		print("Reader has error:\n{}\n{}".format(reader.error(),reader.errorString()))
		sys.exit(0)
	writer.writeEndDocument()
	fileRead.close()
	fileWrite.close()

	# switch the fileWrite to fileRead
	fileRead.remove()
	fileWrite.rename(fileRead.fileName())

print("EOF")