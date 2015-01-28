# -*- coding: utf-8 -*-
import urllib2
import re
import os
import json
import time
from datetime import date, datetime
import sys
import string

import xbmcplugin
import CommonFunctions
import xbmcutil as xbmcUtil
from bs4 import BeautifulSoup

xbmc.log(">>> Running in Python {0}".format(sys.version))

dbg = True

common = CommonFunctions
common.plugin = "plugin.video.ruutu"

USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

# sets default encoding to utf-8
reload(sys)
sys.setdefaultencoding('utf8')


def scrapRSS(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    response = urllib2.urlopen(req)
    content = response.read()
    response.close()
    match = re.compile("<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?" +
                       "<description>.*?src='(.*?)'.*?br/&gt;(.*?)</description>" +
                       ".*?<pubDate>(.*?)</pubDate>.*?</item>",
                       re.DOTALL).findall(content)
    # title, link, img, description, date
    return match


def scrapVideoId(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    response = urllib2.urlopen(req)
    matchVideoId = re.compile("vid=(.*)").findall(response.geturl())

    response.close()
    return matchVideoId[0]


def scrapVideoLink(url):
    xbmc.log(url)  # NOQA
    req = urllib2.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    response = urllib2.urlopen(req)
    content = response.read()
    response.close()

    matchVideoId = re.compile('ruutuplayer\(.*"(http.*?)"').findall(content)
    if len(matchVideoId) == 0:
        matchVideoId = re.compile("providerURL', '(http.*?)'").findall(content)
    if len(matchVideoId) == 0:
        matchVideoId = re.compile("<!-- (http.*?) -->").findall(content)

    if len(matchVideoId) == 0:
        return None

    videoUrl = urllib2.unquote(matchVideoId[0])

    req = urllib2.Request(videoUrl)
    req.add_header('User-Agent', USER_AGENT)
    response = urllib2.urlopen(req)
    regexp = "(http://)(.*)(/playlist.m3u8)"
    regexp = re.compile(regexp, re.IGNORECASE)
    videoLink = regexp.search(response.read())

    return videoLink.group(0)


def downloadVideo(url, title):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    videoUrl = scrapVideoLink(url)

    downloadPath = ruutu.addon.getSetting('download-path')
    if downloadPath is None or downloadPath == '':
        return
    downloadPath += url.split('/')[-2]
    if not os.path.exists(downloadPath):
        os.makedirs(downloadPath)

    filename = "%s %s" % (''.join(
        c for c in title if c in valid_chars), videoUrl.split(':')[-1])

    params = {"url": videoUrl, "download_path": downloadPath}
    xbmc.log(url + " " + filename + "   " + str(params))  # NOQA
    dw = downloader.SimpleDownloader()  # NOQA
    dw.download(filename, params)


def scrapSeries(url, pg=1):
    try:
        # find serie id
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        content = response.read()
        response.close()

        res = re.compile('episodes_1","args":\["(.*?)"\]').findall(content)
        if len(res) > 0:
            serieId = res[0]
            url = "".join(["http://www.ruutu.fi/views_cacheable_pager/",
                           'videos_by_series/episodes_1/',
                           serieId, '?page=0%2C', str(pg - 1)])
            return scrapPager(url)
        else:
            soup = BeautifulSoup(content, "html5lib")
            section = soup.find(id='quicktabs-container-ruutu_series_episodes_by_season')
            items = section.find_all('div', class_='views-row grid-3')
            content = ''
            for it in items:
                content += str(it)
            return scrapPagerContent(content)
        # xbmcUtil.notification('Error', 'Could not find series')
        # return None
    except Exception as e:
        xbmcUtil.notification('Error', str(e))
        return None


def scrapPager(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    try:
        response = urllib2.urlopen(req)
        content = response.read()
        response.close()
        return scrapPagerContent(content)
    except urllib2.HTTPError:
        return []


def trimFromExtraSpaces(text):
    try:
        retVal = " ".join(text.split())
    except:
        retVal = ""
    return retVal


def scrapPagerContent(content):
    xbmc.log(">>> titleLink: {0}".format(content))
    retList = []
    soup = BeautifulSoup(content, "html5lib")
    items = soup.findAll('article')
    for it in items:
        image = it.find('img').get('src') if it.find('img') is not None else ''
        link = it.select('h2 a')[0]['href']
        title = trimFromExtraSpaces(it.select('h2 a')[0].string)
        if len(title) == 0:
            title = link
        episodeNum = ''
        seasonNum = ''

        htmlSeason = it.select('.field-name-field-season')
        if len(htmlSeason) > 0:
            season = repr(htmlSeason[0])
            season = re.compile(
                'span>.+?([0-9]+[0-9]*?).*?</', re.DOTALL).findall(season)
            if len(season) > 0:
                seasonNum = season[0]

        htmlEpisode = it.select('.field-name-field-episode')
        if len(htmlEpisode) > 0:
            episode = repr(htmlEpisode[0])
            episode = re.compile(
                'span>.+?([0-9]+[0-9]*?).*?</', re.DOTALL).findall(episode)
            if len(episode) > 0:
                episodeNum = episode[0]

        selDuration = it.select('.field-name-field-duration')
        duration = selDuration[0].string.strip() if len(
            selDuration) > 0 else ''
        duration = duration.replace(' min', '')

        selAvailability = it.select('.availability-timestamp')
        if len(selAvailability) > 0 and selAvailability[0].string is not None:
            available = selAvailability[0].string.strip()
        else:
            available = '0'

        selDesc = it.select('.field-name-field-webdescription p')
        desc = selDesc[0].string.strip() if len(
            selDesc) > 0 and selDesc[0].string is not None else '0'

        selAvailabilityText = it.select('.availability-text')
        if len(selAvailabilityText) > 0 and selAvailabilityText[0].string is not None:
            availabilityText = selAvailabilityText[0].string.strip()
        else:
            availabilityText = ''
        # desc += '\n\r' + availabilityText

        selDetails = it.select('.details .field-type-text')
        details = selDetails[0].string.strip() if len(
            selDetails) > 0 and selDetails[0].string is not None else ''

        selStartTime = it.select('.field-name-field-starttime')
        publishedTs = None
        if len(selStartTime) > 0:
            for strippedString in selStartTime[0].stripped_strings:
                published = strippedString
                try:
                    publishedTs = datetime.strptime(published, '%d.%m.%Y')
                except TypeError:
                    publishedTs = datetime(*(time.strptime(
                        published, '%d.%m.%Y')[0:6]))
        # search for duplicate
        isDuplicate = False
        for entry in retList:
            if entry['link'] == "http://www.ruutu.fi" + link:
                isDuplicate = True
                break

        if not isDuplicate:
            retList.append(
                {'title': title,
                    'seasonNum': seasonNum,
                    'episodeNum': episodeNum,
                    'link': "http://www.ruutu.fi" + link,
                    'image': image,
                    'duration': duration,
                    'published-ts': publishedTs,
                    'available-text': availabilityText,
                    'available': available,
                    'desc': desc,
                    'details': details})

    return retList


def scrapJSON(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    try:
        response = urllib2.urlopen(req)
        content = response.read()
        response.close()
        jsonObj = json.loads(content)
        return jsonObj
    except urllib2.HTTPError:
        return []


def scrapPrograms():
    url = 'http://www.ruutu.fi/ajax/series-navi'
    result = common.fetchPage({"link": url})
    content = result['content']
    match = re.compile("<li>(.*?)</li>", re.DOTALL).findall(content)

    retLinks = []
    for m in match:
        link = common.parseDOM(m, "a", {'href': '*'}, 'href')
        name = common.parseDOM(m, "a", {'href': '*'})
        if len(link) > 0 and "ruutuplus" not in m:
            retLinks.append({'link': "http://www.ruutu.fi" + str(
                link[0]), 'name': name[0]})

    return retLinks


def formatDate(dt):
    delta = date.today() - dt.date()
    if delta.days == 0:
        return lang(30004)
    if delta.days == 1:
        return lang(30010)
    if 1 < delta.days < 5:
        return dt.strftime('%A %d.%m.%Y')
    return dt.strftime('%d.%m.%Y')


class RuutuAddon(xbmcUtil.ViewAddonAbstract):
    ADDON_ID = 'plugin.video.ruutu'

    def __init__(self):
        xbmcUtil.ViewAddonAbstract.__init__(self)
        self.REMOVE = u'[COLOR red][B]•[/B][/COLOR] %s' % self.lang(30019)
        self.FAVOURITE = '[COLOR yellow][B]•[/B][/COLOR] %s'
        self.EXPIRES_DAYS = u'[COLOR brown]%d' + self.lang(
            30003) + '[/COLOR] %s'
        self.EXPIRES_HOURS = u'[COLOR red]%d' + self.lang(
            30002) + '[/COLOR] %s'
        self.GROUP_FORMAT = u'   [COLOR blue]%s[/COLOR]'
        self.NEXT = '[COLOR blue]   ➔  %s  ➔[/COLOR]' % self.lang(33078)

        self.addHandler(None, self.handleMain)
        self.addHandler('category', self.handleCategory)
        self.addHandler('serie', self.handleSeries)
        self.addHandler('programs', self.handlePrograms)
        self.favourites = {}
        self.initFavourites()
        self.enabledDownload = self.addon.getSetting(
            "enable-download") == 'true'

    def handleMain(self, pg, args):
        self.addViewLink('›› ' + self.lang(30020), 'programs', 1)
        self.addViewLink(self.lang(30028),
                         'category',
                         1,
                         {'link': 'http://www.ruutu.fi/views_cacheable_pager/videos/block_1?page=0%2C',
                             'grouping': True,
                             'pg-size': 10})
        self.addViewLink(self.lang(30030), 'category', 1,
                         {'link': 'http://www.ruutu.fi/views_cacheable_pager/videos/block_6?page=0%2C0%2C0%2C0%2C',
                             'pg-size': 10})  # yhden viikon ajalta
        self.addViewLink(self.lang(30021), 'category', 1,
                         {'link': 'http://www.ruutu.fi/views_cacheable_pager/' +
                             'videos_by_series/episodes_1/164876?page=0%2C',
                             'grouping': True, 'pg-size': 10})
        self.addViewLink(self.lang(30027), 'category', 1,
                         {'link': 'http://www.ruutu.fi/views_cacheable_pager/' +
                             'videos/block_2?page=0%2C', 'grouping': True, 'pg-size': 10})
        self.addViewLink(self.lang(30023), 'category', 1,
                         {'link': 'http://www.ruutu.fi/views_cacheable_pager/' +
                             'videos/block_3?page=0%2C', 'grouping': True, 'pg-size': 5})
        self.addViewLink(self.lang(30029), 'category', 1,
                         {'link': 'http://www.ruutu.fi/views_cacheable_pager/' +
                             'theme_liftups/block_8/Ruoka?' +
                             'page=0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C', 'grouping': 'True'})
        for title, link in self.favourites.items():
            t = title
            cm = [(self.createContextMenuAction(
                self.REMOVE, 'removeFav', {'name': t}))]
            self.addViewLink(self.FAVOURITE % t, 'serie', 1, {
                             'link': link, 'pg-size': 10}, cm)

    def initFavourites(self):
        fav = self.addon.getSetting("fav")
        if fav:
            try:
                favList = eval(fav)
                for title, link in favList.items():
                    self.favourites[title] = link
            except:
                pass

    def isFavourite(self, title):
        return title in self.favourites

    @staticmethod
    def getPageQuery(pg):
        return str(pg - 1) if pg > 0 else ''

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
        if items is not None:
            xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
            for item in items:
                if grouping and groupName != formatDate(item['published-ts']):
                    groupName = formatDate(item['published-ts'])
                    self.addVideoLink(self.GROUP_FORMAT % groupName, '', '')

                title = item['title']
                if markFav and self.isFavourite(title):
                    title = self.FAVOURITE % title
                if len(item['details']) > 0:
                    title += ': ' + item['details']
                    if len(title) > 50:
                        title = title[:50] + u'…'
                if len(item['episodeNum']) > 0 and len(item['seasonNum']) > 0:
                    title += ' [%s#%s]' % (item[
                                           'seasonNum'], item['episodeNum'])

                av = item['available']
                expiresInHours = int((int(av) - time.time()) / (60 * 60))

                availableText = item['available-text']
                if 24 > expiresInHours >= 0:
                    title = self.EXPIRES_HOURS % (expiresInHours, title)
                    availableText = '[COLOR red]%s[/COLOR]' % availableText
                elif 120 >= expiresInHours >= 0:
                    title = self.EXPIRES_DAYS % (expiresInHours / 24, title)
                    availableText = '[COLOR red]%s[/COLOR]' % availableText

                plot = '[B]%s[/B]\n\r%s\n\r%s' % (item[
                                                  'details'], item['desc'], availableText)

                episodeNum = item['episodeNum']
                seasonNum = item['seasonNum']
                contextMenu = []

                if self.enabledDownload:
                    contextMenu.append(
                        (self.createContextMenuAction('Download',
                                                      'download',
                                                      {'videoLink': item['link'],
                                                       'title': item['title']})))
                if item['published-ts'] is not None:
                    aired = item['published-ts'].strftime('%Y-%m-%d')
                else:
                    aired = ''
                self.addVideoLink(title, item['link'], item['image'],
                                  infoLabels={'plot': plot,
                                              'season': seasonNum,
                                              'episode': episodeNum,
                                              'aired': aired,
                                              'duration': item['duration']},
                                  contextMenu=contextMenu)
            if len(items) > 0 and len(items) >= pgSize:
                self.addViewLink(self.NEXT, handler, pg + 1, args)

    def handleSeriesJSON(self, pg, args):
        if 'link' in args:
            items = scrapJSON(args['link'])
            for item in items['video_episode']:
                link = 'http://arkisto.ruutu.fi/video?vt=video_episode&vid=' + \
                    item['video_filename'][:-4]
                image = 'http://arkisto.ruutu.fi/' + item['video_preview_url']
                self.addVideoLink(item['title'], link, image, '')

    def handlePrograms(self, pg, args):
        serieList = scrapPrograms()
        for serie in serieList:
            try:
                title = serie['name'].encode('utf-8').replace('&#039;', "'")
                menu = [(
                    self.createContextMenuAction(
                        self.FAVOURITE % self.lang(30017),
                        'addFav', {'name': serie['name'], 'link': serie['link']}))]
                if self.isFavourite(title):
                    title = self.FAVOURITE % title
                    menu = [(self.createContextMenuAction(
                        self.REMOVE, 'removeFav', {'name': serie['name']}))]

                self.addViewLink(title, 'serie', 1, {
                                 'link': serie['link'], 'pg-size': 1000}, menu)
            except:
                pass

    def handleAction(self, action, params):
        if action == 'addFav':
            self.favourites[params['name'].encode("utf-8")] = params['link']
            favStr = repr(self.favourites)
            self.addon.setSetting('fav', favStr)
            xbmcUtil.notification(self.lang(
                30006), params['name'].encode("utf-8"))
        elif action == 'removeFav':
            self.favourites.pop(params['name'])
            favStr = repr(self.favourites)
            self.addon.setSetting('fav', favStr)
            xbmcUtil.notification(self.lang(
                30007), params['name'].encode("utf-8"))
        elif action == 'download':
            downloadVideo(params['videoLink'], params['title'])
        else:
            super(ViewAddonAbstract, self).handleAction(self, action, params)  # NOQA

    def handleVideo(self, link):
        videoLink = scrapVideoLink(link)
        return videoLink

# -----------------------------------
ruutu = RuutuAddon()
lang = ruutu.lang
ruutu.handle()
