#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  redmine.py
#
#  Copyright 2015 LGnap <lgnap@desktop.helpcomputer.ovh>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

from redmine import Redmine
import RedmineCredential
import textwrap
import re
from PIL import Image
from PIL import ImageDraw, ImageFont
#from EPD import EPD

USER_ID_GAEL = 69

STATUS_ID_NEW = 1
STATUS_ID_WAIT = 4
STATUS_ID_IN_PROGRESS = 2
STATUS_ID_RID = 9
STATUS_ID_RIT = 3
STATUS_ID_RFV = 10
STATUS_ID_ASSIGNED = 12

WHITE = 1
BLACK = 0
fontTitles = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",12)
fontIssues = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",11)
fontBoldIssues = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",11)


def extractUsableStatuses(redmine):
    hashStatuses = {}
    # {1: u'New', 2: u'In Progress', 3: u'Ready in test', 4: u'Waiting feedback', 5: u'Closed', 6: u'Rejected',
    # 9: u'Ready in dev',10: u'Ready for validation', 11: u'Go for prod', 12: u'Assigned', 13: u'On Stable', 14: u'To Rollback'}

    allowed_statuses = ['New', 'In Progress', 'Ready in dev', 'Ready in test', 'Ready for validation', 'Waiting feedback', 'Assigned']

    issues_statuses = redmine.issue_status.all()

    for issue_status in issues_statuses:
                if issue_status.name in allowed_statuses:
                                hashStatuses[issue_status.id] = issue_status.name

    return hashStatuses


def isIssueToMe(issue):
    return hasattr(issue, 'assigned_to') and issue.assigned_to.id == USER_ID_GAEL


def listIdsForStatus(redmine, projectName, statusId):
    return redmine.issue.filter(project_id=projectName, status_id=statusId)


def listIdsForQuery(redmine, projectName, queryId):
    return redmine.issue.filter(project_id=projectName, query_id=queryId)


def transferToEpd(epd, image):
    # display image on the panel
    epd.clear()
    epd.display(image)
    epd.update()

def transferToScreen(image):
    image.save('/tmp/redmine.jpg')

def drawDots(draw):

    # three pixels in bottom left corner
    draw.point((0, 175), fill=BLACK)
    draw.point((1, 175), fill=BLACK)
    draw.point((0, 174), fill=BLACK)
    # three pixels in bottom right corner
    draw.point((263, 175), fill=BLACK)
    draw.point((262, 175), fill=BLACK)
    draw.point((263, 174), fill=BLACK)


def createImage(size):
    # initially set all white background
    return Image.new('RGB', size, "white")


def drawColumnTitles(draw):
    draw.text((10, 1), 'Assigned', font=fontTitles, fill=BLACK)
    draw.text((91, 1), 'In progress', font=fontTitles, fill=BLACK)
    draw.text((186, 1), 'Ready ...', font=fontTitles, fill=BLACK)
    return draw.textsize('Assigned', font=fontTitles)


def drawLines(draw, headerLineHeight):
    #headers
    draw.line([(0, headerLineHeight), (263, headerLineHeight)], fill=BLACK)

    #columns
    draw.line([(88, 0), (88, 140)], fill=BLACK)
    draw.line([(176, 0), (176, 140)], fill=BLACK)


def drawMultiColumnContent(draw, headerLineHeight, xPos, issues):
    if len(issues) == 0:
        return
    currentY = headerLineHeight + 3
    textSize = draw.textsize(issues[0].subject, font=fontIssues)
    currentX = xPos

    for issue in issues:
        if isIssueToMe(issue):
            draw.text((currentX, currentY), str(issue.id), font=fontBoldIssues, fill=BLACK)

        else:
            draw.text((currentX, currentY), str(issue.id), font=fontIssues, fill=BLACK)
        currentX += 40
        if (currentX == xPos + 80):
            currentY += textSize[1] + 5
            currentX = xPos


def drawBottomText(draw, issuesNew, issuesWait):
    draw.text((2, 145), formatIssues('New', issuesNew), font=fontIssues, fill=BLACK)
    draw.text((2, 160), formatIssues('Wait', issuesWait), font=fontIssues, fill=BLACK)


def formatIssues(label, issues):
    issueIds = []
    for issue in issues:
        issueIds.append(str(issue.id))

    stringBuilder = label + ' (' + str(len(issueIds)) + '): ' + ', '.join(issueIds)
    wrappedText = textwrap.wrap(stringBuilder, 40)
    return re.sub(r',$', '...', wrappedText[0])


def main(args):
    if len(args) != 2:
        sys.stderr.write("Please provide project name !\n")
        return 1

    redmine = Redmine(RedmineCredential.host, key=RedmineCredential.key, requests={'verify': RedmineCredential.request_verify})

#    epd = EPD()
#    epd.size
#    print('panel = {p:s} {w:d} x {h:d}  version={v:s} COG={g:d}'.format(p=epd.panel, w=epd.width, h=epd.height, v=epd.version, g=epd.cog))
    fakeSize = [264, 176]

    image = createImage(fakeSize)
    # prepare for drawing
    draw = ImageDraw.Draw(image)

    drawDots(draw)

    # column title: text
    columnsTitleSize = drawColumnTitles(draw)
    headerLineHeight = columnsTitleSize[1] + 2

    drawLines(draw, headerLineHeight)

    issuesNew = listIdsForStatus(redmine, args[1], STATUS_ID_NEW)
    issuesWait = listIdsForStatus(redmine, args[1], STATUS_ID_WAIT)

    drawBottomText(draw, issuesNew, issuesWait)

    drawMultiColumnContent(draw, headerLineHeight, 5, listIdsForStatus(redmine, args[1], STATUS_ID_ASSIGNED))
    drawMultiColumnContent(draw, headerLineHeight, 95, listIdsForStatus(redmine, args[1], STATUS_ID_IN_PROGRESS))
    drawMultiColumnContent(draw, headerLineHeight, 185,
        listIdsForQuery(redmine, args[1], 69)
    )

#    transferToEpd(epd, image)
    transferToScreen(image)

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
