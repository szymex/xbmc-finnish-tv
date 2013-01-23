# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import os,subprocess, json
import CommonFunctions
import xbmcutil as xbmcUtil
import time
import datetime
from datetime import date
import sys

common = CommonFunctions
common.plugin = "plugin.video.riemurasia"

#sets default encoding to utf-8
reload(sys) 
sys.setdefaultencoding('utf8')


class RiemurasiaScraper:
	ADDR = 'http://www.riemurasia.net/jylppy/' 
	def scrapVideos(self,params=''):
		url = self.ADDR + 'mediaselaus.php?c=2' + params
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

		response = urllib2.urlopen(req)
		content=response.read()	
		response.close()		
		content = content.decode('iso-8859-1').encode('utf8')

		ret = common.parseDOM(content, "div", {'class': 'alaosa_selaus'})
		retList = common.parseDOM(ret, "div", {'class': 'kaatiskuva'})
	
		retItems = []	
		for item in retList:
			link = self.ADDR + common.parseDOM(item, "a", {'href': '*'}, 'href')[0]
			title = common.parseDOM(item, "img", ret='alt')[0].replace('&ouml;', 'ö').replace('&auml;', 'ä')
			img = common.parseDOM(item, "img", ret='src')[0]
			retItems.append( {'link':link, 'img':img, 'plot': '', 'title': title } )		
	
		return retItems


	def scrapVideoLink(self,url):
	
		xbmc.log( url )
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		content = response.read()

		#---- file video ----
		matchTitle=re.compile('file: "(.*?)"').findall(content)
		if (len(matchTitle) > 1): #HD
			jmVidLink = urllib.unquote(matchTitle[1])
			return jmVidLink
		if (len(matchTitle) > 0):
			jmVidLink = urllib.unquote(matchTitle[0])
			return jmVidLink

		#could not scrap video	
		return None


	
class RiemurasiaAddon (xbmcUtil.ViewAddonAbstract):
	ADDON_ID = 'plugin.video.riemurasia'
	SCRAPPER = RiemurasiaScraper()
	def __init__(self):
		xbmcUtil.ViewAddonAbstract.__init__(self)
		self.addHandler(None, self.handleMain)
		self.addHandler('newest', self.handleNewest)
		self.addHandler('popular', self.handlePopular)
		self.addHandler('most-watched', self.handleMostWatched)
		
	def handleMain(self, pg, args):
		self.addViewLink('[COLOR blue]SUOSITUIMMAT[/COLOR]' ,'popular', 1 )
		self.addViewLink('[COLOR blue]KATSOTUIMMAT[/COLOR]' ,'most-watched', 1 )
		
		for it in self.SCRAPPER.scrapVideos('&limit=1'):
			self.addVideoLink(it['title'], it['link'], it['img'], infoLabels={'plot':it['plot']})
		self.addViewLink('[COLOR blue]   ➔  Seurava  ➔[/COLOR]' ,'newest', 2 )
	
	def handleNewest(self, pg, args):
		for it in self.SCRAPPER.scrapVideos('&limit='+ str(pg)):
			self.addVideoLink(it['title'], it['link'], it['img'], infoLabels={'plot':it['plot']})
		self.addViewLink('[COLOR blue]   ➔  Seurava  ➔[/COLOR]' ,'newest', pg+1 )
	
	def handlePopular(self, pg, args):
		for it in self.SCRAPPER.scrapVideos('&k=1&limit='+ str(pg)):
			self.addVideoLink(it['title'], it['link'], it['img'], infoLabels={'plot':it['plot']})
		self.addViewLink('[COLOR blue]   ➔  Seurava  ➔[/COLOR]' ,'popular', pg+1 )
	
	def handleMostWatched(self, pg, args):
		for it in self.SCRAPPER.scrapVideos('&s=1&limit='+ str(pg)):
			self.addVideoLink(it['title'], it['link'], it['img'], infoLabels={'plot':it['plot']})
		self.addViewLink('[COLOR blue]   ➔  Seurava  ➔[/COLOR]' ,'most-watched', pg+1 )
		
	def handleVideo(self, link):
		vid = self.SCRAPPER.scrapVideoLink(link)
		return vid
		

#-----------------------------------

riemurasia = RiemurasiaAddon()
riemurasia.handle()
