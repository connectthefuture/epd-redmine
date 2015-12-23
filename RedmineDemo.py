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
#from EPD import EPD

USER_ID_GAEL = 69

STATUS_ID_NEW = 1
STATUS_ID_WAIT = 4
STATUS_ID_IN_PROGRESS = 2
STATUS_ID_RID = 9
STATUS_ID_RIT = 3
STATUS_ID_RFV = 10
STATUS_ID_ASSIGNED = 12


def extractUsableStatuses(redmine):
    hashStatuses = {}
    # {1: u'New', 2: u'In Progress', 3: u'Ready in test', 4: u'Waiting feedback', 5: u'Closed', 6: u'Rejected',
    # 9: u'Ready in dev',10: u'Ready for validation', 11: u'Go for prod', 12: u'Assigned', 13: u'On Stable', 14: u'To Rollback'}

    allowed_statuses = ['New', 'In Progress', 'Ready in dev', 'Ready in test', 'Ready for validation', 'Waiting feedback', 'Assigned']

    issues_statuses = redmine.issue_status.all();
    
    for issue_status in issues_statuses:
                if issue_status.name in allowed_statuses:
                                hashStatuses[issue_status.id] = issue_status.name
    
    return hashStatuses

def isIssueToMe(issue): 
    return hasattr(issue, 'assigned_to') and issue.assigned_to.id == USER_ID_GAEL

def listIdsForStatus(redmine, projectName, statusId):
    issues = redmine.issue.filter(project_id=projectName, status_id=statusId)

    issue_ids = []
    for issue in issues:
                issue_ids.append(str(issue.id))
    
    usableStatuses = extractUsableStatuses(redmine)
    return usableStatuses[statusId] + ' (' + str(len(issues)) + '): ' + ', '.join(issue_ids)


def main(args):
    if len(args) != 2:
        sys.stderr.write('Please provide project name')
        return 1
    
    redmine = Redmine(RedmineCredential.host, key=RedmineCredential.key, requests={'verify': RedmineCredential.request_verify})

#   epd = EPD()

#   print('panel = {p:s} {w:d} x {h:d}  version={v:s} COG={g:d}'.format(p=epd.panel, w=epd.width, h=epd.height, v=epd.version, g=epd.cog))
#    epd.clear()
    
    print listIdsForStatus(redmine, args[1], STATUS_ID_NEW);
    print
    print listIdsForStatus(redmine, args[1], STATUS_ID_WAIT);
    print

    print listIdsForStatus(redmine, args[1], STATUS_ID_ASSIGNED);
    print
    print listIdsForStatus(redmine, args[1], STATUS_ID_RFV);
    print

    print listIdsForStatus(redmine, args[1], STATUS_ID_RID);
    print

    print listIdsForStatus(redmine, args[1], STATUS_ID_RIT);
    print

    print listIdsForStatus(redmine, args[1], STATUS_ID_IN_PROGRESS);

    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

