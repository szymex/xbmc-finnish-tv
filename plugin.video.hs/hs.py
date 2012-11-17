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
common.plugin = "plugin.video.hs"

#sets default encoding to utf-8
reload(sys) 
sys.setdefaultencoding('utf8')


def scrapPopular(isNewest=False):
	url = 'http://www.hs.fi/videot/?ref=hs-navi-uutiset'
	result = common.fetchPage({"link": url})

	if isNewest:	
		ret = common.parseDOM(result['content'], "div", {'id': 'latest-videos-tab-box'})
	else:
		ret = common.parseDOM(result['content'], "div", {'class': 'most-popular-videos'})

	ret = common.parseDOM(ret, "ul", {'class': 'video-list'})
	retList = common.parseDOM(ret, "li")
	
	retItems = []	
	for item in retList:
		link = common.parseDOM(item, "a", {'href': '*'}, 'href')[0]
		img = common.parseDOM(item, "img", ret='src')[0]
		plot = common.parseDOM(item, "img", ret='title')[0]
		plot = plot.replace('&auml;', 'ä').replace('&ouml;', 'ö')
		title = common.parseDOM(item, "h4", {'class': 'title'})[0]
		title = common.parseDOM(title, "a")[0]
		retItems.append( {'link':link, 'img':img, 'plot': plot, 'title': title } )
	
	return retItems


def scrapVideoLink(url):
	
	xbmc.log( url )
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	content = response.read()
	matchVideoId=re.compile('providerURL.*?"(.*?)"').findall(content)
	response.close()
	videoUrl = urllib2.unquote( matchVideoId[0])
	if videoUrl[:1] == '/': 
		videoUrl = 'http://www.hs.fi' + videoUrl
	
	
	req = urllib2.Request(videoUrl)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	videoLink = re.compile('<SourceFile>(.*?)</SourceFile>', re.DOTALL).findall(response.read())[0]
	videoLink = videoLink.strip()
	xbmc.log( videoLink )	
		
	return videoLink


	
class HSAddon (xbmcUtil.ViewAddonAbstract):
	ADDON_ID = 'plugin.video.hs'
	
	def __init__(self):
		xbmcUtil.ViewAddonAbstract.__init__(self)
		self.addHandler(None, self.handleMain)
		self.addHandler('newest', self.handleNewest)
		
	def handleMain(self, pg, args):
		self.addViewLink('›› Uusimmat' ,'newest',1 )		
		for it in scrapPopular():
			self.addVideoLink(it['title'], it['link'], it['img'], infoLabels={'plot':it['plot']})
	
	def handleNewest(self, pg, args):
		for it in scrapPopular(True):
			self.addVideoLink(it['title'], it['link'], it['img'], infoLabels={'plot':it['plot']})
		
	def handleVideo(self, link):
		videoLink = scrapVideoLink(link)
		return videoLink
#-----------------------------------

hs = HSAddon()
hs.handle()
