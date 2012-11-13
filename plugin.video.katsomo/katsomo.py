# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import os,subprocess, json
import CommonFunctions
import xbmcutil as xbmcUtil
import inspect
import time
import datetime
from datetime import date
import sys

common = CommonFunctions
common.plugin = "plugin.video.katsomo"

#sets default encoding to utf-8
reload(sys) 
sys.setdefaultencoding('utf8')

USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.1.1; Nexus 7 Build/JRO03D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Safari/535.19'

def scrapVideoLink(url):
	
	xbmc.log( url )
	req = urllib2.Request(url)
	req.add_header('User-Agent', USER_AGENT)
	response = urllib2.urlopen(req)
	ret = common.parseDOM(response.read(), "source", {'type': 'video/mp4'}, ret = "src")
	if len(ret)>0:
		return ret[0]
	else:
		return None

def scrapSerie(url):
	xbmc.log( url )
	req = urllib2.Request(url)
	req.add_header('User-Agent', USER_AGENT)
	response = urllib2.urlopen(req)
	ret = common.parseDOM(response.read(), "div", {'class': 'program'})
	
	l = []
	for r in ret:
		link = 'http://m.katsomo.fi' + common.parseDOM(r, "a", ret = "href")[0]
		title = common.parseDOM(r, "p", {'class': 'program-name'})[0]
		title += ' ' + common.parseDOM(r, "p", {'class': 'program-abstract'})[0]
		img = 'http://m.katsomo.fi' + common.parseDOM(r, "img", ret = "src")[0]
		l.append( {'link':link, 'title':title, 'img':img} )
		
	return l

def scrapPrograms():
	req = urllib2.Request('http://m.katsomo.fi/katsomo/programs')
	req.add_header('User-Agent', USER_AGENT)
	response = urllib2.urlopen(req)
	ret = common.parseDOM(response.read(), "ul", {'class': 'all-programs-list'})
	retIDs = common.parseDOM(ret, "li", ret="data-id")
	retNames = common.parseDOM(ret, "li")
	xbmc.log( str(retIDs) )
	l=[]
	for i in range(0, len(retIDs)):
		name = retNames[i]
		id = retIDs[i]
		if not 'star' in name:
			l.append({'title':name, 'link':'http://m.katsomo.fi/katsomo/?treeId=' + id})
	
	return l
	
	
class KatsomoAddon (xbmcUtil.ViewAddonAbstract):
	ADDON_ID = 'plugin.video.katsomo'
	
	def __init__(self):
		xbmcUtil.ViewAddonAbstract.__init__(self)
		self.addHandler(None, self.handleMain)
		self.addHandler('serie', self.handleSerie)
		self.addHandler('programs', self.handlePrograms)

	def handleMain(self, pg, args):
		self.addViewLink('›› Ohjelmat','programs',1 )
		self.addViewLink('Uutiset','serie',1, {'link':'http://m.katsomo.fi/katsomo/?treeId=33001'} )
		self.addViewLink('Urheilu','serie',1, {'link':'http://m.katsomo.fi/katsomo/?treeId=33002'} )
		self.addViewLink('Lapset','serie',1, {'link':'http://m.katsomo.fi/katsomo/?treeId=33003'} )
		
	def handlePrograms(self, pg, args):
		programs = scrapPrograms()
		for p in programs:
			self.addViewLink(p['title'] ,'serie',1,{'link': p['link']})

	def handleSerie(self, pg, args):
		link = args['link']
		series = scrapSerie(link)
		for s in series:
			self.addVideoLink(s['title'] , s['link'], s['img'])
		
	def handleVideo(self, link):
		return scrapVideoLink(link)
#-----------------------------------

katsomo = KatsomoAddon()
katsomo.handle()