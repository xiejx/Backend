import json

from django.shortcuts import HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.db import transaction

from manager_app import models
from user_app import models as tmp    # optimization: message queue
from manager_app.utils.mgr_auth import SALT
from manager_app.utils.mgr_auth import authenticate
from manager_app.utils.method_test import is_post
from manager_app.utils.method_test import is_get
from manager_app.utils.db_to_dict import process_mgr_obj
from manager_app.utils.db_to_dict import process_record_obj

# Create your views here.


def login(request):
    """
    :param request:
    request.POST.get('username')
    request.POST.get('password')
    :return:
    HttpResponse(json.dumps(result))
    """
    result = {
        'status': '',  # 'success' or 'failure'
        'error_msg': '',  # notes of failure
    }

    # handle wrong method
    if not is_post(request, result):
        return HttpResponse(json.dumps(result))

    username = request.POST.get('username')
    password = request.POST.get('password')

    mgr = models.ManagerInfo.objects.filter(
        username=username,
        password=password,
    )

    if mgr.count() == 1:
        result['status'] = 'success'
        response = HttpResponse(json.dumps(result))
        response.set_signed_cookie(key='username', value=username, salt=SALT)
        return response
    else:
        result['status'] = 'failure'
        result['error_msg'] = 'this user does not exist, or the password is wrong'
        return HttpResponse(json.dumps(result))


@authenticate
def logout(request):
    """
    :param request:
    :return:
    HttpResponse(json.dumps(result))
    """
    result = {
        'status': '',  # 'success' or 'failure'
        'error_msg': '',  # notes of failure
    }

    # handle wrong method
    if not is_post(request, result):
        return HttpResponse(json.dumps(result))

    result['status'] = 'success'
    response = HttpResponse(json.dumps(result))
    response.delete_cookie(key='username')

    return response


@authenticate
def manager_info(request):
    """
    :param request:
    :return:
    HttpResponse(json.dumps(result))
    """
    result = {
        'status': '',  # 'success' or 'failure'
        'msg': '',
        'error_msg': '',  # notes of failure
    }

    # handle wrong method
    if not is_get(request, result):
        return HttpResponse(json.dumps(result))

    username = request.get_signed_cookie(key='username', salt=SALT)
    mgr = models.ManagerInfo.objects.filter(username=username).first()

    if mgr:
        result['status'] = 'success'
        mgr_dict = process_mgr_obj(mgr)
        result['msg'] = json.dumps(mgr_dict)
    else:
        result['status'] = 'failure'
        result['error_msg'] = 'mgr db info may be deleted'

    return HttpResponse(json.dumps(result))


class ReportInfoBox(View):
    @method_decorator(authenticate)
    def dispatch(self, request, *args, **kwargs):
        return super(ReportInfoBox, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def get(request):
        """
        :param request:
        :return:
        HttpResponse(json.dumps(result))
        """
        result = {
            'status': '',  # 'success' or 'failure'
            'msg': '',
            'error_msg': '',  # notes of failure
        }

        reports = tmp.AttitudeRecord.objects.filter(attitude=2)
        report_dict = dict()
        for i in range(reports.count()):
            report_reason = str(reports[i].report_reason)
            cid = str(reports[i].cid.id)

            # add an item for a new comment
            if cid not in report_dict.keys():
                # detail report reason info is in db
                report_dict[cid] = {
                    'content': reports[i].cid.content,
                    'report_reasons': {
                        '0': '0',
                        '1': '0',
                        '2': '0',
                        '3': '0',
                        '4': '0',
                        '5': '0',
                        '6': '0',
                        '7': '0',
                        '8': '0',
                    },
                }

            # keep using str
            report_dict[cid]['report_reasons'][report_reason] = \
                str(int(report_dict[cid]['report_reasons'][report_reason]) + 1)

        # stringify data
        for key in report_dict.keys():
            report_dict[key]['report_reasons'] = \
                json.dumps(report_dict[key]['report_reasons'])
            report_dict[key] = json.dumps(report_dict[key])
        result['msg'] = json.dumps(report_dict)
        result['status'] = 'success'

        return HttpResponse(json.dumps(result))

    @staticmethod
    def post(request):
        """
        :param request:
        request.POST.get('protocol'): '0' means delete comment,
                                    '1' means delete related report
        request.POST.get('cid'): target comment id
        :return:
        HttpResponse(json.dumps(result))
        """
        result = {
            'status': '',  # 'success' or 'failure'
            'error_msg': '',  # notes of failure
        }

        protocol = request.POST.get('protocol')
        if protocol is None:
            result['status'] = 'failure'
            result['error_msg'] = 'protocol required'

        cid = request.POST.get('cid')
        if cid is None:
            result['status'] = 'failure'
            result['error_msg'] = 'cid (comment id) required'

        if protocol == '0':
            # delete comment
            tmp.Comment.objects.filter(id=cid).delete()
            result['status'] = 'success'
        elif protocol == '1':
            # delete related reports
            tmp.AttitudeRecord.objects.filter(cid=cid).delete()
            result['status'] = 'success'
        else:
            result['status'] = 'failure'
            result['error_msg'] = 'invalid protocol'

        return HttpResponse(json.dumps(result))


class InventoryManagement(View):
    @method_decorator(authenticate)
    def dispatch(self, request, *args, **kwargs):
        return super(InventoryManagement, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def get(request):
        pass

    @staticmethod
    def post(request):
        pass


class Debit(View):
    @method_decorator(authenticate)
    def dispatch(self, request, *args, **kwargs):
        return super(Debit, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def get(request):
        """get user's order record
        :param request:
        request.GET.get('username')
        :return:
        HttpResponse(json.dumps(result))
        """
        result = {
            'status': '',  # 'success' or 'failure'
            'msg': '',  # the selected user's all debit record
            'error_msg': '',  # notes of failure
        }

        # ensure request contains 'username'
        username = request.GET.get('username')
        if username is None:
            result['status'] = 'failure'
            result['error_msg'] = 'username required'
            return HttpResponse(json.dumps(result))

        # ensure related user is in db
        user = tmp.UserInfo.objects.filter(user__username=username).first()
        if user is None:
            result['status'] = 'failure'
            result['error_msg'] = 'related user not exists'
            return HttpResponse(json.dumps(result))

        # process data
        records = tmp.ActiveRecord.objects.filter(uid=user.id).filter(active=0)
        record_dict = {}
        for i in range(records.count()):
            record = process_record_obj(records[i])
            record_dict[str(records[i].id)] = json.dumps(record)
        result['msg'] = json.dumps(record_dict)
        result['status'] = 'success'

        return HttpResponse(json.dumps(result))

    @staticmethod
    def post(request):
        """
        :param request:
        request.POST.get('msg')
        :return:
        HttpResponse(json.dumps(result))
        """
        result = {
            'status': '',  # 'success' or 'failure'
            'error_msg': '',  # notes of failure
        }

        # ensure request contains 'msg'
        msg = request.POST.get('msg')
        if msg is None:
            result['status'] = 'failure'
            result['error_msg'] = 'msg (debit message) required'
            return HttpResponse(json.dumps(result))

        msg = json.loads(msg)

        # ensure msg contains 'username' and 'bid'
        if 'username' not in msg.keys() or 'bid' not in msg.keys():
            result['status'] = 'failure'
            result['error_msg'] = 'msg must contain username and bid'
            return HttpResponse(json.dumps(result))

        # ensure user exists
        user = tmp.UserInfo.objects.filter(user__username=msg['username']).first()
        if user is None:
            result['status'] = 'failure'
            result['error_msg'] = 'related user not exists'
            return HttpResponse(json.dumps(result))

        # ensure book exists
        book = tmp.BookInfo.objects.filter(id=int(msg['bid'])).first()
        if book is None:
            result['status'] = 'failure'
            result['error_msg'] = 'the desired book not exists'
            return HttpResponse(json.dumps(result))

        # start a transaction
        with transaction.atomic():
            # get the book instance
            book_instance = book.book_instances.filter(state=0).first()
            if book_instance is None:
                result['status'] = 'failure'
                result['error_msg'] = 'inadequate inventory'
                return HttpResponse(json.dumps(result))
            book_instance.state = 2
            book_instance.save()

            # record debit
            tmp.ActiveRecord.objects.create(
                uid=user,
                bid=book_instance,
                active=1,
            )
        result['status'] = 'success'

        return HttpResponse(json.dumps(result))


class Return(View):
    @method_decorator(authenticate)
    def dispatch(self, request, *args, **kwargs):
        return super(Return, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def get(request):
        """get user's debit record
        :param request:
        request.GET.get('username')
        :return:
        HttpResponse(json.dumps(result))
        """
        result = {
            'status': '',  # 'success' or 'failure'
            'msg': '',    # the selected user's all debit record
            'error_msg': '',  # notes of failure
        }

        # ensure request contains 'username'
        username = request.GET.get('username')
        if username is None:
            result['status'] = 'failure'
            result['error_msg'] = 'username required'
            return HttpResponse(json.dumps(result))

        # ensure related user is in db
        user = tmp.UserInfo.objects.filter(user__username=username).first()
        if user is None:
            result['status'] = 'failure'
            result['error_msg'] = 'related user not exists'
            return HttpResponse(json.dumps(result))

        # process data
        records = tmp.ActiveRecord.objects.filter(uid=user.id).filter(active=1)
        record_dict = {}
        for i in range(records.count()):
            record = process_record_obj(records[i])
            record_dict[str(records[i].id)] = json.dumps(record)
        result['msg'] = json.dumps(record_dict)
        result['status'] = 'success'

        return HttpResponse(json.dumps(result))

    @staticmethod
    def post(request):
        """
        :param request:
        request.POST.get('rid'):
        :return:
        HttpResponse(json.dumps(result))
        """
        result = {
            'status': '',  # 'success' or 'failure'
            'error_msg': '',  # notes of failure
        }

        # ensure request contains 'rid'
        rid = request.POST.get('rid')
        if rid is None:
            result['status'] = 'failure'
            result['error_msg'] = 'rid (record id) required'
            return HttpResponse(json.dumps(result))
        rid = int(rid)

        # ensure related active record is in db
        record = tmp.ActiveRecord.objects.filter(id=rid).first()
        if record is None:
            result['status'] = 'failure'
            result['error_msg'] = 'related active record not exists'
            return HttpResponse(json.dumps(result))

        # add return record
        tmp.ActiveRecord.objects.create(
            uid=record.uid,
            bid=record.bid,
            active=2,
        )

        # change related book instance's state into common
        record.bid.state = 0
        record.bid.save()

        # delete target active record
        tmp.ActiveRecord.objects.filter(id=rid).delete()
        result['status'] = 'success'

        return HttpResponse(json.dumps(result))

