from __future__ import division
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from builtins import range
from builtins import object
from past.utils import old_div
from django.urls import reverse
from django.conf import settings
from django.core.paginator import Paginator as corePaginator


def _adj_range(adjacent_pages, page_obj, page_range):
    l = list(page_range)
    current = page_obj.number - 1

    left_cut = right_cut = []
    left = l[1:current]

    first = [l[0]]
    last = [l[-1]]

    if page_obj.number == l[0]:
        first = []
    elif len(left) > adjacent_pages:
        left = left[-adjacent_pages:]
        left_cut = [0]

    right = l[current + 1: -1]
    if page_obj.number == l[-1]:
        last = []
    if len(right) > adjacent_pages:
        right = right[:adjacent_pages]
        right_cut = [0]

    sep_list = first + left_cut + left + [page_obj.number] + right + right_cut + last
    return sep_list


class DjangoplicityPaginator (corePaginator):
    def __init__(self, *args, **kwargs):
        self.adjacent_pages = kwargs.get("adjacent_pages", None)
        if not self.adjacent_pages:
            self.adjacent_pages = getattr(settings, 'PAGINATOR_ADJ', 3)
        super(DjangoplicityPaginator, self).__init__(*args, **kwargs)

    def adj_range(self, page_obj):
        return _adj_range(self.adjacent_pages, page_obj, self.page_range)


class DjangoplicityQuerySetPaginator (corePaginator):
    def __init__(self, *args, **kwargs):
        self.adjacent_pages = kwargs.get("adjacent_pages", None)
        if not self.adjacent_pages:
            self.adjacent_pages = getattr(settings, 'PAGINATOR_ADJ', 3)
        super(DjangoplicityQuerySetPaginator, self).__init__(*args, **kwargs)

    def adj_range(self, page_obj):
        return _adj_range(self.adjacent_pages, page_obj, self.page_range)


class Paginator (object):
    """
    given sizes, offsets, etc, returns a dictionary with pagination parameters
    makes sure there is no negative indexing
    """
    DEF_PAGINATE_BY = 10
    DEF_PAGINATE_BY_ONELINELIST = 50
    DEF_PAGINATE_BY_FEATURELIST = 10
    DEF_PAGINATE_SHOW_BOUNDS = 5  # show current page plus X pages to each side

    @staticmethod
    def paginate(total, page=1, paginate_by=DEF_PAGINATE_BY, view_name='', pre_args=None, post_args=None, limit=None):
        if pre_args is None:
            pre_args = []
        if post_args is None:
            post_args = []

        page = page - 1
        if page < 0:
            page = 0

        leftlimit = page * paginate_by

        items_in_page = paginate_by
        pagecount = int(old_div(total, paginate_by))
        if int(pagecount) == int(page):
            items_in_page = total % paginate_by

        rightlimit = leftlimit + items_in_page

        current_page = page + 1

        if total % paginate_by > 0:
            pagecount = pagecount + 1

        over_limit = limit is not None and current_page > limit

        if over_limit or pagecount == 1:
            page_links = []
        else:
            if page != 0:
                page_links = [
                    {'id': 'Previous', 'link': reverse(view_name, args=pre_args + [current_page - 1 ] + post_args)},
                    {'id': '|', 'link': None},
                ]
            else:
                page_links = [{'id': 'Previous', 'link': None}, {'id': '|', 'link': None}]
            if pagecount < (Paginator.DEF_PAGINATE_SHOW_BOUNDS * 2) + 2:
                page_links.extend([{'id': p, 'link': reverse(view_name, args=pre_args + [p] + post_args) } for p in range(1, pagecount + 1)])
            else:
                if current_page < Paginator.DEF_PAGINATE_SHOW_BOUNDS:
                    page_links.extend([{'id': p, 'link': reverse(view_name, args=pre_args + [p] + post_args) } for p in range(1, current_page + 1)])
                else:
                    page_links.extend([{'id': 1, 'link': reverse(view_name, args=pre_args + [1] + post_args) }, {'id': '...', 'link': None}])
                    page_links.extend([{'id': p, 'link': reverse(view_name, args=pre_args + [p] + post_args) } for p in range(current_page - Paginator.DEF_PAGINATE_SHOW_BOUNDS + 1, current_page + 1)])
                if pagecount - current_page < Paginator.DEF_PAGINATE_SHOW_BOUNDS + 1:
                    page_links.extend([{'id': p, 'link': reverse(view_name, args=pre_args + [p] + post_args) } for p in range(current_page + 1, pagecount + 1)])
                else:
                    if limit is None or limit > current_page:
                        page_links.extend([{'id': p, 'link': reverse(view_name, args=pre_args + [p] + post_args) } for p in range(current_page + 1, current_page + Paginator.DEF_PAGINATE_SHOW_BOUNDS + 1)])
                        page_links.extend([{'id': '...', 'link': None}])
                        if limit is None:
                            page_links.extend([{'id': pagecount, 'link': reverse(view_name, args=pre_args + [pagecount] + post_args)}])
                    else:
                        page_links.extend([ {'id': '...', 'link': None}])
            if page != pagecount - 1:
                page_links.extend([{'id': '|', 'link': None}, {'id': 'Next', 'link': reverse(view_name, args=pre_args + [current_page + 1] + post_args) }])

        return {
                'l': leftlimit,
                'r': rightlimit,
                'count': total,
                'pagecount': pagecount,
                'currentpage': current_page,
                'items_in_page': items_in_page,
                #TODO: review paging method
                'pages': page_links,
                'paginate_by': paginate_by,
            }
