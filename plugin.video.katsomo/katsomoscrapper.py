import urllib,urllib2,re
import CommonFunctions
import xbmc
from datetime import datetime
import time

common = CommonFunctions
common.plugin = "plugin.video.katsomo"

USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.1.1; Nexus 7 Build/JRO03D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Safari/535.19'

class KatsomoScrapper:

	def scrapVideoLink(self, url):
		xbmc.log( url )
		req = urllib2.Request(url)
		req.add_header('User-Agent', USER_AGENT)
		req.add_header('Cookie', 'hq=1')

		response = urllib2.urlopen(req)
		ret = common.parseDOM(response.read(), "source", {'type': 'video/mp4'}, ret = "src")
		if len(ret)>0:
			return ret[0]
		else:
			return None
			
	def scrapSerie(self, url):
		xbmc.log( url )
		req = urllib2.Request(url)
		req.add_header('User-Agent', USER_AGENT)
		response = urllib2.urlopen(req)
		ret = common.parseDOM(response.read(), "div", {'class': 'program'})
		
		l = []
		for r in ret:
			link = 'http://m.katsomo.fi' + common.parseDOM(r, "a", ret = "href")[0]
			title = common.parseDOM(r, "p", {'class': 'program-name'})[0]
			if 'class="star"' in title: continue
				
			title += ' ' + common.parseDOM(r, "p", {'class': 'program-abstract'})[0]
			img = 'http://m.katsomo.fi' + common.parseDOM(r, "img", ret = "src")[0]
			
			timestamp = common.parseDOM(r, "p", {'class': 'timestamp'})[0]
			ts = None
			if 'TULOSSA' in timestamp:
				continue;

			try:
				ts = datetime.strptime(timestamp.replace('- ', ''), '%d.%m.%Y %H.%M')
			except TypeError:
				ts = datetime(*(time.strptime(timestamp.replace('- ', ''), '%d.%m.%Y %H.%M')[0:6]))				
			
			l.append( {'link':link, 'title':title, 'img':img, 'published': timestamp, 'publ-ts': ts} )
			
		return l

	def scrapPrograms(self):
		req = urllib2.Request('http://m.katsomo.fi/katsomo/programs')
		req.add_header('User-Agent', USER_AGENT)
		response = urllib2.urlopen(req)
		ret = common.parseDOM(response.read(), "ul", {'class': 'all-programs-list'})
		retIDs = common.parseDOM(ret, "li", ret="data-id")
		retNames = common.parseDOM(ret, "li")
		#xbmc.log( str(retIDs) )
		l=[]
		for i in range(0, len(retIDs)):
			name = retNames[i]
			id = retIDs[i]
			if not 'star' in name:
				l.append({'title':name, 'link':'http://m.katsomo.fi/katsomo/?treeId=' + id, 'treeId': id})
		
		return l
