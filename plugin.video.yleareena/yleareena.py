# -*- coding: utf-8 -*-
import os,subprocess
import urllib,urllib2,re
import xbmcplugin,xbmcgui,xbmcaddon
import xbmcutil as xbmcUtil
import simplejson as json
from datetime import date
import time
import datetime
import os, sys, inspect

#sets default encoding to utf-8
reload(sys) 
sys.setdefaultencoding('utf8')

#for windows add Crypto module folder 
if sys.platform == 'win32':
	cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"win32")))
	if cmd_subfolder not in sys.path:
		sys.path.insert(0, cmd_subfolder)
	 
try:
	#import yle-dl (version 2.0.1)
	yledl = __import__('lib.yle-dl', globals(), locals(), ['yle-dl'], -1)
except ImportError as e:
	xbmc.log(str(e), level=xbmc.LOGERROR )
	xbmcUtil.notification('Error', str(e))
	sys.exit();


def scrapVideo(url):
	
	url = yledl.encode_url_utf8(url)
	dl = yledl.downloader_factory(url)
	playlist = dl.get_playlist(url, True)
	clip = playlist[0]

	rtmpparams = dl.get_rtmp_parameters(clip, url)
	enc = sys.getfilesystemencoding()
	rtmpUrl = dl.rtmp_parameters_to_url(rtmpparams).encode(enc, 'replace')
	
	xbmc.log(url + " -> " + rtmpUrl)
	return rtmpUrl

def readJSON(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	try:	
		response = urllib2.urlopen(req)
		content=response.read()	
		response.close()				
		jsonObj = json.loads(content)
		return jsonObj
	except IOError as e:
		xbmc.log(str(e), level=xbmc.LOGERROR )
		xbmcUtil.notification('Error', str(e))
		return [];

today = str(date.today())
tomorrow = str(datetime.date.today() + datetime.timedelta(days=1))
yesterday = str(datetime.date.today() + datetime.timedelta(days=-1))
day_minus_2 = str(datetime.date.today() + datetime.timedelta(days=-2))
day_minus_3 = str(datetime.date.today() + datetime.timedelta(days=-3))
day_minus_4 = str(datetime.date.today() + datetime.timedelta(days=-4))
day_minus_5 = str(datetime.date.today() + datetime.timedelta(days=-5))
def relativeDay(day):
	if day==tomorrow:
		return u'Huomenna'
	if day==today:
		return u'Täänän'
	if day==yesterday:
		return u'Eilen'
	if day==day_minus_2:
		return getWeekday(datetime.date.today().weekday()-2) + ' (' + day + ')'
	if day==day_minus_3:
		return getWeekday(datetime.date.today().weekday()-3) + ' (' + day + ')'
	if day==day_minus_4:
		return getWeekday(datetime.date.today().weekday()-4) + ' (' + day + ')'
	if day==day_minus_5:
		return getWeekday(datetime.date.today().weekday()-5) + ' (' + day + ')'
	
	return day

#w={0:'Maanantai',1:'Tiistai',2:'Keskiviikko',3:'Torstai',4:'Perjantai',5:'Lauantai',6:'Sunnuntai'}

def getWeekday(weekday):
	if weekday<0: weekday+=7
	if weekday==0: return u'Maanantai'
	if weekday==1: return u'Tiistai'
	if weekday==2: return u'Keskiviikko'
	if weekday==3: return u'Torstai'
	if weekday==4: return u'Perjantai'
	if weekday==5: return u'Lauantai'
	if weekday==6: return u'Sunnuntai'
	
class YleAreenaAddon (xbmcUtil.ViewAddonAbstract):
	GROUP = u'   [COLOR blue]%s[/COLOR]'
	NEXT = '[COLOR blue]   ➔  NEXT  ➔[/COLOR]'
	EXPIRES_HOURS = u'[COLOR red]%dh[/COLOR] %s'
	EXPIRES_DAYS = u'[COLOR brown]%dpv[/COLOR] %s'
	FAVOURITE = u'[COLOR yellow]★[/COLOR] %s'
	REMOVE = u'[COLOR red]✖[/COLOR] %s'	
	
	def __init__(self):
		self.setAddonId('plugin.video.yleareena')

		self.favSeries = {}
		self.initFavourites()
 		self.addHandler(None, self.handleMain)
		self.addHandler('programs', self.handlePrograms)
		self.addHandler('serie', self.handleSerie)
		self.addHandler('live', self.handleLive)
	
	def initFavourites(self):
		fav = self.addon.getSetting("fav")
		if fav:
			try:
				favList = eval(fav)
				for title, link in favList.items():
					self.favSeries[title] = link
			except:
				pass
		
	def handleMain(self, pg, args):
		self.addViewLink('» Ohjelmat','programs',1, {'link':'http://areena.yle.fi/tv/kaikki.json?jarjestys=ao' } )
		self.addViewLink('Uutiset','serie', 1, {'link':'http://areena.yle.fi/tv/uutiset/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink('Suora','live', 0, {'link':'http://areena.yle.fi/tv/suora.json?from=0&to=24' } )
		self.addViewLink('Lapset','serie', 1, {'link':'http://areena.yle.fi/tv/lapset/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink('Sarjat ja elokuvat','serie', 1, {'link':'http://areena.yle.fi/tv/sarjat-ja-elokuvat/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink('Viihde ja kulttuuri','serie', 1, {'link':'http://areena.yle.fi/tv/viihde-ja-kulttuuri/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink('Dokumentit ja fakta','serie', 1, {'link':'http://areena.yle.fi/tv/dokumentit-ja-fakta/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink('Urheilu','serie', 1, {'link':'http://areena.yle.fi/tv/urheilu/kaikki.json?jarjestys=uusin', 'grouping':True } )
		
		for key in  self.favSeries.iterkeys():
			self.addViewLink(self.FAVOURITE % key, 'serie', 1, 
							{'link':self.favSeries[key] + '.json?from=0&to=24&sisalto=ohjelmat'},
							[(self.createContextMenuAction(self.REMOVE % 'Remove', 'removeFav', {'name':key}) )] )
	
	def handlePrograms(self, pg, args):
		link = args['link']+self.getPageQuery(pg, 100) if 'link' in args else ''
		if link != '':
			items = readJSON(link)
			for item in items['search']['results']:
				if 'series' in item:
					serie = item['series']
					title = serie['name']
					
					img = serie['images']['M']
					link='http://areena.yle.fi/tv/' + serie['id'] + '.json?from=0&to=24&sisalto=ohjelmat'	
					if title in self.favSeries:
						title = self.FAVOURITE % title
						cxm = []
					else:
						cxm = [ (self.createContextMenuAction(self.FAVOURITE % 'Mark as favourite', 'addFav', {'name':title, 'link':link}) )  ]
					self.addViewLink(title,'serie',1, {'link':link }, infoLabels={'plot': serie['shortDesc']},contextMenu=cxm )
			if len(items['search']['results']) == 100:
					self.addViewLink(self.NEXT,'programs', pg+1, args )
	
	def handleAction(self, action, params):
		if action=='addFav':
			self.favSeries[params['name'].encode("utf-8")] = params['link']
			favStr = repr(self.favSeries)
			self.addon.setSetting('fav', favStr)
			xbmcUtil.notification('Success', "Added: " + params['name'].encode("utf-8") )
		elif action=='removeFav':
			self.favSeries.pop(params['name'])
			favStr = repr(self.favSeries)
			self.addon.setSetting('fav', favStr)
			xbmcUtil.notification('Removed', unicode(params['name'], "utf-8").encode("utf-8") )
		else:
			super(ViewAddonAbstract, self).handleAction(self, action, params)
		
	def handleLive(self, pg, args):
		items = readJSON(args['link'])

		for i in range(0, len(items['current'])) :
			item = items['current'][i]

			startTime = item['start'][11:16]
			img = item['pubContent']['images']['orig']
			title = u"[COLOR red]◉[/COLOR] " + startTime + ' | ' + item['pubContent']['title'] 
			plot = item['pubContent']['desc']
			link = 'http://areena.yle.fi/tv/' + item['pubContent']['id']
			
			self.addVideoLink(title, link, img, infoLabels={'plot': plot })
		if 'upcoming' in items:
			for days in items['upcoming']:
				day = relativeDay( days['day'][:10])
				if day != u'Täänän': 
					self.addVideoLink('   [COLOR blue]' + day + '[/COLOR]', '', '')
				
				for item in days['items']:
					if datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S')[:13] == item['start'][:13]:
						title = u"[COLOR orange]◉[/COLOR] "
					else:
						title = u"◉ "
					startTime = item['start'][11:16]
					img = item['pubContent']['images']['orig']
					title +=  startTime + ' | ' + item['pubContent']['title'] 
					plot = item['pubContent']['desc']
					link = 'http://areena.yle.fi/tv/' + item['pubContent']['id']
					
					self.addVideoLink(title, link, img, infoLabels={'plot': plot })
        
	DEFAULT_PAGE_SIZE = 30
	def getPageQuery(self, pg, pageSize=DEFAULT_PAGE_SIZE):
		if pg>0:
			pgFrom = (pg - 1) * pageSize
			pgTo = pg * pageSize
			return '&from=%s&to=%s' % (pgFrom, pgTo)
		else:
			return ''
	
	def handleSerie(self, pg, args):
		grouping = args['grouping'] if 'grouping' in args else False
		groupName = ''
		link = args['link']+self.getPageQuery(pg) if 'link' in args else ''
		print link
		if link != '':
			items = readJSON(link)
			if 'search' in items:
				for item in items['search']['results']:
					title = item['title']
					episodeNumber = ''
					if 'episodeNumber' in item and int(item['episodeNumber'])<1000:				
						episodeNumber = str(item['episodeNumber'])
						title += ' #' + episodeNumber
					#elif 'published' in item:
					#	title += ' #' + item['published'][:10]
					
					duration = str(item['durationSec'])	if 'durationSec' in item else ''
					plot = item['desc'] if 'desc' in item and item['desc'] != None else ''
					plot += '\r\nPublished: ' + item['published'] if 'published' in item else ''
					
					expiresInHours = -1
					if 'expires' in item and item['expires'] != None:
						try:
							expiresInHours = int((time.mktime(time.strptime(item['expires'], "%Y-%m-%dT%H:%M:%S")) - time.time())/(60*60))
							plot += u"\n\rExpires: " + str(item['expires'])
						except:
							xbmc.log('Could not parse ' + item['expires'], level=xbmc.LOGWARNING )							
						
					img = item['images']['M']
					link='http://areena.yle.fi/tv/' + item['id']
					if 'series' in item:
						serieName = item['series']['name']
						serieLink = 'http://areena.yle.fi/tv/' + item['series']['id']
						contextMenu = [ (self.createContextMenuAction(self.FAVOURITE % 'Mark as favourite', 'addFav', {'name':serieName, 'link':serieLink}) )  ]
						if not item['title'].upper().startswith(serieName.upper()):
							title = serieName + ': ' + title
					else:
						contextMenu = []
					if grouping:						
						if 'published' in item and groupName != relativeDay(item['published'][:10]):
							groupName = relativeDay(item['published'][:10])
							if groupName != u'Täänän':
								self.addVideoLink(self.GROUP % groupName, '', '')
					
					if expiresInHours<24 and expiresInHours>=0:
						title = self.EXPIRES_HOURS % (expiresInHours, title);
					elif expiresInHours<120 and expiresInHours>=0:
						title = self.EXPIRES_DAYS % (expiresInHours/24, title);
					
					self.addVideoLink(title, link, img, infoLabels={'duration':duration, 'plot': plot, 'episode': episodeNumber, 'date': item['published'] }, contextMenu=contextMenu)
				
				if len(items['search']['results']) == self.DEFAULT_PAGE_SIZE:
					self.addViewLink(self.NEXT,'serie', pg+1, args )

	def handleVideo(self, link):
		videoLink = scrapVideo(link)
		return videoLink

#-----------------------------------

yleAreenaAddon = YleAreenaAddon()
yleAreenaAddon.handle()