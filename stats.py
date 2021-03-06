import csv_parser
import sql_out_parser
import operator
import datetime
import plotly.plotly as pl
from plotly.graph_objs import *
import plotly.exceptions
import collections as cols
from arguments import Arguments
from messages import *

class WordCloudBuilder:
	def __init__(self):
		# read ignored words
		ignoredFile = open("ignore_words.list", "r")
		self.ignoredWords = []
		for line in ignoredFile:
			self.ignoredWords.append(line[:-1])

		self.delimeters = ".,\\/><[]{}()!@#$%^&*:;\"\'?1234567890\n"

	def generateWordsCloud(self, messages):
		# clear messages from delimeters
		for d in self.delimeters:
			for message in messages:
				message._message = message._message.replace(d, ' ').lower()

		# generate most used words dictionary
		word_map = {}
		for message in messages:
			for word in message._message.split( ):
				if word in word_map.keys():
					word_map[word] = word_map[word] + 1
				else:
					word_map[word] = 1

		# and sort it
		sorted_map = reversed(sorted(word_map.items(), key=operator.itemgetter(1)))

		return sorted_map

	def printCloud(self, output, words):
		for word in words:
			if len(word[0]) > 2 and word[1] > 2 and word[0].lower() not in self.ignoredWords:
				output.write(word[0] + '(' + str(word[1]) + ') ')
		output.write('\n\n\n\n')

class Stats:
	def __init__(self):
		self.builded = False
		self.messages = None
		self.myMessages = None
		self.partnerMessages = None
		self.totalMessagesCount = 0
		self.myMessagesCount = 0
		self.partnerMessagesCount = 0
		self.myMessagesAverageLength = 0
		self.partnerMessagesAverageLength = 0
		self.firstMessage = None
		self.lastMessage = None
		self.totalDaysCount = 0
		self.averageMessagesPerDay = 0
		self.myMsgPercentage = 0
		self.wordCloudBuilder = WordCloudBuilder()
		self.statsName = ""
		self.messageDistribution = None

	def build(self, csv_names = None, db_names = None, writeDebugLog = False):
		self.statsName = "Nastya"
		self.builded = True
		self.messages = []

		if csv_names is not None:
			for filename in csv_names:
				print "reading ", filename
				messages = csv_parser.buildMessagesArray(filename, writeDebugLog)
				self.messages = makeUnitedArray(self.messages, messages)

		if db_names is not None:
			for filename in db_names:
				print "reading ", filename
				messages = sql_out_parser.buildMessagesArray(filename, writeDebugLog)
				self.messages = makeUnitedArray(self.messages, messages)

		if writeDebugLog:
			f = open('debug_res.txt', 'w')
			for msg in self.messages:
				msg.out(f, True)


		self.firstMessage = self.messages[0]
		self.lastMessage = self.messages[0]

		self.totalMessagesCount = len(self.messages)
		self.myMessages = []
		self.partnerMessages = []

		myMessagesLength = 0
		partnerMessagesLength = 0

		for msg in self.messages:
			# find first and last message time
			if msg._datetime < self.firstMessage._datetime:
				self.firstMessage = msg

			if msg._datetime > self.lastMessage._datetime:
				self.lastMessage = msg

			# find number and length of messages
			if len(msg._author) == 2: # f*cking unicode
				self.myMessages.append(msg)
				myMessagesLength = myMessagesLength + len(msg._message)
			else:
				self.partnerMessages.append(msg)
				partnerMessagesLength = partnerMessagesLength + len(msg._message)

		self.myMessagesCount = len(self.myMessages)
		self.partnerMessagesCount = len(self.partnerMessages)

		self.totalDaysCount = (self.lastMessage._datetime - self.firstMessage._datetime).days
		self.myMessagesAverageLength = myMessagesLength / self.myMessagesCount
		self.partnerMessagesAverageLength = partnerMessagesLength / self.partnerMessagesCount

		self.myMsgPercentage = self.myMessagesCount * 100 / self.totalMessagesCount

		self.averageMessagesPerDay = self.totalMessagesCount / self.totalDaysCount

	def buildTimeline(self, date = None):
		timeline = {}

		for i in range(0, 24):
			timeline[i] = 0

		for msg in self.messages:
			timeline[msg._datetime.hour] += 1

		return timeline

	def buildMessageDistribution(self):
		if self.messageDistribution is not None:
			return self.messageDistribution

		distribution = {}

		date = self.firstMessage._datetime.date()
		while date <= self.lastMessage._datetime.date():
			distribution[str(date)] = 0
			date += datetime.timedelta(days=1)

		for msg in self.messages:
			date = str(msg._datetime.date())
			if date in distribution.keys():
				distribution[date] += 1
			else:
				distribution[date] = 1
		self.messageDistribution = cols.OrderedDict(sorted(distribution.items()))
		return self.messageDistribution


	def buildTotalWordCloud(self, out = None):
		words = self.wordCloudBuilder.generateWordsCloud(self.messages)
		if out is not None:
			out.write("\nWords cloud:\n")
			self.wordCloudBuilder.printCloud(out, words)

	def buildMyWordCloud(self, out = None):
		myWords = self.wordCloudBuilder.generateWordsCloud(self.myMessages)
		if out is not None:
			out.write("\nMy words cloud:\n")
			self.wordCloudBuilder.printCloud(out, myWords)


	def buildPartnerWordCloud(self, out = None):
		partnerWords = self.wordCloudBuilder.generateWordsCloud(self.partnerMessages)
		if out is not None:
			out.write("\nPartner words cloud:\n")
			self.wordCloudBuilder.printCloud(out, partnerWords)

	def printSimpleStats(self, out):
		out.write("First message was " + str(self.firstMessage._datetime) + '\n')
		out.write("Last message was " + str(self.lastMessage._datetime) + '\n')
		out.write("Whole number of days: " + str(self.totalDaysCount) + '\n')

		out.write("\nNumber of messages: " + str(self.totalMessagesCount) + '\n')

		out.write("Average number of messages per day: " + str(self.averageMessagesPerDay) + '\n')

		out.write("\nMy messages number: " + str(self.myMessagesCount) + ' [' + str(self.myMsgPercentage) + '%]\n')
		out.write("Partner messages number: " + str(self.partnerMessagesCount) + ' [' + str(100 - self.myMsgPercentage) + '%]\n')

		out.write("\nMy average message length: " + str(self.myMessagesAverageLength) + '\n')
		out.write("Partner average message length: " + str(self.partnerMessagesAverageLength) + '\n')

	def plotTimeline(self, out = None):
		timeline = self.buildTimeline()

		data = Data([
			Bar(
				x = timeline.keys(),
				y = timeline.values()
			)
		])
		name = 'Timeline ' + self.statsName
		plotUrl = self.__plot(data, name)

		if out is not None:
			out.write("\nTimeline of messages: " + plotUrl + "\n")

	def plotMessageDistribution(self, out = None):
		distr = self.buildMessageDistribution()

		data = Data([
   			Scatter(
        		x=distr.keys(),
        		y=distr.values()
    		)
		])
		name = 'Message distribution ' + self.statsName
		plotUrl = self.__plot(data, name)

		if out is not None:
			out.write("message distribution plot: " + plotUrl + "\n")

	def plotMessageTimeDistribution(self, out = None):
		distr = self.buildMessageDistribution()

		# build timeline per day
		# hour1:
		#	date1: messageCount
		#	date2: messageCount
		# hour2:
		#	date1: messageCount
		#	date2: messageCount
		hours = {}
		for hour in range(0,24):
			distribution = {}
			for day in distr.keys():
				distribution[day] = 0

			for msg in self.messages:
				if msg._datetime.hour == hour:
					date = str(msg._datetime.date())
					if date in distribution.keys():
						distribution[date] += 1
					else:
						distribution[date] = 1
			hours[hour] = cols.OrderedDict(sorted(distribution.items()))

		# now count per day percentage
		for date in distr:
			for hour in hours.keys():
				if distr[date] <> 0:
					hours[hour][date] /= float(distr[date]) / 100.0
				else:
					hours[hour][date] = 0

		# and sum from the lowest to the highest
		for date in distr:
			for hour in hours.keys()[1:]:
				hours[hour][date] += hours[hour - 1][date]


		tracers = []
		for hour in hours.keys():
			trace = Scatter(
				x = hours[hour].keys(),
				y = hours[hour].values(),
				mode = 'lines',
				line = Line(
					width = 0.5
				),
				fill = 'tonexty'
			)
			tracers.append(trace)

		data = Data(tracers)
		layout = Layout(
    		showlegend=True,
    		xaxis=XAxis(
        		type='category',
    		),
    		yaxis=YAxis(
        		type='linear',
        		range=[1, 100],
        		dtick=20,
        		ticksuffix='%'
    		)
		)
		fig = Figure(data=data, layout=layout)
		plotUrl = self.__plot(fig, "Message time distribution " + self.statsName)

		if out is not None:
			out.write("Message time distribution plot: " + plotUrl)

		return plotUrl


	def __plot(self, data, name):
		try:
			return pl.plot(data, fileopt='overwrite', auto_open=False, filename=name)
		except plotly.exceptions.PlotlyError as pe:
			print "Plotly error"
			print pe
			return "Not builded"

def parseNames(line):
	return line.split('|') if line is not None else None

def initCommandLineArgs():
	args = Arguments()
	args.addNewArg('force_all', '-all', 'Force building of all statistics', True)
	args.addNewArg('no_debug', '-nd', "Don't build debug output", True)
	args.addNewArg('words_cloud', '-wc', "Build words cloud (slow)", True)
	args.addNewArg('timeline', '-ptm', "Build timeline plot fo whole chat", True)
	args.addNewArg('distribution', '-pmd', "Build message distribution per day plot")
	args.addNewArg('time_distribution', '-ptmd', "Build message times distribution per days plot", True)
	args.addNewArg('database', '-db', "Use info from database extracted file. Files should be listed with | separator")
	args.addNewArg('csv', '-csv', "Use info from csv files. Files should be listed using | separator")
	args.addNewArg('help', 'help', "Show this page")
	return args

# This module can be used as standalone script
if __name__ == '__main__':
	import sys 		# Use this only in standalone mode
	args = initCommandLineArgs()

	paramsNum = len(sys.argv)
	if paramsNum < 2:
		args.printHelp()

	args.parseArgs(sys.argv[1:], True)

	csv_names = parseNames(args.getValue('csv'))
	db_names = parseNames(args.getValue('database'))

	buildDebug = not args.getValue('no_debug')
	buildWordsCloud = args.getValue('words_cloud')
	plotTimeline = args.getValue('timeline')
	plotMessageDistribution = args.getValue('distribution')
	plotTimeMessageDistribution = args.getValue('time_distribution')

	if args.getValue('force_all'):
		print 'All stats forced'
		buildDebug = True
		buildWordsCloud = True
		plotTimeline = True
		plotMessageDistribution = True
		plotTimeMessageDistribution = True

	out = open("stats_{0}.txt".format(csv_names[0][:-4]), "w")
	stats = Stats()

	print "Building simple stats..."
	stats.build(csv_names, db_names, writeDebugLog=buildDebug)
	stats.printSimpleStats(out)

	if plotTimeline:
		print "Building timeline..."
		stats.plotTimeline(out)

	if plotMessageDistribution:
		print "Plotting message distribution..."
		stats.plotMessageDistribution(out)

	if plotTimeMessageDistribution:
		out.write("\n\n")
		print "Plotting messages time distribution..."
		stats.plotMessageTimeDistribution(out)

	if buildWordsCloud:
		print "Building total words cloud..."
		stats.buildTotalWordCloud(out)
		print "Building my words cloud..."
		stats.buildMyWordCloud(out)
		print "Building partner words cloud..."
		stats.buildPartnerWordCloud(out)
	out.close()