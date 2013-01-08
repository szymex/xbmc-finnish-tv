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
	REMOVE = u'[COLOR red]✖[/COLOR] %s' % 'Remove'
	FAVOURITE = '[COLOR yellow]★[/COLOR] %s'

	def __init__(self):
		xbmcUtil.ViewAddonAbstract.__init__(self)
		self.addHandler(None, self.handleMain)
		self.addHandler('serie', self.handleSerie)
		self.addHandler('programs', self.handlePrograms)
		self.scrapper = KatsomoScrapper()
		self.favourites = {}
		self.initFavourites()

	def handleMain(self, pg, args):
		self.addViewLink('›› ' + lang(30020),'programs',1 )
		self.addViewLink(lang(30028),'serie',1, {'link':'http://m.katsomo.fi/katsomo', 'useGroups': True} )
		self.addViewLink(lang(30021),'serie',1, {'link':'http://m.katsomo.fi/katsomo/?treeId=33001', 'useGroups': True} )
		self.addViewLink(lang(30027),'serie',1, {'link':'http://m.katsomo.fi/katsomo/?treeId=33002', 'useGroups': True} )
		self.addViewLink(lang(30023),'serie',1, {'link':'http://m.katsomo.fi/katsomo/?treeId=33003', 'useGroups': True} )
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

	def handlePrograms(self, pg, args):
		programs = self.scrapper.scrapPrograms()
		for p in programs:
			title = p['title']
			menu = [ (self.createContextMenuAction(self.FAVOURITE % 'Mark as favourite', 'addFav', {'name':p['title'], 'link':p['link']} ) ) ]
			if p['title'] in self.favourites:
				title = self.FAVOURITE % title
				menu = [ (self.createContextMenuAction(self.REMOVE, 'removeFav', {'name':p['title']} ) ) ]
			self.addViewLink(title ,'serie',1,{'link': p['link']}, menu)

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

	def handleAction(self, action, params):
		if action=='addFav':
			self.favourites[params['name'].encode("utf-8")] = params['link']
			favStr = repr(self.favourites)
			self.addon.setSetting('fav', favStr)
			xbmcUtil.notification('Added', params['name'].encode("utf-8") )
		elif action=='removeFav':
			self.favourites.pop(params['name'])
			favStr = repr(self.favourites)
			self.addon.setSetting('fav', favStr)
			xbmcUtil.notification('Removed', params['name'].encode("utf-8") )
		else:
			super(ViewAddonAbstract, self).handleAction(self, action, params)

#-----------------------------------

def formatDate(dt):
	delta = date.today() - dt.date()
	if delta.days==0: return lang(30004)
	if delta.days==1: return lang(30010)
	if delta.days>1 and delta.days<5: return dt.strftime('%A %d.%m.%Y')
	return dt.strftime('%d.%m.%Y')


katsomo = KatsomoAddon()
lang = katsomo.lang
katsomo.handle()
