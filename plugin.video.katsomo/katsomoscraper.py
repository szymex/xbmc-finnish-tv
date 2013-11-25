import urllib,urllib2,re
import os
import cookielib
import CommonFunctions
import xbmc,xbmcaddon
from datetime import datetime
import time

#cookie handling 
addon = xbmcaddon.Addon('plugin.video.katsomo')
cookie_file = xbmc.translatePath(addon.getAddonInfo('profile')) + "cookies.txt"

cj = cookielib.LWPCookieJar(cookie_file)
if os.path.isfile(cookie_file):
	try:
		cj.revert(ignore_discard = True)
	except IOError:
		pass
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

login_true = False

logmsg = "plugin.video.katsomo - "

common = CommonFunctions
common.plugin = "plugin.video.katsomo"

USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.1.1; Nexus 7 Build/JRO03D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Safari/535.19'

class KatsomoScraper:

	def checkLogin( self ):
		global cj,login_true
		if os.path.isfile(cookie_file):
			try:
				cj.revert(ignore_discard = True)
			except IOError:
				pass
		#xbmc.log(logmsg + "checking login status to katsomo")
		login_url='http://m.mtvkatsomo.fi/login'
		req = urllib2.Request(login_url)
		req.add_header('User-Agent', USER_AGENT)
		response = opener.open(req)
		ret = common.parseDOM(response.read(), "nav", attrs = { "id": "login-search" })
		ret = common.parseDOM(ret, "a", ret = "href")
		#xbmc.log(ret[0])
		if "/user" in ret:
			xbmc.log(logmsg + "Login status active, no need to login" )
			login_true = True
			return 1
		else:
			xbmc.log(logmsg + "Login status not active, need to login" )
			login_true = False
			return 0

	def doLogin(self, username, password):
		global cj,login_true
		login_true = False
		xbmc.log(logmsg + "Login to katsomo" )
		login_url='http://m.mtvkatsomo.fi/login'
		postvars = { 
			'u' : username,
			'p' : password
		}
		header_data = {
			'User-Agent' : USER_AGENT,
			'Referer' : 'http://m.mtvkatsomo.fi/login'
		}
		if self.checkLogin():
			return 1
		req = urllib2.Request(login_url, urllib.urlencode(postvars), header_data )
		response = opener.open(req)
		ret = common.parseDOM(response.read(), "nav", attrs = { "id": "login-search" })
		ret = common.parseDOM(ret, "a", ret = "href")
		#xbmc.log(ret[0])
		if "/user" in ret:
			xbmc.log(logmsg + "Login to katsomo succeed" )
			cj.save( ignore_discard=True )
			login_true = True
			return 1
		else:
			xbmc.log(logmsg + "Login to katsomo failed" )
			cj.clear()
			login_true = False
			return 0

	def noLogin(self):
		global login_true
		login_true = False
		return 0

	def scrapVideoLink(self, url):
		#xbmc.log( logmsg + url )
		req = urllib2.Request(url)
		req.add_header('User-Agent', USER_AGENT)
		ck = cookielib.Cookie(version=0, name='hq', value='1', port=None, port_specified=False, domain='m.mtvkatsomo.fi', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
		cj.set_cookie(ck)

		response = opener.open(req)
		ret = common.parseDOM(response.read(), "source", {'type': 'video/mp4'}, ret = "src")
		if len(ret)>0:
			return ret[0]
		else:
			return None
			
	def scrapSerie(self, url):
		global login_true
		xbmc.log( logmsg + url )
		req = urllib2.Request(url)
		req.add_header('User-Agent', USER_AGENT)
		response = opener.open(req)
		
		programs = common.parseDOM(response.read(), "div", {'class': 'programs'})[0]
		ret = common.parseDOM(programs, "div", {'class': 'program program-toggle'})
		l = []
		for r in ret:
			link = 'http://m.mtvkatsomo.fi' + common.parseDOM(r, "a", ret = "href")[0]
			title = common.parseDOM(r, "p", {'class': 'program-name'})[0]
			if 'class="star"' in title and not login_true: continue
			elif 'class="star"' in title and login_true and self.scrapVideoLink(link) == None: continue	
			
			img = 'http://m.mtvkatsomo.fi' + common.parseDOM(r, "img", ret = "src")[0]
			
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

	def scrapLive(self, url):
		global login_true
		xbmc.log( logmsg + url )
		req = urllib2.Request(url)
		req.add_header('User-Agent', USER_AGENT)
		response = opener.open(req)
		
		channels = common.parseDOM(response.read(), "div", {'class': 'channel'})
		l = []
		for r in channels:
			link = 'http://m.mtvkatsomo.fi' + common.parseDOM(r, "a", ret = "href")[0]
			title = common.parseDOM(r, "h1")[0]
			
			title += ' - ' + common.parseDOM(r, "h2")[0]
			imgClass = common.parseDOM(r, "div", ret = "class")[0].split(' ')[1]
			img = ''
			if imgClass == 'channel-logo-1':
				title = '[MTV3] ' + title
				img = 'http://m.mtvkatsomo.fi/images/channel-logos/channel-logo-mtv3@2x.png'
			elif imgClass == 'channel-logo-3':
				title = '[SUB] ' + title
				img = 'http://m.mtvkatsomo.fi/images/channel-logos/channel-logo-sub@2x.png'
			elif imgClass == 'channel-logo-6':
				title = '[AVA] ' + title
				img = 'http://m.mtvkatsomo.fi/images/channel-logos/channel-logo-ava@2x.png'
			
			
			l.append( {'link':link, 'title':common.replaceHTMLCodes(title), 'img':img} )
			
		return l		
		
	def scrapPrograms(self):
		global login_true
		req = urllib2.Request('http://m.mtvkatsomo.fi/programs')
		req.add_header('User-Agent', USER_AGENT)
		response = opener.open(req)
		ret = common.parseDOM(response.read(), "div", {'id': 'programs-by-name'})
		ret = common.parseDOM(ret, "ul", {'class': 'all-programs-list'})
		retIDs = common.parseDOM(ret, "a", ret="href")
		retNames = common.parseDOM(ret, "li")
		#xbmc.log( str(retIDs) )
		l=[]
		for i in range(0, len(retIDs)):
			name = retNames[i]
			id = retIDs[i]
			if not 'star' in name:
				l.append({'title':common.stripTags(name), 'link':'http://m.mtvkatsomo.fi' + id, 'treeId': id})
			else:
				l.append({'title':common.stripTags(name) + " *", 'link':'http://m.mtvkatsomo.fi' + id, 'treeId': id})
		return l
