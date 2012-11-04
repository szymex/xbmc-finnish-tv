# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import os,subprocess, json
import CommonFunctions
xbmcUtil = __import__('xbmcutil_v1_0')
import inspect

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

def scrapSeries(url):
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
			url = 'http://www.ruutu.fi/views_cacheable_pager/videos_by_series/episodes_1/' + serieId + '?page=0%2C0'
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
			image = it.find('img').get('src')
			link = it.select('h2 a')[0]['href']
			title = it.select('h2 a')[0].string + " -"
			for sec in it.select('footer .details-inline div'):
				for str in sec.stripped_strings:
					title += " " + str
			selDuration = it.select('.field-name-field-duration')
			if len(selDuration)>0:
				duration = selDuration[0].string.strip()
			else:
				duration = ''

			retList.append( {'title':title, 'link':"http://www.ruutu.fi" + link, 'image':image, 'duration': duration});
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

class RuutuAddon (xbmcUtil.ViewAddonAbstract):
	def __init__(self):
		self.setAddonId('plugin.video.ruutu')
		
		self.addHandler(None, self.handleMain)
		self.addHandler('category', self.handleCategory)
		self.addHandler('serie', self.handleSeries)
		self.addHandler('programs', self.handlePrograms)

	def handleMain(self, pg, args):
		self.addViewLink('›› Ohjelmat','programs',1 )
		self.addViewLink('Uutiset','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos_by_series/episodes_1/164876?page=0%2C0' } )
		self.addViewLink('Katsotuimmat','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_9?page=0%2C0%2C0' } )
		self.addViewLink('Uusimmat','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_1?page=0%2C0%2C0' } )
		self.addViewLink('Urheilu: katsotuimmat','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_5?page=0%2C0%2C0' } )
		self.addViewLink('Urheilu: uusimmat','category',1, {'link':'http://www.ruutu.fi/views_cacheable_pager/videos/block_2?page=0%2C0' } )
		
		try:
			strCat = open(os.path.join(self.BASE_PATH,'favourites.txt')).read().split('\n')
			for cat in strCat:
				if not cat.startswith('#'):
					splCat = cat.split("|")
					if (len(splCat)==2):
						self.addViewLink('[COLOR yellow]★[/COLOR] ' + splCat[0].strip(),'serie',1, {'link':splCat[1].strip()}, [('[COLOR red]✖[/COLOR] Remove', 'RunScript(special://home/addons/plugin.video.ruutu/favourites.py,-remove,'+splCat[0].strip()+ ')')] )
		except:
			xbmc.log("Could not read favourites from file: " + self.BASE_PATH + "favourites.txt", level=xbmc.LOGWARNING )

	def handleCategory(self, pg, args):
		if 'link' in args:
			items = scrapPager(args['link'])
			for item in items:				
				self.addVideoLink(item['title'] , item['link'], item['image'])
	
	def handleSeries(self, pg, args):
		if 'link' in args:
			items = scrapSeries(args['link'])
			if items != None:			
				for item in items:
					self.addVideoLink(item['title'] , item['link'], item['image'], infoLabels={'duration':item['duration']})
	
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
				self.addViewLink(serie['name'] , 'serie', 1, {'link':serie['link']}, [('[COLOR yellow]★[/COLOR] Mark as favourite', 'RunScript(special://home/addons/plugin.video.ruutu/favourites.py,-add,'+serie['name']+', ' +serie['link']+ ')')])
			except:
				pass


		
	def handleVideo(self, link):
		videoLink = scrapVideoLink(link)
		#print(videoId)
		#videoLink = 'rtmp://streamh1.nelonen.fi/hot/mp4:'+videoId+'.mp4'

		return videoLink
#-----------------------------------

ruutu = RuutuAddon()
ruutu.handle()