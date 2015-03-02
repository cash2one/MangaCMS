## -*- coding: utf-8 -*-
<!DOCTYPE html>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="treeRender"      file="/books/render.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>

	${ut.headerBase()}

	<script type="text/javascript">
		$(document).ready(function() {
		// Tooltip only Text

	</script>

	<link rel="stylesheet" href="/books/treeview.css">

</head>


<%
startTime = time.time()
# print("Rendering begun")
%>


<%!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import settings
import string

import urllib.parse
%>

<%
startTime = time.time()
# print("Rendering begun")
%>

<%def name="renderRow(rowData)">
	<h2>LNDB Book Series: </h2>
</%def>

<%def name="renderError(rowData)">
	<h2>LNDB Book Series: </h2>
</%def>



<%def name="queryError(errStr=None)">
	<br>

	<div class="errorPattern">
		<h2>Content Error!</h2>
		<p>${errStr}</p>

	</div>




</%def>


<%def name="renderId(itemId)">
	<%

	cursor = sqlCon.cursor()

	cursor.execute("""SELECT dbid,
							changestate,
							ctitle,
							otitle,
							vtitle,
							jtitle,
							jvtitle,
							series,
							pub,
							label,
							volno,
							author,
							illust,
							target,
							description,
							seriesentry,
							covers,
							readingprogress,
							availprogress,
							rating,
							reldate,
							lastchanged,
							lastchecked,
							firstseen FROM books_lndb WHERE dbid=%s;""", (itemId, ))
	item = cursor.fetchone()

	%>


	<h2>Book item ${itemId}</h2>
	<div>
		${item}
	</div>
</%def>


<%def name="render()">
	<%


	if "dbid" in request.params:
		try:
			seriesId = int(request.params["dbid"])
			renderId(seriesId)
			return
		except:
			pass

	queryError("No item ID in URL!")

	%>

</%def>


<body>


	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv">
				<div class="contentdiv">
					<%
					render()

					%>


				</div>

			</div>
		</div>
	</div>


	<%
	fsInfo = os.statvfs(settings.mangaFolders[1]["dir"])
	stopTime = time.time()
	timeDelta = stopTime - startTime
	%>

	<p>
		This page rendered in ${timeDelta} seconds.<br>
		Disk = ${int((fsInfo.f_bsize*fsInfo.f_bavail) / (1024*1024))/1000.0} GB of  ${int((fsInfo.f_bsize*fsInfo.f_blocks) / (1024*1024))/1000.0} GB Free.
	</p>

</body>
</html>