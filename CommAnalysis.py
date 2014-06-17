#python2.7 script to parse multiple CSV files of comm summary info, do a bunch of calculations on it, print the results in a new CSV file
#Will calculate average response times per device per channel, device counts per channel, total communication time, prediction on comm time after adding devices, suggested poll rates, estimated percent improvement if the new poll rates were applied(this number will be smaller than actual improvement, ALL averages are taken on the conservative side).
#Jacob Vickers - SET TEAM SCADA Intern - 5/29/2013



import csv
import os
import decimal
import math
import datetime

'''
input_string = raw_input("Please enter source CSV file: ")		#take input from user. this must be the export of the main grid on comm summary screen

 section is for testing purposes, to save me from typing out all of the names of the files. otherwise it will prompt the user for the filenames. 
#EXAMPLE: you want to test riverton, just type "riv" at the first prompt and it will assume the source and secondary files are named as below.
if input_string == "riv":
	input_string = "rivnew.csv"
	second_string = "rivnew2.csv"
	result_string = "riverton_results.csv"

elif input_string == "ran":
	input_string = "ran.csv"
	second_string = "ran2.csv"
	result_string = "rangely_results.csv"
elif input_string == "dj":
	input_string = "dj.csv"
	second_string = "dj2.csv"
	result_string = "dj_results.csv"
else:
	second_string = raw_input("Please enter secondary CSV file: ")	#this must be the export from the second grid on comm summary screen
	result_string = raw_input("Please enter final result CSV file: ")	#where the results are stored. file does not have to exist, must be a CSV
'''
input_string = "exportout.csv"
second_string = "exportout2.csv"
result_string = "results.csv"
try:
	with open(input_string, 'rb') as f:
		u = 1
except IOError:
	print os.getcwd()

	i = 0 
	while i < 9999999:
		i = i + 1

with open(input_string, 'rb') as f:	#builds a "cleaned up" version of the first export, only takes good values. Kicks out any rows that have incomplete data, we dont want them. 	
	writer = csv.writer(open("temp.csv",'wb'))
	reader = csv.reader(f)
	i = 0
	for row in reader:		
		s = "SALE"	#common names that have bad values in site services, want to remove them.
		p = "NETSA"
		if i < 1:	#i==1 means first row in CSV
			#want to discard the first row since its usually just labels
			if row.count("Status") == 1 or row.count("Mtr TYPE") == 1 or row.count("SYCSAPRT") == 1 or row.count("SYDEVCOMID") == 1:  #these are all common labels, assign variables to indicate where the labels are. Dynamic indexing.
								
				if row.count("CommID") == 1:
					com_idx = row.index("CommID")
				elif row.count("COM") == 1:	#other name for COMMID					
					com_idx = row.index("COM")
				elif row.count("SYDEVCOMID") == 1:	#other name for COMMID					
					com_idx = row.index("SYDEVCOMID")				
				else:
					com_idx = 0		
				if row.count("Mtr TYPE") == 1:
					device_idx = row.index("Mtr TYPE")
				elif row.count("RTU Type") == 1:	#other name for Mtr Type
					device_idx = row.index("RTU Type")
				elif row.count("SYDEVTYPE") == 1:	#other name for Mtr Type
					device_idx = row.index("SYDEVTYPE")
				else:
					device_idx = 0						
				if row.count("Avg Resp (ms)") == 1:
					avgresp_idx = row.index("Avg Resp (ms)")
				elif row.count("Resp (ms)") == 1:
					avgresp_idx = row.index("Resp (ms)")
				elif row.count("Avg Succ Resp Time") == 1:
					avgresp_idx = row.index("Avg Succ Resp Time")
				elif row.count("SYCSAPRT") == 1:	#other name for avg resp
					avgresp_idx = row.index("SYCSAPRT")								
				i = i + 1
			
		else:	   #write the row to the "cleaned up" CSV document. Excludes any blank entries, or entries that dont have an avg response. The "cleaned up" CSV only has good entries.  

			if row[0].find(s) == -1 and row[0].find(p) == -1 and row[avgresp_idx] !="" and row[avgresp_idx] !=" " and row[avgresp_idx]!= "0" and row[avgresp_idx] != 0 and row[com_idx] !="" and row[com_idx] != " " and row[avgresp_idx] !='' and row[avgresp_idx] !=0.0 and row[avgresp_idx] !="0.0" and row[device_idx] != " " and row[device_idx] != "":							
				writer.writerow(row)
				x = len(row)	#grabbing the row length here for more error checking later
				c = len(row)
f.close()

#for some reason grid cells cant hold more than 16 characters but the row labels can, fixing it here.
with open(second_string, 'rb') as f:	 	
	s = []
	reader = csv.reader(f)	
	for row in reader:
		if len(row[0]) > 16:	#chopping chars > 16 off, as thats how it will be read in
			str_tmp = row[0]
			str_tmp = str_tmp[0:16]
			row[0] = str_tmp
		if row.count("SYCSSTNLD") == 1:			
			succ_msg_idx = row.index("SYCSSTNLD")		#dynamic indexing
			fail_msg_idx = row.index("SYCSFTOTLD")		#NOTE: If the second grid on the comm sum screen has labels other than the UDCs listed right here, this code will not work(please leave them as default). If you changed those labels, you are a bad person and you should feel bad.
			avg_resp_idx = row.index("SYCSAPRTLD")
		if row[succ_msg_idx] != "" and row[succ_msg_idx] != " " and row[fail_msg_idx] != "" and row[fail_msg_idx] != " " and row[avg_resp_idx] != "" and row[avg_resp_idx] != " ":
			s.append(row)
with open("temp2.csv",'wb') as f:	#fixed version of the smaller grid
	writer = csv.writer(f)
	for a in s:
		writer.writerow(a)

#Global variables. Lists are very closely related to C++ Vectors
device_list = [] #this holds the devices that are used in this site service. will automatically populate
chan_list = []	#chan_list will be the main data holder for this program. will eventually function something like a 2D array. Its the only 2D list because I found out it was just as easy to use a 1D list when I was halfway through building this script.
chan_resp = []	#will hold avg response time per channel, # succ msgs last day , avg time to poll entire chan
max_list = []	#list that holds the maximum found response times for each device, will be used to make suggestions on poll rate
max_print_list = []	#list to help me print out the maxes
pred_list = []	#list will contain current and new waittime on failed messages
backup_max = [] # for outliers
#new_sat_list = []	#will contain saturation level of channels. Ended up not needing this.

with open("temp.csv", 'rb') as f:	#read from the "cleaned up" CSV
	reader = csv.reader(f)
	i = 0
	totalsum = 0
	average = 0
	avgresp = 0
	for row in reader:	#get response values, channel value, build the empty channel list
		if len(row) == x:	#more error checking to eliminate bad values
			t = row[avgresp_idx]							
			try:	#was getting some index out of bounds error, but it only happens when the read in file is bad, which shouldnt happen
				avgresp = float(t)
			except IndexError:
				pass					
			dev = row[device_idx]
			if device_list.count(dev) == 0:	#populate the device list if device hasnt been found yet
				device_list.append(dev)
			channel = row[com_idx]
			channel = str(channel)
			if chan_list.count(channel) == 0 and channel != "CHANNE":					
				chan_list.append(channel)
		x = len(row)
x = c			
for a in chan_list:#make it a list of lists(python), so we can append new values to each entry. Similar to 2D array, except each entry can have multiple data members. NOTE: This is the only list of lists, each item in chan_list is an actual list itself. All of the other data structures that I use in this program are just regular lists. I switched to 1D lists halfway through building this...it was easier and I didn't feel like rebuilding the first part of the program, yeah I know it's bad programming practice.
	chan_list[chan_list.index(a)] = [chan_list[chan_list.index(a)]]
for a in chan_list:#append the new values
	for b in device_list:	
		chan_list[chan_list.index(a)].append(b) #device
		chan_list[chan_list.index(a)].append(0)	#dev resp
		chan_list[chan_list.index(a)].append(0)	#dev count
		chan_list[chan_list.index(a)].append(0)	#dev avg
for c in device_list:
	max_list.append(c)	
	max_list.append(0)	#max response time found per device, will be used later
	backup_max.append(c)	#second largest, used for outliers
	backup_max.append(0)
	backup_max.append(99999)
with open("temp.csv", 'rb') as f:	#read from cleaned up CSV again
	reader = csv.reader(f)
	for row in reader:
		if len(row) == x:	#more error checking, making sure im not taking a bad line with blank values
			t = row[avgresp_idx]		#grab all the info
			avgresp = float(t)		
			dev = row[device_idx]
			channel = row[com_idx]
			channel = str(channel)	
			max_idx = max_list.index(dev) + 1
			if avgresp > max_list[max_idx]:	#finds the largest avg response of each device type
				max_list[max_idx] = avgresp	#puts it in max_list
			for a in chan_list:
				if a[0] == channel:#find where the channel is in the list, manipulate its data members(devices,count,response)
					chn_idx = chan_list.index(a)
					dev_idx = a.index(dev)
			chan_list[chn_idx][dev_idx + 1] = chan_list[chn_idx][dev_idx + 1] + avgresp	#sum the average responses
			chan_list[chn_idx][dev_idx + 2] = chan_list[chn_idx][dev_idx + 2] + 1		#iterate the count

with open("temp.csv", 'rb') as f:	#read from cleaned up CSV again
	reader = csv.reader(f)
	for row in reader:
		if len(row) == x:	#more error checking, making sure im not taking a bad line with blank values
			t = row[avgresp_idx]		#grab all the info
			avgresp = float(t)		
			dev = row[device_idx]
			channel = row[com_idx]
			channel = str(channel)	
			backup_resp_idx = backup_max.index(dev) + 1
			backup_dist_idx = backup_max.index(dev) + 2 
			max_idx = max_list.index(dev) + 1
			dist = 	max_list[max_idx] - avgresp
			if dist < backup_max[backup_dist_idx] and dist != 0.0:				
				backup_max[backup_resp_idx] = avgresp
				backup_max[backup_dist_idx] = dist
for a in chan_list:
	for b in device_list:#build the device data. Each device in each channel needs a count, avg response.
		dev_idx = a.index(b)
		rsp_idx = dev_idx + 1	#keep track of indexes. could've hard-coded this, but this is better for generalization
		cnt_idx = dev_idx + 2
		avg_idx = dev_idx + 3
		if a[cnt_idx] == 0:
			a[avg_idx] = 0	#avoid the division by 0, if the denominator is 0 just set the whole quotient=0. Python is really picky about this, it's not that big of a deal.
		else:
			a[rsp_idx] = float(a[rsp_idx])	
			a[cnt_idx] = int(a[cnt_idx])
			a[avg_idx] = a[rsp_idx] / a[cnt_idx]	#average = sum / count
f.close()

#need to read in second CSV with # succ msgs, avg resp times, failed messges
with open("temp2.csv", 'rb') as f:	#read from the "cleaned up" CSV	
	reader = csv.reader(f)
	i = 0	
	for row in reader:
		if row.count("SYCSSTNLD") == 1:			
			succ_msg_idx = row.index("SYCSSTNLD")		#dynamic indexing
			fail_msg_idx = row.index("SYCSFTOTLD")		#NOTE: If the second grid on the comm sum screen has labels other than the UDCs listed right here, this code will not work(please leave them as default). If you changed those labels, you are a bad person and you should feel bad.
			avg_resp_idx = row.index("SYCSAPRTLD")	
		if i > 0:	#dont want first row
			if row[succ_msg_idx] == "" or row[succ_msg_idx] == " " or row[avg_resp_idx] == "" or row[avg_resp_idx] == " ":
				row[succ_msg_idx] = 1
				row[avg_resp_idx] = 1					
				chan_resp.append(row[0])	#chan name
				chan_resp.append(1)	#num succ msgs		
				chan_resp.append(1)	#avg response time for chan
				chan_resp.append(1)	#average time for chan to poll, not yet calculated
				chan_resp.append(1)	#number of devices per chan, not calculated yet
				chan_resp.append(1)	#avg number of messages per day, not calculated yet
				chan_resp.append(chan_list.index(a))	#the channel's index in the main list
			else:	#store values
				name = row[0]
				num_msgs = row[succ_msg_idx]
				num_msgs = int(num_msgs)
				avg_chan_resp = row[avg_resp_idx]
				avg_chan_resp = float(avg_chan_resp)		
				for a in chan_list:					
					if a[0] == name:		
						chan_resp.append(name)	#chan name
						chan_resp.append(num_msgs)	#num succ msgs		
						chan_resp.append(avg_chan_resp)	#avg response time for chan
						chan_resp.append(0)	#average time for chan to poll, not yet calculated
						chan_resp.append(0)	#number of devices per chan, not calculated yet
						chan_resp.append(0)	#avg number of messages per day, not calculated yet
						chan_resp.append(chan_list.index(a))	#the channel's index in the main list				
		i = i + 1		
f.close()

#chan_resp indexes. these are static and will never change so I can hard code them. 
name_idx = 0
msg_idx = 1
rsp_idx = 2
time_idx = 3
num_idx = 4
day_idx = 5
idx_idx	= 6
while idx_idx < len(chan_resp):
	chan_resp[time_idx] = long(chan_resp[rsp_idx] * chan_resp[msg_idx] * .001)	#avg time to poll channel in seconds(its originally in ms)	
	a = chan_list[chan_resp[idx_idx]]	#find corresponding entry in the chan_list
	cnt_idx = 3	#index of device count in the chan_list
	last = 4	#last index, to make sure i'm not exceeding the length of the list and stuff
	cnt_sum = 0	#total # of devices in a channel
	while last < len(a):
		cnt_sum = cnt_sum + int(a[cnt_idx])
		cnt_idx = cnt_idx + 4		
		last = last + 4
	chan_resp[num_idx] = cnt_sum
	chan_resp[day_idx] = chan_resp[msg_idx] / chan_resp[num_idx]	#avg msgs per day = total #msgs per day / #devices in channel	 	
	name_idx = name_idx + 7	#Iterate to the next set of data
	msg_idx = msg_idx + 7
	rsp_idx = rsp_idx + 7	
	idx_idx	= idx_idx + 7
	num_idx = num_idx + 7
	day_idx = day_idx + 7
	time_idx = time_idx + 7
avg_rsp_poll = 0	#find the average response time of all the maxs, this will be used to find new wait times for a failed msg.
for c in device_list:
	max_idx = max_list.index(c)+1	
	sug_max = max_list[max_idx] + 300	#safe to set maximum timeout wait 300ms higher than the highest resp time we found. just to be safe
	avg_rsp_poll = avg_rsp_poll + sug_max	
	#sug_max = str(sug_max) + " Msg Timeout(ms)"
	max_print_list.append(c)
	max_print_list.append(sug_max)	
y = len(max_list) / 2	#gives me the count of devices so i can find the average
try:
	avg_rsp_poll = float(avg_rsp_poll / y)
except ZeroDivisionError:	#divide by 0 error, instead of crashing it will produce blank output. It will only ever happen if its fed a bad file. 
	pass
avg_rsp_poll = round(avg_rsp_poll,3)
for a in chan_list:
	pred_list.append(a[0])	#enter chan names
	pred_list.append(0)	#num failed messages yesterday
	pred_list.append(0)	#old wait time minutes
	pred_list.append(0)	#new wait time
	pred_list.append(0)	#percent improvement
	pred_list.append(0)	#increase in polls per hour

with open("temp2.csv", 'rb') as f:
	reader = csv.reader(f)	
	i = 0	#first row is usually just labels
	for row in reader:
		#print row
		if row.count("SYCSSTNLD") == 1:
			succ_msg_idx = row.index("SYCSSTNLD")		#dynamic indexing
			fail_msg_idx = row.index("SYCSFTOTLD")	
			avg_resp_idx = row.index("SYCSAPRTLD")	
		if i > 0:
			if pred_list.count(row[0]) != 0 and row[avg_resp_idx]!="0.0" and row[avg_resp_idx]!=0.0:	#if the channel is in the pred_list. (if the channel is used it should be in there)					
				base_idx = pred_list.index(row[0])	#dynamic indexing 
				failed_msgs = int(row[fail_msg_idx])		
				pred_list[base_idx + 1] = failed_msgs	#num failed msgs
				if failed_msgs != 0:					
					wait_time = float(pred_list[base_idx + 1] * 18)	#assuming 6000ms wait time and 3 retries. 6*3=18
					wait_time = float(wait_time / 60)	#get it into minutes
					wait_time = round(wait_time,3)
					#print wait_time
					pred_list[base_idx + 2] = wait_time 	#old wait time
					new_wait = float(failed_msgs * avg_rsp_poll*.001 * 2)	#average of all the suggest poll settings is used here. 2 retries
					new_wait = float(new_wait / 60)
					new_wait = round(new_wait,3)
					pred_list[base_idx + 3] = new_wait	#new wait time 			
					per_imp = float(new_wait / wait_time)	#calcuating precent improvement, This isn't used anymore but I left it in here just because.
					per_imp = float(1-per_imp)
					per_imp = float(per_imp*100)
					per_imp = round(per_imp,3)				
					per_imp = str(per_imp)+"%"
					pred_list[base_idx + 4] = per_imp	#percent improvement
				else:
					new_wait = 0
					wait_time = 0
					per_imp = 0
					pred_list[base_idx + 2] = wait_time
					pred_list[base_idx + 3] = new_wait
					pred_list[base_idx + 4] = per_imp
		i = 1	
f.close()
rsp = 1

#PRINTING SECTION, WRITES ALL OUTPUT TO CSV FILE
with open(result_string, 'wb') as f:
	writer = csv.writer(f)
	from time import localtime, strftime
	time = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())	
	u = ["Channel","TIMESTAMP: "+time]
	writer.writerow(u)
	for a in chan_list:
		if chan_resp.count(a[0]) > 0:
			p = chan_resp.index(a[0])
			o = float(chan_resp[p+3])
			mins = float(o / 60)
			mins = round(mins,3)		
			o = mins / 1440	#1440 = num minutes in a day		
			o = o * 100
			o = round(o,3)		
			o = str(o)		
			if mins == 0.0:	#if there is no data point for avg resp
				mins = "COULD NOT CALCULATE: INSUFFICIENT DATA."
				o = "%Saturation(daily) "+ mins
				r = [a[0], "Device Type" , "Device Average Response(ms)" , "Device Count" , o]
			else:
				mins = str(mins)
				o = "%Saturation(daily) " + o + "%" + " = " + mins + " Minutes"			
				r = [a[0], "Device Type" , "Device Average Response(ms)" , "Device Count" , o]	#csv writer can only write lists for some reason. so i make it a list
			writer.writerow(r)
			chn_idx = chan_list.index(a)
			dev_idx = 1
			rsp_idx = 2	
			cnt_idx = 3
			avg_idx = 4			
			while avg_idx < len(a):#don't want to exceed the array size.
				q = [" ",a[dev_idx],round(a[avg_idx],3),a[cnt_idx]]			
				writer.writerow(q)			 
				dev_idx = dev_idx + 4	#move on to the next device in the list, it's 4 places away from the current one
				rsp_idx = rsp_idx + 4	
				cnt_idx = cnt_idx + 4
				avg_idx = avg_idx + 4
			l = [" "]
			writer.writerow(l)
			l = [" ", "COST TO ADD: " ,"Additional Time(Seconds) ","New Saturation%"]
			writer.writerow(l)
			chn_idx = chan_list.index(a)
			dev_idx = 1
			rsp_idx = 2	
			cnt_idx = 3
			avg_idx = 4	
			while avg_idx < len(a):#don't want to exceed the array size.
				addtime = a[avg_idx] * chan_resp[p + 5] * .001
				addtime = round(addtime, 3)
				o = float(float(chan_resp[p+3]) + addtime)					
				o = float(o / 60)			
				o =float(o / 1440)
				o = o * 100
				o = round(o,3)			
				po = str(o) + " "+" %"					
				q = [" " , a[dev_idx] , addtime, po]
				writer.writerow(q)
				dev_idx = dev_idx + 4	#move on to the next device in the list, it's 4 places away from the current one
				rsp_idx = rsp_idx + 4	
				cnt_idx = cnt_idx + 4
				avg_idx = avg_idx + 4		
			z = [" "]
			writer.writerow(z)
			writer.writerow(z)
			writer.writerow(z)
	u =  ["Suggested Polling Settings(ms)",]
	writer.writerow(u)
	dev_idx = 0
	max_idx = 1
	while max_idx < len(max_print_list):
		if max_print_list[max_idx] < 6000.00:					
			u =  [" ",max_print_list[dev_idx],max_print_list[max_idx]]
			#print u
			writer.writerow(u)
		else:
			
			tmpstr = str(max_print_list[max_idx] - 300)
			tmpstr = "  Outlier at: " + tmpstr + "  set wait time accordingdly for this specific device"
			u =  [" ",max_print_list[dev_idx],backup_max[backup_max.index(max_print_list[dev_idx]) + 1] + 300,tmpstr]
			writer.writerow(u)
		max_idx = max_idx + 2
		dev_idx = dev_idx + 2
	z = [" "]
	writer.writerow(z)
	writer.writerow(z)
	writer.writerow(z)
	u = [" " , "Current Time Spent Waiting on Failed Messages(minutes per day)" , "Estimated New Time Spent Waiting(minutes per day)","**NOTE: Some channels may be missing from this list due to insufficient data"]
	writer.writerow(u)
	max_idx = 5
	while max_idx < len(pred_list):		
		u = [pred_list[max_idx - 5] , round(pred_list[max_idx-3],2), round(pred_list[max_idx-2],2)]
		writer.writerow(u)
		max_idx = max_idx + 6
print "Script finished."
f.close()
