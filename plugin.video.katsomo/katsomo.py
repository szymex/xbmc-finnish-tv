# -*- coding: utf-8 -*-
import xbmcplugin,xbmcgui
import xbmcutil as xbmcUtil
import sys
from katsomoscrapper import KatsomoScrapper
from datetime import datetime, date


#sets default encoding to utf-8
reload(sys) 
sys.setdefaultencoding('utf8')
	
class KatsomoAddon (xbmcUtil.ViewAddonAbstract):
	ADDON_ID = 'plugin.video.katsomo'
	GROUP = u'   [COLOR blue]%s[/COLOR]'
	
	def __init__(self):
		xbmcUtil.ViewAddonAbstract.__init__(self)
		self.addHandler(None, self.handleMain)
		self.addHandler('serie', self.handleSerie)
		self.addHandler('programs', self.handlePrograms)
		self.scrapper = KatsomoScrapper()

	def handleMain(self, pg, args):
		self.addViewLink('›› Ohjelmat','programs',1 )
		self.addViewLink('Uutiset','serie',1, {'link':'http://m.katsomo.fi/katsomo/?treeId=33001', 'useGroups': True} )
		self.addViewLink('Urheilu','serie',1, {'link':'http://m.katsomo.fi/katsomo/?treeId=33002', 'useGroups': True} )
		self.addViewLink('Lapset','serie',1, {'link':'http://m.katsomo.fi/katsomo/?treeId=33003', 'useGroups': True} )
		
	def handlePrograms(self, pg, args):
		programs = self.scrapper.scrapPrograms()
		for p in programs:
			self.addViewLink(p['title'] ,'serie',1,{'link': p['link']})

	def handleSerie(self, pg, args):
		link = args['link']
		series = self.scrapper.scrapSerie(link)
		xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
		useGroups = args['useGroups'] if 'useGroups' in args else False;
		groupName = formatDate(datetime.now())
		
		for s in series:
			if useGroups and s['publ-ts'] != None and groupName != formatDate(s['publ-ts']):
				groupName = formatDate(s['publ-ts'])
				self.addVideoLink(self.GROUP % groupName, '', '')

			self.addVideoLink(s['title'] , s['link'], s['img'], infoLabels={'aired': s['published'] } )
		
	def handleVideo(self, link):
		return self.scrapper.scrapVideoLink(link)
#-----------------------------------

def formatDate(dt):
	delta = date.today() - dt.date()
	if delta.days==0: return 'Today'
	if delta.days==1: return 'Yesterday'
	if delta.days>1 and delta.days<5: return dt.strftime('%A %d.%m.%Y')
	return dt.strftime('%d.%m.%Y')


katsomo = KatsomoAddon()
katsomo.handle()