
# -*- coding: utf-8 -*-

import re

import os
import os.path
import time


import urllib.parse

import bs4


import runStatus
runStatus.preloadDicts = False
import nameTools as nt
import settings

import WebRequest
import MangaCMSOld.cleaner.processDownload

import MangaCMSOld.ScrapePlugins.RetreivalBase

class ContentLoader(MangaCMSOld.ScrapePlugins.RetreivalBase.RetreivalBase):




	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Hitomi.Cl"
	pluginName = "Hitomi Content Retreiver"
	tableKey   = "hit"
	urlBase = "https://hitomi.la/"


	tableName = "HentaiItems"


	retreivalThreads = 3


	def getFileName(self, soup):
		title = soup.find("h1")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text().strip()


	def imageUrls(self, soup):
		thumbnailDiv = soup.find("div", id="thumbnail-container")

		ret = []

		for link in thumbnailDiv.find_all("a", class_='gallerythumb'):

			referrer = urllib.parse.urljoin(self.urlBase, link['href'])
			if hasattr(link, "data-src"):
				thumbUrl = link.img['data-src']
			else:
				thumbUrl = link.img['src']

			if not "t." in thumbUrl[-6:]:
				raise ValueError("Url is not a thumb? = '%s'" % thumbUrl)
			else:
				imgUrl = thumbUrl[:-6] + thumbUrl[-6:].replace("t.", '.')

			imgUrl   = urllib.parse.urljoin(self.urlBase, imgUrl)
			imgUrl = imgUrl.replace("//t.", "//i.")

			ret.append((imgUrl, referrer))

		return ret




	def format_tag(self, tag_raw):
		if "♀" in tag_raw:
			tag_raw = tag_raw.replace("♀", "")
			tag_raw = "female " + tag_raw
		if "♂" in tag_raw:
			tag_raw = tag_raw.replace("♂", "")
			tag_raw = "male " + tag_raw

		tag = tag_raw.strip()
		while "  " in tag:
			tag = tag.replace("  ", " ")
		tag = tag.strip().replace(" ", "-")
		return tag.lower()

	def getCategoryTags(self, soup):
		tablediv = soup.find("div", class_='gallery-info')
		tagTable = soup.find("table")

		tags = []

		formatters = {
						"series"     : "parody",
						"characters" : "characters",
						"tags"       : "",
					}

		ignoreTags = [
					"type",
					]

		# print("soup.h2", )

		category = "Unknown?"

		for tr in tagTable.find_all("tr"):
			if len(tr.find_all("td")) != 2:
				continue

			what, values = tr.find_all("td")

			what = what.get_text().strip().lower()
			if what in ignoreTags:
				continue
			elif what == "Type":
				category = values.get_text().strip()
				if category == "Manga One-shot":
					category = "=0= One-Shot"
			elif what == "language":

				lang_tag = values.get_text().strip()
				lang_tag = self.format_tag("language " + lang_tag)
				tags.append(lang_tag)

			elif what in formatters:
				for li in values.find_all("li"):
					tag = " ".join([formatters[what], li.get_text()])
					tag = self.format_tag(tag)
					tags.append(tag)

		artist_str = "unknown artist"
		for artist in soup.h2("li"):
			artist_str = artist.get_text()
			atag = "artist " + artist_str
			atag = self.format_tag(atag)
			tags.append(atag)

		# print(category, tags)
		return category, tags, artist_str

	def getDownloadInfo(self, linkDict):
		sourcePage = linkDict["sourceUrl"]

		self.log.info("Retrieving item: %s", sourcePage)

		self.updateDbEntry(linkDict["sourceUrl"], dlState=1)

		soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': 'https://hitomi.la/'})

		if not soup:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")

		gal_section = soup.find("div", class_='gallery')


		category, tags, artist = self.getCategoryTags(gal_section)
		tags = ' '.join(tags)
		linkDict['artist'] = artist
		linkDict['title'] = self.getFileName(gal_section)
		linkDict['dirPath'] = os.path.join(settings.hitSettings["dlDir"], nt.makeFilenameSafe(category))

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])

		self.log.info("Folderpath: %s", linkDict["dirPath"])

		self.log.debug("Linkdict = ")
		for key, value in list(linkDict.items()):
			self.log.debug("		%s - %s", key, value)


		if tags:
			self.log.info("Adding tag info %s", tags)
			self.addTags(sourceUrl=linkDict["sourceUrl"], tags=tags)


		read_url = soup.find("a", text=re.compile("Read Online", re.IGNORECASE))
		spage = urllib.parse.urljoin(self.urlBase, read_url['href'])

		linkDict["spage"] = spage

		self.updateDbEntry(linkDict["sourceUrl"], seriesName=category, lastUpdate=time.time())

		return linkDict

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content

	def extract_cdn_subdomain(self, url):
		# var number_of_frontends = 2;
		number_of_frontends = 2
		# function subdomain_from_galleryid(g) {
		#         if (adapose) {
		#                 return '0';
		#         }
		#         return String.fromCharCode(97 + (g % number_of_frontends));
		# }

		# function subdomain_from_url(url, base) {
		#         var retval = 'a';
		#         if (base) {
		#                 retval = base;
		#         }

		#         var r = /\/(\d+)\//;
		#         var m = r.exec(url);
		#         var g;
		#         if (m) {
		#                 g = parseInt(m[1]);
		#         }
		#         if (g) {
		#                 retval = subdomain_from_galleryid(g) + retval;
		#         }

		#         return retval;
		# }

		# function url_from_url(url, base) {
		#         return url.replace(/\/\/..?\.hitomi\.la\//, '//'+subdomain_from_url(url, base)+'.hitomi.la/');
		# }

		chunks = [tmp for tmp in url.split("/") if tmp and all([char in '0123456789' for char in tmp])]

		if len(chunks) != 1:
			raise RuntimeError("Too many (or too few) chunks: '%s'" % chunks)

		g = int(chunks[0])

		subid = chr(97 + (g % number_of_frontends)) + "a"

		return subid


	def getImages(self, linkDict):

		# print("getImage", linkDict)

		soup = self.wg.getSoup(linkDict['spage'], addlHeaders={'Referer': linkDict["sourceUrl"]})

		raw_imgs = soup.find_all('div', class_="img-url")

		imageurls = []


		for div in raw_imgs:
			imgurl = div.get_text().strip()
			# print("ImageURL:", imgurl)
			imgurl = re.sub(r"\/\/..?\.hitomi\.la\/", 'https://{}.hitomi.la/'.format(self.extract_cdn_subdomain(imgurl)), imgurl, flags=re.IGNORECASE)
			# print("ImageURL:", imgurl)
			imageurls.append((imgurl, linkDict['spage']))
		if not imageurls:
			return []

		images = []


		for imageurl, referrer in imageurls:
			images.append(self.getImage(imageurl, referrer))

		return images


	def getLink(self, linkDict):
		try:
			linkDict = self.getDownloadInfo(linkDict)
			images = self.getImages(linkDict)
			title  = linkDict['title']
			artist = linkDict['artist']

		except WebRequest.WebGetException:
			self.updateDbEntry(linkDict["sourceUrl"], dlState=-2, downloadPath="ERROR", fileName="ERROR: FAILED")
			return False

		if images and title:
			fileN = title+" "+artist+".zip"
			fileN = nt.makeFilenameSafe(fileN)
			wholePath = os.path.join(linkDict["dirPath"], fileN)

			wholePath = self.save_image_set(wholePath, images)

			self.log.info("Successfully Saved to path: %s", wholePath)


			self.updateDbEntry(linkDict["sourceUrl"], downloadPath=linkDict["dirPath"], fileName=fileN)

			# Deduper uses the path info for relinking, so we have to dedup the item after updating the downloadPath and fileN
			dedupState = MangaCMSOld.cleaner.processDownload.processDownload(None, wholePath, pron=True, deleteDups=True, includePHash=True, rowId=linkDict['dbId'])
			self.log.info( "Done")

			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)


			self.updateDbEntry(linkDict["sourceUrl"], dlState=2)

			return wholePath

		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			return False



	def setup(self):
		self.wg.stepThroughJsWaf(self.urlBase, titleContains="Hitomi")


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = ContentLoader()
		# run.getDownloadInfo({'sourceUrl':'https://hitomi.la/galleries/284.html'})
		run.do_fetch_content()
