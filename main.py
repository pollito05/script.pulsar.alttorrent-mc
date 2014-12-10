# coding: utf-8
from pulsar import provider
import re
import common
import xbmc

#clear cache
if provider.ADDON.getSetting('clear_cache') == 'true':
    import xbmcvfs
    provider.ADDON.setSetting('clear_cache','false')
    path = xbmc.translatePath('special://temp')
    xbmcvfs.delete(path + 'alt-torrent.db')

# this read the settings
values3 = {'ALL': 0, 'HDTV': 1,'480p': 1,'DVD': 1,'720p': 2 ,'1080p': 3, '3D': 3, "1440p": 4 ,"2K": 5,"4K": 5} #code_resolution steeve

# this read the settings
settings = common.Settings()
# define the browser
browser = common.Browser()
# create the filters
filters = common.Filtering()

#premium account
username = provider.ADDON.getSetting('username') # username
password = provider.ADDON.getSetting('password') # passsword

# open login_check
browser.login(settings.url + '/ajax/login_check_user.php', {'user': username}, "true")
browser.login(settings.url + '/ajax/login_check_pass.php', {'user': username, 'password': password}, "true")

# open login_check
browser.login(settings.url + '/ajax/login_check.php', {'user': username, 'password': password}, "true")
if browser.content != 'true' :  # login
    provider.notify(message=browser.status, header='ERROR!!', time=5000, image=settings.icon)
    provider.log.error('******** %s ********' % browser.status)


def get_url(scd_link): # find url from adf.ly
    browser1 = common.Browser()
    url = 'http://www.bypassshorturl.com/get.php'
    values = {'url': scd_link }
    browser1.login(url,values,'true')
    return browser1.content


def get_torrent(torrent):
    url_code = '%s/movie/%s.html' % (settings.url,torrent)
    browser.open(url_code)
    data = browser.content
    code = re.search('{id:(.*?),',data).group(1)
    browser.open('%s/ajax/download.html?id=%s&code=1' % (settings.url,code))
    url_adfly = browser.content
    return get_url(url_adfly)


def extract_magnets(key):
    try:
        url_search = "%s?q=%s" % (settings.url, key)
        provider.log.info(url_search)
        browser.open(url_search)
        data = browser.content
        size = re.findall('(.*?)&nbsp;<span class="icon-hdd">',data)
        results = []
        for cm,(temp,torrent) in enumerate(re.findall('class="thumbnail"(.*?)/movie/(.*?).html',data, re.S)):
            if '3D' in torrent: resASCII = '3D'
            if '1080p' in torrent: resASCII = '1080p'
            if '720p' in torrent: resASCII = '720p'
            name = torrent.replace('-',' ') + ' - ' + size[cm].lstrip() + ' - ' + settings.name_provider
            results.append({'name' : name, 'uri' : get_torrent(torrent) , 'resolution' : values3[resASCII], 'filesize' : size[cm].lstrip()})
        return results
    except:
        provider.log.error('>>>>>>>ERROR parsing data<<<<<<<')
        provider.notify(message='ERROR parsing data', header=None, time=5000, image=settings.icon)


def  get_magnets(key):
    results= []
    import shelve
    path = xbmc.translatePath('special://temp')
    s = shelve.open(path + 'alt-torrent.db')
    if not key in s:
        torrents = extract_magnets(key)
        if torrents is not None:
            s[key] = torrents
            s.sync()
            if settings.time_noti > 0 : provider.notify(message='Creating Cache...  Please, trying again...', header = None, time = 2000, image = settings.icon)
    else:
        torrents = s[key]
    filters.information()
    if torrents is not None:
        for torrent in torrents:
            name = torrent['name']
            size = torrent['filesize']
            filters.title = name
            if filters.verify(name, size):
                #yield torrent
                results.append(torrent)
                provider.log.info(torrent['uri'] + ' ++++ ADDED +++')
            else:
                provider.log.warning(filters.reason)
    s.close()
    return results


def search(query):
    return []


def search_movie(info):
    filters.use_movie()
    if settings.time_noti > 0 : provider.notify(message='Searching: ' + info['title'].encode('utf-8').title()  + '...', header = None, time = settings.time_noti, image = settings.icon)
    return get_magnets(info['imdb_id'].encode('utf-8'))


def search_episode(info):
    # just movies site
    return []

# This registers your module for use
provider.register(search, search_movie, search_episode)