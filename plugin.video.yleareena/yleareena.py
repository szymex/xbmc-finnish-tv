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
import CommonFunctions

#Lisätty Debug
settings = xbmcaddon.Addon('plugin.video.yleareena')
localize = settings.getLocalizedString
common = CommonFunctions
if settings.getSetting('debug') == "true":
  common.dbg = True
else:
  common.dbg = False
#Debug loppu

#sets default encoding to utf-8
reload(sys) 
sys.setdefaultencoding('utf8')

#for windows add Crypto module folder 
if sys.platform == 'win32':
	cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"win32")))
	if cmd_subfolder not in sys.path:
		sys.path.insert(0, cmd_subfolder)

#for OSX add Crypto module folder 
if sys.platform == 'darwin':
	cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"osx")))
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

	media = clip.get('media', {})
	subtitles = media.get('subtitles', [])
	subtitlesFiles = []
	if len(subtitles)>0:	
		videoname = url.split('/')[-1];
		path = os.path.join(xbmc.translatePath(yleAreenaAddon.addon.getAddonInfo("profile") ).decode("utf-8"), videoname)
		
		for sub in subtitles:
			lang = sub.get('lang', '')
			url = sub.get('url', None)
			if url:
				try:
					subtitlefile = path + '.' + lang + '.srt'
					enc = sys.getfilesystemencoding()
					urllib.urlretrieve(url, subtitlefile.encode(enc, 'replace'))
					subtitlesFiles.append(subtitlefile)
				except IOError, exc:
					xbmc.log(u'Failed to download subtitles from: ' + url)

	return (rtmpUrl, subtitlesFiles)

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
		return lang(33007)
	if day==today:
		return lang(33006)
	if day==yesterday:
		return lang(30010)
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
	if weekday==0: return lang(11)
	if weekday==1: return lang(12)
	if weekday==2: return lang(13)
	if weekday==3: return lang(14)
	if weekday==4: return lang(15)
	if weekday==5: return lang(16)
	if weekday==6: return lang(17)
	
class YleAreenaAddon (xbmcUtil.ViewAddonAbstract):
	ADDON_ID = 'plugin.video.yleareena'
	DEFAULT_LANG = 'fin'
	LANGUAGES = ['fin','fih','swe','swh','sme','None']
	
	def __init__(self):
		xbmcUtil.ViewAddonAbstract.__init__(self)
		self.initConst()
		self.favSeries = {}
		self.initFavourites()
 		self.addHandler(None, self.handleMain)
		self.addHandler('programs', self.handlePrograms)
		self.addHandler('serie', self.handleSerie)
		self.addHandler('live', self.handleLive)
		try:
			self.DEFAULT_LANG = self.LANGUAGES[int(self.addon.getSetting("lang"))]
		except:
			pass
	
	def initConst(self):
		self.NEXT = '[COLOR blue]   ➔  %s  ➔[/COLOR]' % self.lang(33078)
		self.GROUP = u'   [COLOR blue]%s[/COLOR]'
		self.EXPIRES_HOURS = u'[COLOR red]%d' + self.lang(30002) + '[/COLOR] %s'
		self.EXPIRES_DAYS = u'[COLOR brown]%d' + self.lang(30003) + '[/COLOR] %s'
		self.FAVOURITE = '[COLOR yellow]★[/COLOR] %s'
		self.REMOVE = u'[COLOR red]✖[/COLOR] %s' % self.lang(1210)
		
	def initFavourites(self):
		fav = self.addon.getSetting("fav")
		if fav:
			try:
				favList = eval(fav)
				for title, link in favList.items():
					self.favSeries[title] = link
			except:
				pass
		else:
			self.addon.setSetting("fav", repr(self.favSeries))
		
	def handleMain(self, pg, args):
		self.addViewLink('» ' + self.lang(30020),'programs',1, {'link':'http://areena.yle.fi/tv/kaikki.json?jarjestys=ao' } )
		self.addViewLink(self.lang(30021),'serie', 1, {'link':'http://areena.yle.fi/tv/uutiset/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink(self.lang(30022),'live', 0, {'link':'http://areena.yle.fi/tv/suora.json?from=0&to=24' } )
		self.addViewLink(self.lang(30023),'serie', 1, {'link':'http://areena.yle.fi/tv/lapset/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink(self.lang(30024),'serie', 1, {'link':'http://areena.yle.fi/tv/sarjat-ja-elokuvat/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink(self.lang(30025),'serie', 1, {'link':'http://areena.yle.fi/tv/viihde-ja-kulttuuri/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink(self.lang(30026),'serie', 1, {'link':'http://areena.yle.fi/tv/dokumentit-ja-fakta/kaikki.json?jarjestys=uusin', 'grouping':True } )
		self.addViewLink(self.lang(30027),'serie', 1, {'link':'http://areena.yle.fi/tv/urheilu/kaikki.json?jarjestys=uusin', 'grouping':True } )
		
		for key in  self.favSeries.iterkeys():
			self.addViewLink(self.FAVOURITE % key, 'serie', 1, 
							{'link':self.favSeries[key] + '.json?from=0&to=24&sisalto=ohjelmat'},
							[(self.createContextMenuAction(self.REMOVE, 'removeFav', {'name':key}) )] )
	
	def handlePrograms(self, pg, args):
		link = args['link']+self.getPageQuery(pg, 100) if 'link' in args else ''
		if link != '':
			items = readJSON(link)
			xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
			for item in items['search']['results']:
				if 'series' in item and item['series']['name'] != None:
					serie = item['series']
					title = serie['name']
					
					img = serie['images']['M']
					link='http://areena.yle.fi/tv/' + serie['id'] + '.json?from=0&to=24&sisalto=ohjelmat'	
					if title in self.favSeries:
						title = self.FAVOURITE % title
						cxm = []
					else:
						cxm = [ (self.createContextMenuAction(self.FAVOURITE % self.lang(14076), 'addFav', {'name':title, 'link':link}) )  ]
					self.addViewLink(title,'serie',1, {'link':link }, infoLabels={'plot': serie['shortDesc']},contextMenu=cxm )
			if len(items['search']['results']) == 100:
					self.addViewLink(self.NEXT,'programs', pg+1, args )
	
	def handleAction(self, action, params):
		if action=='addFav':
			self.favSeries[params['name'].encode("utf-8")] = params['link']
			favStr = repr(self.favSeries)
			self.addon.setSetting('fav', favStr)
			xbmcUtil.notification(self.lang(30006), params['name'].encode("utf-8") )
		elif action=='removeFav':
			self.favSeries.pop(params['name'])
			favStr = repr(self.favSeries)
			self.addon.setSetting('fav', favStr)
			xbmcUtil.notification(self.lang(30007), unicode(params['name'], "utf-8").encode("utf-8") )
		else:
			super(ViewAddonAbstract, self).handleAction(self, action, params)
		
	def handleLive(self, pg, args):
		items = readJSON(args['link'])

		xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
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
				if day != self.lang(33006): 
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
				xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
				for item in items['search']['results']:
					title = item['title']
					episodeNumber = ''
					if 'episodeNumber' in item and int(item['episodeNumber'])<1000:				
						episodeNumber = int(item['episodeNumber'])
						title += ' #' + str(episodeNumber)
					#elif 'published' in item:
					#	title += ' #' + item['published'][:10]
					
					published = item['published'].replace('T', ' ') if 'published' in item else ''
					plot = item['desc'] if 'desc' in item and item['desc'] != None else ''
					plot += '\r\n%s: %s' % (self.lang(30008),published) if published != '' else ''
					
					expiresInHours = -1
					expiresText = None
					if 'expires' in item and item['expires'] != None:
						try:
							expiresInHours = int((time.mktime(time.strptime(item['expires'], "%Y-%m-%dT%H:%M:%S")) - time.time())/(60*60))
							#plot += u"\n\r%s: %s" % (self.lang(30009), str(item['expires']) )
							expiresText = item['expires'].replace('T', ' ')
						except:
							xbmc.log('Could not parse ' + item['expires'], level=xbmc.LOGWARNING )							
						
					img = item['images']['M']
					link='http://areena.yle.fi/tv/' + item['id']
					if 'series' in item:
						serieName = item['series']['name']
						serieLink = 'http://areena.yle.fi/tv/' + item['series']['id']
						contextMenu = [ (self.createContextMenuAction(self.FAVOURITE % self.lang(14076), 'addFav', {'name':serieName, 'link':serieLink}) )  ]
						if serieName != None and not item['title'].upper().startswith(serieName.upper()):
							title = serieName + ': ' + title
					else:
						contextMenu = []
					if grouping:						
						if 'published' in item and groupName != relativeDay(item['published'][:10]):
							groupName = relativeDay(item['published'][:10])
							if groupName != self.lang(33006):
								self.addVideoLink(self.GROUP % groupName, '', '')
					
					if expiresInHours<24 and expiresInHours>=0:
						title = self.EXPIRES_HOURS % (expiresInHours, title);
						expiresText = '[COLOR red]%s[/COLOR]' % expiresText
					elif expiresInHours<120 and expiresInHours>=0:
						title = self.EXPIRES_DAYS % (expiresInHours/24, title);
						expiresText = '[COLOR red]%s[/COLOR]' % expiresText
						
					plot = plot + u"\n\r%s: %s" % (self.lang(30009), expiresText) if expiresText != None else plot
					
					isInternational = self.addon.getSetting("international")=='true'
					if isInternational and 'international' in item and not item['international']:
						continue

					self.addVideoLink(title, link, img, infoLabels={'plot': plot,'duration':str(item.get('duration','')), 'episode': episodeNumber,'aired': published[:10], 'date': published }, 
									  contextMenu=contextMenu, videoStreamInfo={'duration':item['durationSec']})
				
				if len(items['search']['results']) == self.DEFAULT_PAGE_SIZE:
					self.addViewLink(self.NEXT,'serie', pg+1, args )

	def playVideo(self, link):
		resolvedVideoLink, subtitleFiles = scrapVideo(link)
		if (resolvedVideoLink!=None):
			liz=xbmcgui.ListItem(path=resolvedVideoLink)
			xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
			
			if len(subtitleFiles)>0:
				player = xbmc.Player()
				i = 0				
				while not player.isPlaying() or (player.isPlaying() and resolvedVideoLink != player.getPlayingFile()):
					i += 1
					time.sleep(1)
					if i > 20:
						break
				if player.isPlaying() and resolvedVideoLink == player.getPlayingFile():
					defaultSubtitleFile = None
					
					#find default subtitle file
					for subfile in subtitleFiles:				
						if self.DEFAULT_LANG in subfile: 
							defaultSubtitleFile = subfile

					#add other subtitles
					for subfile in subtitleFiles:				
						if defaultSubtitleFile != subfile: xbmc.Player().setSubtitles(subfile)
					
					if defaultSubtitleFile != None:					
						xbmc.Player().setSubtitles(defaultSubtitleFile)
					xbmc.Player().showSubtitles(defaultSubtitleFile != None)

		else:
			print ("could not play " + link)
			notification(header="Warning", message="Could not find video.")

	def handleVideo(self, link):
		videoLink = scrapVideo(link)
		return videoLink

#-----------------------------------

yleAreenaAddon = YleAreenaAddon()
lang = yleAreenaAddon.lang
yleAreenaAddon.handle()
