# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import os,subprocess, json
import CommonFunctions
import xbmcutil as xbmcUtil
import inspect
import time
import datetime
from datetime import date
from bs4 import BeautifulSoup
import sys
dbg = True
import SimpleDownloader as downloader
import string

common = CommonFunctions
common.plugin = "plugin.video.ruutu"

#sets default encoding to utf-8
reload(sys) 
sys.setdefaultencoding('utf8')

def scrapRSS(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	content=response.read()
	response.close()
	match=re.compile("<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<description>.*?src='(.*?)'.*?br/&gt;(.*?)</description>.*?<pubDate>(.*?)</pubDate>.*?</item>", re.DOTALL).findall(content)
	#title, link, img, description, date
	return match

def scrapVideoId(url):
	
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	matchVideoId=re.compile("vid=(.*)").findall(response.geturl())

	response.close()
	return matchVideoId[0]

def scrapVideoLink(url):
	
	xbmc.log( url )
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	matchVideoId=re.compile("providerURL', '(http.*?)'").findall(response.read())
	response.close()
	videoUrl = urllib2.unquote( matchVideoId[0])
	
	req = urllib2.Request(videoUrl)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	videoLink = re.compile('<SourceFile>(.*?)</SourceFile>').findall(response.read())[0]
		
	return videoLink

def downloadVideo(url, title):
	valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
	videoUrl = scrapVideoLink(url)

	downloadPath = ruutu.addon.getSetting('download-path')
	if downloadPath == None or downloadPath == '': 
		downloadPath = '~/'
	downloadPath += url.split('/')[-2]
	if not os.path.exists(downloadPath):
		os.makedirs(downloadPath)

	filename = "%s %s" % (''.join(c for c in title if c in valid_chars), videoUrl.split(':')[-1] )

	params = {}
	params["url"] = videoUrl
	params["download_path"] = downloadPath
	xbmc.log(url + " " + filename + "   " + str(params))
	dw = downloader.SimpleDownloader()
	dw.download(filename, params)

def scrapSeries(url, pg=1):
	try:		
		#find serie id
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		content=response.read()	
		response.close()
	
		res = re.compile('episodes_1":\["(.*?)"\]').findall(content)
		if len(res)>0:
			serieId = res[0]
			url = 'http://www.ruutu.fi/views_cacheable_pager/videos_by_series/episodes_1/' + serieId + '?page=0%2C' + str(pg-1)
			return scrapPager(url)
		else:
			xbmcUtil.notification('Error', 'Could not find series')
			return None
	except Exception as e:
		xbmcUtil.notification('Error', str(e))
		return None
		
		

def scrapPager(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	try:	
		response = urllib2.urlopen(req)
		content=response.read()	
		response.close()				

		retList = []
		soup = BeautifulSoup(content)
		items = soup.findAll('article')
		for it in items:
			image = it.find('img').get('src') if it.find('img')!= None else ''
			link = it.select('h2 a')[0]['href']
			title = it.select('h2 a')[0].string
			episodeNum = ''
			for sec in it.select('footer .details-inline div'):
				for str in sec.stripped_strings:
					episodeNum += " " + str
			if len(episodeNum)>0: episodeNum = episodeNum[1:]
			selDuration = it.select('.field-name-field-duration')
			duration = selDuration[0].string.strip() if len(selDuration)>0 else ''
			duration = duration.replace(' min','')

			selAvailability = it.select('.availability-timestamp')
			available = selAvailability[0].string.strip() if len(selAvailability)>0 else '0'
			
			selDesc = it.select('.field-name-field-webdescription p')
			desc = selDesc[0].string.strip() if len(selDesc)>0 else '0'
			
			selAvailabilityText = it.select('.availability-text')
			availabilityText = selAvailabilityText[0].string.strip() if len(selAvailabilityText)>0 else ''
			#desc += '\n\r' + availabilityText
			
			selDetails = it.select('.details .field-type-text')
			details = selDetails[0].string.strip() if len(selDetails)>0 and selDetails[0].string!=None else ''
			
			selStartTime = it.select('.field-name-field-starttime')
			for str in selStartTime[0].stripped_strings:
				published = str

			retList.append( {'title':title, 'episodeNum':episodeNum, 'link':"http://www.ruutu.fi" + link, 'image':image, 'duration': duration, 
							'published':published,'available-text':availabilityText, 'available': available, 'desc':desc, 'details':details });
	except urllib2.HTTPError:
		retList=[];	

	return retList



def scrapJSON(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	try:	
		response = urllib2.urlopen(req)
		content=response.read()	
		response.close()				
		jsonObj = json.loads(content)
		return jsonObj
	except urllib2.HTTPError:
		return [];

def scrapPrograms():
	url = 'http://www.ruutu.fi/ajax/series-navi'
	result = common.fetchPage({"link": url})
	ret = common.parseDOM(result['content'], "div", {'class': 'view-content'})
	links = common.parseDOM(ret[0], "a", {'href': '*'}, 'href')
	names = common.parseDOM(ret[0], "a", {'href': '*'})
	retLinks = []
	for i in range(0, len(names) ):
		retLinks.append( {'link': "http://www.ruutu.fi" + str(links[i]), 'name': names[i] } )

	return retLinks

today = date.today().strftime("%d.%m.%Y").lstrip('0')
yesterday = (datetime.date.today() + datetime.timedelta(days=-1)).strftime("%d.%m.%Y").lstrip('0')
day_minus_2 = (datetime.date.today() + datetime.timedelta(days=-2)).strftime("%d.%m.%Y").lstrip('0')
day_minus_3 = (datetime.date.today() + datetime.timedelta(days=-3)).strftime("%d.%m.%Y").lstrip('0')
day_minus_4 = (datetime.date.today() + datetime.timedelta(days=-4)).strftime("%d.%m.%Y").lstrip('0')
day_minus_5 = (datetime.date.today() + datetime.timedelta(days=-5)).strftime("%d.%m.%Y").lstrip('0')
def relativeDay(day, emptyToday=False):
	if day==today:
		return lang(33006) if not emptyToday else '' #today
	if day==yesterday:
		return lang(30010) #yesterday
	if day==day_minus_2:
		return getWeekday(datetime.date.today().weekday()-2) + ' (' + day + ')'
	if day==day_minus_3:
		return getWeekday(datetime.date.today().weekday()-3) + ' (' + day + ')'
	if day==day_minus_4:
		return getWeekday(datetime.date.today().weekday()-4) + ' (' + day + ')'
	if day==day_minus_5:
		return getWeekday(datetime.date.today().weekday()-5) + ' (' + day + ')'
	
	return day

def getWeekday(weekday):
	if weekday<0: weekday+=7
	if weekday==0: return lang(11)
	if weekday==1: return lang(12)
	if weekday==2: return lang(13)
	if weekday==3: return lang(14)
	if weekday==4: return lang(15)
	if weekday==5: return lang(16)
	if weekday==6: return lang(17)

	
class RuutuAddon (xbmcUtil.ViewAddonAbstract):
	ADDON_ID = 'plugin.video.ruutu'
	
	def __init__(self):
		xbmcUtil.ViewAddonAbstract.__init__(self)
		self.initConst()
		self.addHandler(None, self.handleMain)
		self.addHandler('category', self.handleCategory)
		self.addHandler('serie', self.handleSeries)
		self.addHandler('programs', self.handlePrograms)
		self.favourites = {}
		self.initFavourites()
		
	def initConst(self):
		self.NEXT = '[COLOR blue]   ➔  %s  ➔[/COLOR]' % self.lang(33078)
		self.GROUP_FORMAT = u'   [COLOR blue]%s[/COLOR]'
		self.EXPIRES_HOURS = u'[COLOR red]%d' + self.lang(30002) + '[/COLOR] %s'
		self.EXPIRES_DAYS = u'[COLOR brown]%d' + self.lang(30003) + '[/COLOR] %s'
		self.FAVOURITE = '[COLOR yellow]★[/COLOR] %s'
		self.REMOVE = u'[COLOR red]✖[/COLOR] %s' % self.lang(1210)
	

	def handleMain(self, pg, args):
		self.addViewLink('›› ' + self.lang(30020),'programs',1 )
		self.addViewLink(self.lang(30028),'category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_1?page=0%2C','grouping':True, 'pg-size':10 } )
		self.addViewLink(self.lang(30030),'category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_6?page=0%2C0%2C0%2C0%2C', 'pg-size':10 } ) #yhden viikon ajalta
		self.addViewLink(self.lang(30021),'category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos_by_series/episodes_1/164876?page=0%2C','grouping':True, 'pg-size':10 } )
		self.addViewLink(self.lang(30027),'category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_2?page=0%2C','grouping':True, 'pg-size':10 } )
		self.addViewLink(self.lang(30023),'category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_3?page=0%2C','grouping':True, 'pg-size':5 } )
		self.addViewLink(self.lang(30029),'category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/theme_liftups/block_8/Ruoka?page=0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C','grouping':'True' } )
		for title, link in self.favourites.items():
			t = title			
			cm = [ (self.createContextMenuAction(self.REMOVE, 'removeFav', {'name':t} ) ) ]
			self.addViewLink(self.FAVOURITE % t,'serie',1, {'link':link, 'pg-size':10}, cm )
	
	def initFavourites(self):
		fav = self.addon.getSetting("fav")
		if fav:
			try:
				favList = eval(fav)
				for title, link in favList.items():
					self.favourites[title] = link
			except:
				pass
	
	
	def isFavourite(self, title):
		return title in self.favourites
			
	def getPageQuery(self, pg):
		return str(pg-1) if pg>0	else ''
			
	def handleCategory(self, pg, args):
		link = args['link'] + self.getPageQuery(pg) if 'link' in args else ''
		if link != '':
			items = scrapPager(link)
			self.listItems(items, pg, args, 'category', True)

	def handleSeries(self, pg, args):
		link = args['link'] if 'link' in args else ''
		if link != '':
			self.listItems(scrapSeries(link, pg), pg, args, 'serie', False)


	def listItems(self, items, pg, args, handler, markFav=False):
		grouping = args['grouping'] if 'grouping' in args else False
		pgSize = int(args['pg-size']) if 'pg-size' in args else -1
		groupName = ''
		if items != None:		
			xbmcplugin.setContent(int(sys.argv[1]), 'episodes')		
			for item in items:
				if grouping and groupName != relativeDay(item['published'], True):
					groupName = relativeDay(item['published'], len(groupName)==0)
					self.addVideoLink(self.GROUP_FORMAT % groupName, '', '')

				title = item['title']
				if markFav and self.isFavourite(title):
					title = self.FAVOURITE % title
				if len(item['details'])>0:
					title += ': ' + item['details']
					if len(title)>50:
						title = title[:50] + u'…'
				if len(item['episodeNum'])>0:
					title += ' [' + item['episodeNum'].replace('Kausi ', '').replace(' Jakso ', '#') + ']'
				
				av = item['available']
				expiresInHours = int((int(av) - time.time())/(60*60))
				
				availableText = item['available-text']
				if expiresInHours<24 and expiresInHours>=0:
					title = self.EXPIRES_HOURS % (expiresInHours, title)
					availableText = '[COLOR red]%s[/COLOR]' % availableText
				elif expiresInHours<=120 and expiresInHours>=0:
					title = self.EXPIRES_DAYS % (expiresInHours/24, title)
					availableText = '[COLOR red]%s[/COLOR]' % availableText
				
				plot = '[B]%s[/B]\n\r%s\n\r%s\n\r%s' % (item['details'], item['episodeNum'], item['desc'], availableText)

				episodeNum = None
				seasonNum = None
				if 'episodeNum' in item:
					episodeMatch = re.compile("Jakso ([0-9]*)", re.DOTALL).findall(item['episodeNum'])
					episodeNum = int(episodeMatch[0]) if len(episodeMatch)>0 else None
					seasonMatch = re.compile("Kausi ([0-9]*)", re.DOTALL).findall(item['episodeNum'])
					seasonNum = int(seasonMatch[0]) if len(seasonMatch)>0 else None
				contextMenu = [ (self.createContextMenuAction('Download', 'download', {'videoLink':item['link'], 'title': item['title']}) ) ]
				self.addVideoLink(title , item['link'], item['image'], infoLabels={'plot':plot,'season':seasonNum, 'episode': episodeNum,'aired': item['published'] , 'duration':item['duration']}, contextMenu=contextMenu)
			if len(items)>0 and len(items)>=pgSize:
				self.addViewLink(self.NEXT,handler, pg+1, args )
			
	def handleSeriesJSON(self, pg, args):
		if 'link' in args:
			items = scrapJSON(args['link'])
			for item in items['video_episode']:
				link = 'http://arkisto.ruutu.fi/video?vt=video_episode&vid=' + item['video_filename'][:-4]
				image = 'http://arkisto.ruutu.fi/' + item['video_preview_url']
				self.addVideoLink(item['title'] , link, image, '')

	def handlePrograms(self, pg, args):
		serieList = scrapPrograms()
		for serie in serieList:
			try:				
				title = serie['name'].encode('utf-8')
				menu = [ (self.createContextMenuAction(self.FAVOURITE % self.lang(14076), 'addFav', {'name':serie['name'], 'link':serie['link']} ) ) ]
				if self.isFavourite(title):
					title = self.FAVOURITE % title
					menu = [ (self.createContextMenuAction(self.REMOVE, 'removeFav', {'name':serie['name']} ) ) ]
				
				self.addViewLink(title , 'serie', 1, {'link':serie['link'], 'pg-size':10}, menu)
			except:
				pass
				
	def handleAction(self, action, params):
		if action=='addFav':
			self.favourites[params['name'].encode("utf-8")] = params['link']
			favStr = repr(self.favourites)
			self.addon.setSetting('fav', favStr)
			xbmcUtil.notification(self.lang(30006), params['name'].encode("utf-8") )
		elif action=='removeFav':
			self.favourites.pop(params['name'])
			favStr = repr(self.favourites)
			self.addon.setSetting('fav', favStr)
			xbmcUtil.notification(self.lang(30007), params['name'].encode("utf-8") )
		elif action=='download':
			downloadVideo(params['videoLink'], params['title'])		
		else:
			super(ViewAddonAbstract, self).handleAction(self, action, params)
		
	def handleVideo(self, link):
		videoLink = scrapVideoLink(link)
		return videoLink
#-----------------------------------

ruutu = RuutuAddon()
lang = ruutu.lang
ruutu.handle()
