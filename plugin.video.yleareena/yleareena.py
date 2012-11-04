# -*- coding: utf-8 -*-
import os,subprocess
import urllib,urllib2,re
import xbmcplugin,xbmcgui,xbmcaddon
import xbmcUtil
import simplejson as json

import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"win32")))
if cmd_subfolder not in sys.path:
     sys.path.insert(0, cmd_subfolder)

#import yle-dl (version 2.0.1)
yledl = __import__('lib.yle-dl', globals(), locals(), ['yle-dl'], -1)

yledl.encode_url_utf8('')

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
	print url
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

class YleAreenaAddon (xbmcUtil.ViewAddonAbstract):
	def __init__(self):
		self.setAddonId('plugin.video.yleareena')

		self.favSeries = {}
		try:
			strCat = open(os.path.join(self.BASE_PATH,'favourites.txt')).read().split('\n')
			for cat in strCat:
				splCat = cat.split("|")				
				if (len(splCat)==2):
					name = splCat[0].strip()
					link = splCat[1].strip()
					self.favSeries[name]=link
					xbmc.log(name + ' - ' + link, level=xbmc.LOGDEBUG)
		except:
			xbmc.log("Could not read categories from file: 'favourites.txt'", level=xbmc.LOGWARNING )

 		self.addHandler(None, self.handleMain)
		self.addHandler('programs', self.handlePrograms)
		self.addHandler('serie', self.handleSerie)

	def handleMain(self, pg, args):
		self.addViewLink('Ohjelmat','programs',1, {'link':'http://areena.yle.fi/tv/kaikki.json?from=0&to=200&jarjestys=ao' } )
		self.addViewLink('Sarjat ja elokuvat','serie', 1, {'link':'http://areena.yle.fi/tv/sarjat-ja-elokuvat/kaikki.json?from=0&to=24&jarjestys=uusin' } )
		self.addViewLink('Viihde ja kulttuuri','serie', 1, {'link':'http://areena.yle.fi/tv/viihde-ja-kulttuuri/kaikki.json?from=0&to=24&jarjestys=uusin' } )
		self.addViewLink('Dokumentit ja fakta','serie', 1, {'link':'http://areena.yle.fi/tv/dokumentit-ja-fakta/kaikki.json?from=0&to=24&jarjestys=uusin' } )
		self.addViewLink('Uutiset','serie', 1, {'link':'http://areena.yle.fi/tv/uutiset/kaikki.json?from=0&to=24&jarjestys=uusin', 'forceDate':'True' } )
		self.addViewLink('Urheilu','serie', 1, {'link':'http://areena.yle.fi/tv/urheilu/kaikki.json?from=0&to=24&jarjestys=uusin' } )
		self.addViewLink('Lapset','serie', 1, {'link':'http://areena.yle.fi/tv/lapset/kaikki.json?from=24&to=48&jarjestys=uusin' } )
		
		for key in  self.favSeries.iterkeys():
			self.addViewLink("[COLOR yellow]✶[/COLOR] " + key, 'serie', 1, 
							{'link':self.favSeries[key] + '.json?from=0&to=24&sisalto=ohjelmat'},
							[('[COLOR red]✖[/COLOR] Remove', 'RunScript(special://home/addons/plugin.video.yleareena/favourites.py,-remove,'+key+ ')')]  )
	
	def handlePrograms(self, pg, args):
		if 'link' in args:
			items = readJSON(args['link'])
			for item in items['search']['results']:
				if 'series' in item:
					serie = item['series']
					title = serie['name']
					
					img = serie['images']['M']
					link='http://areena.yle.fi/tv/' + serie['id'] + '.json?from=0&to=24&sisalto=ohjelmat'					
					self.addViewLink(title,'serie',1, {'link':link }, infoLabels={'plot': serie['shortDesc']},
									contextMenu=[('[COLOR yellow]✚[/COLOR] Mark as favourite', 'RunScript(special://home/addons/plugin.video.yleareena/favourites.py,-add,'+title+', http://areena.yle.fi/tv/' + serie['id']+ ')')])

	def handleSerie(self, pg, args):
		forceDate = False
		if 'forceDate' in args:
			forceDate = args['forceDate']
			
		if 'link' in args:
			items = readJSON(args['link'])
			if 'search' in items:
				for item in items['search']['results']:
					title = item['title']
					episodeNumber = ''
					if not forceDate and 'episodeNumber' in item and int(item['episodeNumber'])<1000:				
						episodeNumber = str(item['episodeNumber'])
						title += ' - [COLOR grey]' + episodeNumber  + '[/COLOR]'
					elif 'published' in item:
						title += ' - [COLOR grey]' + item['published'][:10] + '[/COLOR]'
					
					duration = ''
					if 'durationSec' in item:
						duration = str(item['durationSec'])
						
					plot = item['desc']
					img = item['images']['M']
					link='http://areena.yle.fi/tv/' + item['id']
					if 'series' in item:
						serieName = item['series']['name']
						serieLink = 'http://areena.yle.fi/tv/' + item['series']['id']
						contextMenu=[('[COLOR yellow]✚[/COLOR] Mark serie as favourite', 'RunScript(special://home/addons/plugin.video.yleareena/favourites.py,-add,'+serieName+', ' + serieLink+ ')')]
						if not item['title'].upper().startswith(serieName.upper()):
							title = '[COLOR grey]' + serieName + '[/COLOR]: ' + title
					else:
						contextMenu = []
						
					self.addVideoLink(title, link, img, infoLabels={'duration':duration, 'plot': item['desc'], 'episode': episodeNumber, 'date': item['published'] },
									contextMenu=contextMenu)
		
	def handleVideo(self, link):
		videoLink = scrapVideo(link)
		return videoLink

#-----------------------------------

yleAreenaAddon = YleAreenaAddon()
yleAreenaAddon.handle()

