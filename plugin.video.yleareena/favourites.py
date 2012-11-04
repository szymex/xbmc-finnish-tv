# -*- coding: utf-8 -*-
import xbmc, xbmcaddon

def favExists(name):
	strCat=''
	try:	
		f = open(os.path.join(BASE_PATH,'favourites.txt') )
		try:
			strCat = f.read().split('\n')
		finally:
			f.close()
	except:
		return False
	
	for cat in strCat:
		if not cat.startswith('#'):
			splCat = cat.split("|")
			if (len(splCat)==2 and splCat[0].strip() == name):
				return True
	return False

def addFavourite(name, urlName):
	f = open(os.path.join(BASE_PATH,'favourites.txt'), "a+")
	try:
		f.write("\n" + name + "\t | " + urlName)
	finally:
		f.close()

def removeFavourite(name):
	strCat=''
	f = open(os.path.join(BASE_PATH,'favourites.txt') )
	try:
		strCat = f.read().split('\n')
	finally:
		f.close()
	
	savedFav = []	
	for cat in strCat:
		if not cat.startswith('#'):
			splCat = cat.split("|")
			if (len(splCat)==2 and splCat[0].strip() == name):
				strCat.remove(cat)
	
	f = open(os.path.join(BASE_PATH,'favourites.txt'), "w+" )
	try:
		for item in strCat:
  			f.write("%s\n" % item)
		return True
	finally:
		f.close()
	return False

#--------------------------------------------

BASE_PATH = xbmcaddon.Addon('plugin.video.yleareena').getAddonInfo('path')

command = sys.argv[1]
if command=="-add":
	name = sys.argv[2]
	urlName = sys.argv[3]

	if favExists(name)==True :
		xbmc.executebuiltin( "XBMC.Notification(Exists,Series: "+name+" already exists,30)")
		xbmc.log( "not added, series: "+name + " | " + urlName + " already exists", xbmc.LOGDEBUG )
		
	else:	
		addFavourite(name, urlName)
		xbmc.executebuiltin( "XBMC.Notification(Added,"+name+",30)")
		xbmc.log( "added favourites: "+name + " | " + urlName, xbmc.LOGDEBUG )

elif command=="-remove" :
	name = sys.argv[2]
	if removeFavourite(name)==True :
		xbmc.executebuiltin( "XBMC.Notification(Success,Removed: "+name+",30)")
	else:
		xbmc.executebuiltin( "XBMC.Notification(Failed,Did not remove: "+name+",30)")
		
else:
	xbmc.executebuiltin( "XBMC.Notification(Error,Unknown operation: "+command+",30)")

