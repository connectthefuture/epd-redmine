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
import sys
import RedmineCredential
import textwrap
import re
import time
import netifaces
from PIL import Image
from PIL import ImageDraw, ImageFont

IMAGE_PATH = '/tmp/redmine.jpg'
from EPD import EPD

STATUS_ID_NEW = 1
STATUS_ID_IN_PROGRESS = 2
STATUS_ID_RESOLVED = 3
STATUS_ID_NEED_FEED = 4
STATUS_ID_CLOSED = 5

WHITE = 1
BLACK = 0

SCREEN_SIZE_X = 264 - 1
SCREEN_SIZE_Y = 176 - 1

BLOCK_1_BOTTOM = SCREEN_SIZE_Y / 2 - 10
BLOCK_2_TOP = SCREEN_SIZE_Y / 2
BLOCK_NB_ISSUES_MAX = 7


fontTitles = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 12)
fontIssues = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 11)
fontItalicIssues = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 11)
fontStatus = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 9)
fontBoldIssues = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 11)
issues = []


def isIssueToMe(issue):
    return hasattr(issue, 'assigned_to') and issue.assigned_to.id == RedmineCredential.USER_ID


def listIdsForStatus(redmine, projectName, statusId):
    global issues
    if not issues:
        issues = redmine.issue.filter(project_id=projectName, sort='updated_on:desc')

    return [issue for issue in issues if issue.status.id == statusId]


def transferToEpd(epd, image, full):
    # display image on the panel
    epd.display(image.rotate(180))

    if full:
        epd.clear()
        epd.update()
    else:
        epd.partial_update()


def getIpAddress():
    defaultGateway = netifaces.gateways()['default']
    if netifaces.AF_INET not in defaultGateway:
        return 'not connected'

    ipv4Gateway = defaultGateway[netifaces.AF_INET]
    ipv4InterfaceName = ipv4Gateway[1]
    interface = netifaces.ifaddresses(ipv4InterfaceName)
    ipv4Interface = interface[netifaces.AF_INET]
    return ipv4Interface[0]['addr']

def transferToScreen(image):  # monitor image with qiv --watch --fixed_zoom 150 /tmp/redmine.jpg
    image.save(IMAGE_PATH)


def drawDots(draw):

    # three pixels in bottom left corner
    draw.point((0, SCREEN_SIZE_Y), fill=BLACK)
    draw.point((1, SCREEN_SIZE_Y), fill=BLACK)
    draw.point((0, SCREEN_SIZE_Y - 1), fill=BLACK)
    # three pixels in bottom right corner
    draw.point((SCREEN_SIZE_X, SCREEN_SIZE_Y), fill=BLACK)
    draw.point((SCREEN_SIZE_X - 1, SCREEN_SIZE_Y), fill=BLACK)
    draw.point((SCREEN_SIZE_X, SCREEN_SIZE_Y - 1), fill=BLACK)


def createImage(size):
    # initially set all white background
    return Image.new('RGB', size, "white")


def drawColumnTitles(draw):
    draw.text((25, 1), 'New', font=fontTitles, fill=BLACK)
    draw.text((91, 1), 'In progress', font=fontTitles, fill=BLACK)
    draw.text((190, 1), 'Resolved', font=fontTitles, fill=BLACK)

    draw.text((5, BLOCK_2_TOP + 1), 'Need Feed', font=fontTitles, fill=BLACK)
    draw.text((110, BLOCK_2_TOP + 1), 'Closed', font=fontTitles, fill=BLACK)

    return draw.textsize('Assigned', font=fontTitles)


def drawLines(draw, headerLineHeight):
    #headers
    draw.line([(0, headerLineHeight), (SCREEN_SIZE_X, headerLineHeight)], fill=BLACK)
    draw.line([(0, BLOCK_2_TOP + headerLineHeight), (SCREEN_SIZE_X, BLOCK_2_TOP + headerLineHeight)], fill=BLACK)

    #columns
    draw.line([(88, 0), (88, BLOCK_1_BOTTOM)], fill=BLACK)
    draw.line([(176, 0), (176, BLOCK_1_BOTTOM)], fill=BLACK)

    draw.line([(88, BLOCK_2_TOP), (88, SCREEN_SIZE_Y)], fill=BLACK)
    draw.line([(176, BLOCK_2_TOP), (176, SCREEN_SIZE_Y)], fill=BLACK)


def drawClock(draw):
    clockText = time.strftime('%H:%M')
    textSize = draw.textsize(clockText, font=fontStatus)
    draw.text(
        (textSize[0], BLOCK_1_BOTTOM),
        clockText,
        font=fontStatus,
        fill=BLACK)


def drawIpAddress(draw, ipAddress):
    textSize = draw.textsize(ipAddress, font=fontStatus)
    draw.text(
        (SCREEN_SIZE_X - textSize[0] - 2, BLOCK_1_BOTTOM),
        ipAddress,
        font=fontStatus,
        fill=BLACK)


def drawNbIssues(draw, currentX, currentY, nbIssues):
    draw.text((currentX, currentY), '(' + str(nbIssues) + ')', font=fontItalicIssues, fill=BLACK)


def drawMultiColumnContent(draw, headerLineHeight, xPos, issues):
    nbIssues = len(issues)
    currentX = xPos
    currentY = headerLineHeight + 3

    if nbIssues == 0:
        drawNbIssues(draw, currentX, currentY, nbIssues)
        return

    textSize = draw.textsize(issues[0].subject, font=fontIssues)

    nbIssuesDisplayed = 0
    for issue in issues:
        if nbIssuesDisplayed == BLOCK_NB_ISSUES_MAX:
            break
        if isIssueToMe(issue):
            draw.text((currentX, currentY), str(issue.id), font=fontBoldIssues, fill=BLACK)
        else:
            draw.text((currentX, currentY), str(issue.id), font=fontIssues, fill=BLACK)
        currentX += 40
        nbIssuesDisplayed += 1
        if (currentX == xPos + 80):
            currentY += textSize[1] + 5
            currentX = xPos

    drawNbIssues(draw, currentX, currentY, nbIssues)


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
    epdFound = True
    if len(args) != 2:
        sys.stderr.write("Please provide project name !\n")
        return 1

    projectName = args[1]

    redmine = Redmine(RedmineCredential.host, key=RedmineCredential.key,
        requests={'verify': RedmineCredential.request_verify})

    imageSize = [SCREEN_SIZE_X + 1, SCREEN_SIZE_Y + 1]
    try:
        epd = EPD()
        print('panel = {p:s} {w:d} x {h:d}  version={v:s} COG={g:d}'.format(p=epd.panel, w=epd.width, h=epd.height, v=epd.version, g=epd.cog))
        imageSize = epd.size
    except IOError:
        sys.stderr.write("Hooops no EPD found. Auto fallback to '" + IMAGE_PATH + "'\n")
        epdFound = False

    counter = 0
    try:
        while True:
            global issues
            issues = []

            image = createImage(imageSize)
            # prepare for drawing
            draw = ImageDraw.Draw(image)

            #drawDots(draw)

            # column title: text
            columnsTitleSize = drawColumnTitles(draw)
            headerLineHeight = columnsTitleSize[1] + 2

            ipAddress = getIpAddress()
            issuesNew = issuesInProgress = issuesResolved = issuesNeedFeed = issuesClosed = []

            try:
                issuesNew = listIdsForStatus(redmine, projectName, STATUS_ID_NEW)
                issuesInProgress = listIdsForStatus(redmine, projectName, STATUS_ID_IN_PROGRESS)
                issuesResolved = listIdsForStatus(redmine, projectName, STATUS_ID_RESOLVED)
                issuesNeedFeed = listIdsForStatus(redmine, projectName, STATUS_ID_NEED_FEED)
                issuesClosed = listIdsForStatus(redmine, projectName, STATUS_ID_CLOSED)
            except Exception as e:
                print e

            drawLines(draw, headerLineHeight)

            drawIpAddress(draw, ipAddress)
            drawClock(draw)

            drawMultiColumnContent(draw, headerLineHeight, 5, issuesNew)
            drawMultiColumnContent(draw, headerLineHeight, 95, issuesInProgress)
            drawMultiColumnContent(draw, headerLineHeight, 185, issuesResolved)

            headerLineHeightSecondScreen = SCREEN_SIZE_Y / 2 + headerLineHeight
            drawMultiColumnContent(draw, headerLineHeightSecondScreen, 5, issuesNeedFeed)
            drawMultiColumnContent(draw, headerLineHeightSecondScreen, 95, issuesClosed)
#            drawMultiColumnContent(draw, headerLineHeightSecondScreen, 185, issuesWait)

            if epdFound:
                transferToEpd(epd, image, counter % (60 * 15) == 0)
            else:
                transferToScreen(image)
            time.sleep(60)
            counter += 60

    except KeyboardInterrupt:  # Exit by typing CTRL-C
        print ("You hit CTRL-C")

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
