import urllib,urllib2,re
import cookielib
import CommonFunctions
import xbmc,xbmcaddon
from datetime import datetime
import time

#cookie handling 
addon = xbmcaddon.Addon('plugin.video.katsomo')
cookie_file = xbmc.translatePath(addon.getAddonInfo('profile')) + "cookies.txt"

cj = cookielib.LWPCookieJar(cookie_file)
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

logmsg = "plugin.video.katsomo - "

common = CommonFunctions
common.plugin = "plugin.video.katsomo"

USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3'

class KatsomoScrapper:

	def checkLogin( self ):
		global cj
		try:
			cj.revert(ignore_discard = True)
		except IOError:
			pass
		#xbmc.log(logmsg + "checking login status to katsomo")
		login_url='http://m.katsomo.fi/katsomo/login'
		req = urllib2.Request(login_url)
		req.add_header('User-Agent', USER_AGENT)
		response = opener.open(req)
		ret = common.parseDOM(response.read(), "div", attrs = { "class": "login" })
		ret = common.parseDOM(ret, "a", ret = "href")
		#xbmc.log(ret[0])
		if "/katsomo/logout" in ret:
			xbmc.log(logmsg + "Login status active, no need to login" )
			return 1
		else:
			xbmc.log(logmsg + "Login status not active, need to login" )
			return 0

	def doLogin(self, username, password):
		xbmc.log(logmsg + "Login to katsomo" )
		login_url='http://m.katsomo.fi/katsomo/login'
		postvars = { 
			'u' : username,
			'p' : password
		}
		header_data = {
			'User-Agent' : USER_AGENT,
			'Referer' : 'http://m.katsomo.fi/katsomo/login'
		}
		if self.checkLogin():
			return 1
		req = urllib2.Request(login_url, urllib.urlencode(postvars), header_data )
		response = opener.open(req)
		ret = common.parseDOM(response.read(), "div", attrs = { "class": "login" })
		ret = common.parseDOM(ret, "a", ret = "href")
		#xbmc.log(ret[0])
		if "/katsomo/logout" in ret:
			xbmc.log(logmsg + "Login to katsomo succeed" )
			cj.save( ignore_discard=True )
			return 1
		else:
			xbmc.log(logmsg + "Login to katsomo failed" )
			cj.clear()
			return 0

	def scrapVideoLink(self, url):
		xbmc.log( url )
		req = urllib2.Request(url)
		req.add_header('User-Agent', USER_AGENT)
		req.add_header('Cookie', 'hq=1')

		response = opener.open(req)
		ret = common.parseDOM(response.read(), "source", {'type': 'video/mp4'}, ret = "src")
		if len(ret)>0:
			return ret[0]
		else:
			return None
			
	def scrapSerie(self, url):
		xbmc.log( url )
		req = urllib2.Request(url)
		req.add_header('User-Agent', USER_AGENT)
		response = opener.open(req)
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
		response = opener.open(req)
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
