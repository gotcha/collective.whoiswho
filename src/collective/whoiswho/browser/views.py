from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName

from Products.Five import BrowserView


class BaseView(BrowserView):

    def __init__(self, context, request):
        super(BaseView, self).__init__(context, request)
        self.groups_tool = getToolByName(self.context, 'portal_groups')
        self.membership_tool = getToolByName(self.context, 'portal_membership')
        context_url = self.context.absolute_url()
        self.all_groups_url = "{0}/@@who-is-who".format(context_url)
        self.group_details_url = "{0}/@@who-group-members".format(context_url)
        self.member_url = "{0}/@@who-member".format(context_url)

    @property
    def portal_state(self):
        return getMultiAdapter((self.context, self.request),
                name=u"plone_portal_state")

    def getGroupInfo(self, id):
        group = self.groups_tool.getGroupById(id)
        result = dict(group=group,
                title=group.getGroupTitleOrName(),
                description=group.getProperty('description', ''),
                url="{0}?group_id={1}".format(self.group_details_url, id))
        return result

    def getMemberInfo(self, id):
        member_info = self.membership_tool.getMemberInfo(id)
        member = self.membership_tool.getMemberById(id)
        summary_view = getMultiAdapter((member, self.request),
                name=u"who-member-summary")
        group_ids = self.groups_tool.getGroupsForPrincipal(member)
        result = dict(title=member_info['fullname'],
                summary=summary_view(),
                url="{0}?member_id={1}".format(self.member_url, id),
                group_ids=group_ids,
                member=member)
        return result

    def getGroupsSortedByTitle(self, group_ids):
        result = list()
        for id in group_ids:
            result.append(self.getGroupInfo(id))
        result.sort(cmp_by_title)
        return result


def cmp_by_title(a, b):
    return cmp(a['title'], b['title'])


class Whoiswho(BaseView):

    def groups(self):
        group_ids = self.groups_tool.getGroupIds()
        return self.getGroupsSortedByTitle(group_ids)


class GroupMembers(BaseView):

    def __init__(self, context, request):
        super(GroupMembers, self).__init__(context, request)
        self.group = self.getGroupInfo(request.group_id)

    def members(self):
        result = list()
        for id in self.group['group'].getMemberIds():
            result.append(self.getMemberInfo(id))
        result.sort(cmp_by_title)
        return result


class Member(BaseView):

    def __init__(self, context, request):
        super(Member, self).__init__(context, request)
        member_id = request.member_id
        self.member = self.getMemberInfo(member_id)
        group_ids = self.member['group_ids']
        self.groups = self.getGroupsSortedByTitle(group_ids)

    def details(self):
        details_view = getMultiAdapter((self.member['member'], self.request),
                name=u"who-member-details")
        return details_view()


class MemberSummary(BrowserView):

    def __call__(self):
        return ''


class MemberDetails(BrowserView):

    def author_url(self):
        portal_url = self.portal_state.portal_url()
        base_url = "{0}/author".format(portal_url)
        author_url = "{0}/{1}".format(base_url, self.context.getId())
        return author_url

    @property
    def portal_state(self):
        return getMultiAdapter((self.context, self.request),
                name=u"plone_portal_state")
