# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import os,subprocess, json
import CommonFunctions
xbmcUtil = __import__('xbmcutil_v1_0_1')
import inspect
import time
import datetime
from datetime import date

#cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"bs5")))
#if cmd_subfolder not in sys.path:
#	sys.path.insert(0, cmd_subfolder)

from bs4 import BeautifulSoup

common = CommonFunctions
common.plugin = "plugin.video.ruutu"

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
	
	print url
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	matchVideoId=re.compile("'providerURL', '(.*?)'").findall(response.read())
	response.close()
	videoUrl = urllib2.unquote( matchVideoId[0])
	
	req = urllib2.Request(videoUrl)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	videoLink = re.compile('<SourceFile>(.*?)</SourceFile>').findall(response.read())[0]
		
	return videoLink

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
			
			selAvailability = it.select('.availability-timestamp')
			available = selAvailability[0].string.strip() if len(selAvailability)>0 else '0'
			
			selDesc = it.select('.field-name-field-webdescription p')
			desc = selDesc[0].string.strip() if len(selDesc)>0 else '0'
			
			selAvailabilityText = it.select('.availability-text')
			availabilityText = selAvailabilityText[0].string.strip() if len(selAvailabilityText)>0 else ''
			desc += '\n\r' + availabilityText
			
			selDetails = it.select('.details .field-type-text')
			details = selDetails[0].string.strip() if len(selDetails)>0 and selDetails[0].string!=None else ''
			
			selStartTime = it.select('.field-name-field-starttime')
			for str in selStartTime[0].stripped_strings:
				published = str

			retList.append( {'title':title, 'episodeNum':episodeNum, 'link':"http://www.ruutu.fi" + link, 'image':image, 'duration': duration, 
							'published':published, 'available': available, 'desc':desc, 'details':details });
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
		return u'Täänän' if not emptyToday else ''
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

def getWeekday(weekday):
	if weekday<0: weekday+=7
	if weekday==0: return u'Maanantai'
	if weekday==1: return u'Tiistai'
	if weekday==2: return u'Keskiviikko'
	if weekday==3: return u'Torstai'
	if weekday==4: return u'Perjantai'
	if weekday==5: return u'Lauantai'
	if weekday==6: return u'Sunnuntai'

	
class RuutuAddon (xbmcUtil.ViewAddonAbstract):
	GROUP_FORMAT = u'   [COLOR blue]%s[/COLOR]'
	NEXT = '[COLOR blue]   ➔  NEXT  ➔[/COLOR]'
	EXPIRES_HOURS = u'[COLOR red]%dh[/COLOR] %s'
	EXPIRES_DAYS = u'[COLOR brown]%dpv[/COLOR] %s'
	FAVOURITE = u'[COLOR yellow]★[/COLOR] %s'
	REMOVE = u'[COLOR red]✖[/COLOR] %s'
	
	def __init__(self):
		self.setAddonId('plugin.video.ruutu')
		
		self.addHandler(None, self.handleMain)
		self.addHandler('category', self.handleCategory)
		self.addHandler('serie', self.handleSeries)
		self.addHandler('programs', self.handlePrograms)
		self.favourites = {}
		self.initFavourites()

	def handleMain(self, pg, args):
		self.addViewLink('›› Ohjelmat','programs',1 )
		self.addViewLink('Uusimmat','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_1?page=0%2C','grouping':True, 'pg-size':10 } )
		self.addViewLink('Katsotuimmat','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_6?page=0%2C0%2C0%2C0%2C', 'pg-size':10 } ) #yhden viikon ajalta
		self.addViewLink('Uutiset','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos_by_series/episodes_1/164876?page=0%2C','grouping':True, 'pg-size':10 } )
		self.addViewLink('Urheilu','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_2?page=0%2C','grouping':True, 'pg-size':10 } )
		self.addViewLink('Lapset','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_3?page=0%2C','grouping':True, 'pg-size':5 } )
		self.addViewLink('Ruoka','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/theme_liftups/block_8/Ruoka?page=0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C','grouping':'True' } )
		for title, link in self.favourites.items():
			self.addViewLink(self.FAVOURITE % title,'serie',1, {'link':link, 'pg-size':10}, [(self.REMOVE % 'Remove', 'RunScript(special://home/addons/plugin.video.ruutu/favourites.py,-remove,'+title+ ')')] )
	
	def initFavourites(self):
		try:
			strCat = open(os.path.join(self.BASE_PATH,'favourites.txt')).read().split('\n')
			for cat in strCat:
				if not cat.startswith('#'):
					splCat = cat.split("|")
					if (len(splCat)==2):
						self.favourites[splCat[0].strip()] = splCat[1].strip()
		except:
			xbmc.log("Could not read favourites from file: " + self.BASE_PATH + "favourites.txt", level=xbmc.LOGWARNING )
	
	
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
			for item in items:
				if grouping and groupName != relativeDay(item['published'], True):
					groupName = relativeDay(item['published'], True)
					self.addVideoLink(self.GROUP_FORMAT % groupName, '', None)

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
				
				if expiresInHours<24 and expiresInHours>=0:
					title = self.EXPIRES_HOURS % (expiresInHours, title)
				elif expiresInHours<=120 and expiresInHours>=0:
					title = self.EXPIRES_DAYS % (expiresInHours/24, title)
				plot = '[B]%s[/B]\n\r%s\n\r%s' % (item['details'], item['episodeNum'], item['desc'])

				self.addVideoLink(title , item['link'], item['image'], infoLabels={'plot':plot, 'duration':item['duration']})
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
				title = serie['name']
				menu = [(self.FAVOURITE % 'Mark as favourite', 'RunScript(special://home/addons/plugin.video.ruutu/favourites.py,-add,'+serie['name']+', ' +serie['link']+ ')')]
				if self.isFavourite(title):
					title = self.FAVOURITE % title
					menu = [(self.REMOVE % 'Remove', 'RunScript(special://home/addons/plugin.video.ruutu/favourites.py,-remove,'+serie['name']+ ')')]
				self.addViewLink(title , 'serie', 1, {'link':serie['link']}, menu)
			except:
				pass


		
	def handleVideo(self, link):
		videoLink = scrapVideoLink(link)
		return videoLink
#-----------------------------------

ruutu = RuutuAddon()
ruutu.handle()