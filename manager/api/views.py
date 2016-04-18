from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import *
from api.serializers import *
from api.prometheus import *
#from api.serializers import UserSerializer
from django.http import Http404
from rest_framework import mixins
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework import permissions
from api.permissions import IsOwnerOrReadOnly
from rest_framework.reverse import reverse
from itertools import *
from django.forms.models import model_to_dict
import json
from drf_multiple_model.views import MultipleModelAPIView

# Create your views here.


@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'user': reverse('UserDetail', request=request, format=format),
        'tests': reverse('TestList', request=request, format=format),
        'test': reverse('TestDetail', request=request, format=format),
        'tests': reverse('UserList', request=request, format=format),
    })
########################################################################################

class SntUsersList(generics.ListCreateAPIView):
    queryset = monitoring_users.objects.all()
    serializer_class = SntUserSerializer

class SntUsersDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = monitoring_users.objects.all()
    serializer_class = SntUserSerializer

class SntServicesPerUserList(generics.ListAPIView):
    #queryset = monitoring_services.objects.all().filter(self.kwargs['usrID'])
    serializer_class = SntServicesFullSerializer

    def get_queryset(self):
        queryset = monitoring_services.objects.all()
        userid  = self.kwargs['usrID']
        return queryset.filter(user=userid)

class SntServicesList(generics.ListCreateAPIView):
    queryset = monitoring_services.objects.all()
    serializer_class = SntServicesSerializer

class SntFunctionsPerServiceList(generics.ListAPIView):
    #queryset = monitoring_functions.objects.all()
    serializer_class = SntFunctionsFullSerializer

    def get_queryset(self):
        queryset = monitoring_functions.objects.all()
        srvid  = self.kwargs['srvID']
        return queryset.filter(service__sonata_srv_id=srvid)

class SntServicesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = monitoring_services.objects.all()
    serializer_class = SntServicesSerializer

class SntFunctionsList(generics.ListCreateAPIView):
    queryset = monitoring_functions.objects.all()
    serializer_class = SntFunctionsSerializer

class SntFunctionsDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = monitoring_functions.objects.all()
    serializer_class = SntFunctionsSerializer

class SntNotifTypesList(generics.ListCreateAPIView):
    queryset = monitoring_notif_types.objects.all()
    serializer_class = SntNotifTypeSerializer

class SntNotifTypesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = monitoring_notif_types.objects.all()
    serializer_class = SntNotifTypeSerializer

class SntMetricsList(generics.ListCreateAPIView):
    queryset = monitoring_metrics.objects.all()
    serializer_class = SntMetricsSerializer

class SntMetricsPerFunctionList(generics.ListAPIView):
    #queryset = monitoring_metrics.objects.all()
    serializer_class = SntMetricsFullSerializer

    def get_queryset(self):
        queryset = monitoring_metrics.objects.all()
        functionid  = self.kwargs['funcID']
        result_list = list(chain(monitoring_services.objects.all(), monitoring_functions.objects.all(), monitoring_metrics.objects.all()))
        return queryset.filter(function__sonata_func_id=functionid)

class SntMetricsPerFunctionList1(generics.ListAPIView):
    #queryset = monitoring_metrics.objects.all()
    def list(self, request, *args, **kwargs):
        
        functionid  = kwargs['funcID']
        queryset = monitoring_metrics.objects.all().filter(function_id=functionid)
        dictionaries = [ obj.as_dict() for obj in queryset ]
        response = {}
        response['data_server_url']='http://sp.int.sonata-nfv.eu:9091'
        response['metrics'] = dictionaries
        return Response(response)

class SntNewServiceConf(generics.CreateAPIView):
    serializer_class = NewServiceSerializer
    def post(self, request, *args, **kwargs):
        service = request.data['service']
        functions = request.data['functions']
        rules = request.data['rules']
        u = monitoring_users.objects.all().filter(sonata_userid=service['sonata_usr_id'])
        if u.count() == 0:
            #add new user
            usr = monitoring_users(sonata_userid=service['sonata_usr_id'])
            usr.save()
            print 'New user added'
        else:
            usr = u[0]
        print usr
        #print json.dumps(service)
        #s = monitoring_services(sonata_srv_id=service['sonata_srv_id'], name=service['name'], description=service['description'], host_id=service['host_id'])
        
        s = monitoring_services.objects.all().filter(sonata_srv_id=service['sonata_srv_id'])
        if s.count() > 0:
            s.delete()    
        srv = monitoring_services(sonata_srv_id=service['sonata_srv_id'], name=service['name'], description=service['description'], host_id=service['host_id'], user=usr)
        srv.save()
        print srv
        #m = monitoring_functions.objects.all().filter(service=srv)
        #if m.count() > 0:
        #    m.delete()
         #   print 'Functions Cleared'
        for f in functions:
            func = monitoring_functions(service=srv ,host_id=f['host_id'] ,name=f['name'] , sonata_func_id=f['sonata_func_id'] , description=f['description'])
            func.save()
            for m in f['metrics']:
                metric = monitoring_metrics(function=func ,name=m['name'] ,cmd=m['cmd'] ,threshold=m['threshold'] ,interval=m['interval'] ,description=m['description'])
                metric.save()

        for r in rules:
            print json.dumps(r)
            nt = monitoring_notif_types.objects.all().filter(id=r['notification_type'])
            if nt.count() == 0:
                return Response({'error':'Alert notification type does not supported. Action Aborted'}, status=status.HTTP_400_BAD_REQUEST)
                srv.delete()
            else:
                rule = monitoring_rules(service=srv, summary=r['summary'] ,notification_type=nt[0], name=r['name'] ,condition=r['condition'] ,duration=r['duration'] ,description=r['description'] )
                rule.save()

        if len(rules) > 0:
            rf = RuleFile(service['sonata_srv_id'],rules) 
            rf.writeFile();
        return Response({'status':"success"})

class SntMetricsDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = monitoring_metrics.objects.all()
    serializer_class = SntMetricsSerializer

class SntRulesList(generics.ListCreateAPIView):
    queryset = monitoring_rules.objects.all()
    serializer_class = SntRulesSerializer

class SntRulesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = monitoring_rules.objects.all()
    serializer_class = SntRulesSerializer

class SntPromMetricList(generics.RetrieveAPIView):
    serializer_class = promMetricsListSerializer
    def get(self, request, *args, **kwargs):
        mt = ProData('prometheus',9090)
        data = mt.getMetrics()
        response = {}
        response['metrics'] = data['data']
        print response
        return Response(response)

class SntPromMetricData(generics.CreateAPIView):
    serializer_class = SntPromMetricSerializer
    '''
    {
    "name": "up",
    "start": "2016-02-28T20:10:30.786Z",
    "end": "2016-03-03T20:11:00.781Z",
    "step": "1h",
    "labels": [{"labeltag":"instance", "labelid":"192.168.1.39:9090"},{"labeltag":"group", "labelid":"development"}]
    }
    '''
    def post(self, request, *args, **kwargs):
        mt = ProData('prometheus',9090)
        data = mt.getTimeRangeData(request.data)
        response = {}
        #print data
        try:
            response['metrics'] = data['data']
        except KeyError:
            response = data
        return Response(response)
'''
class SntServiceConfList(generics.ListCreateAPIView):
    serializer_class = SntServiceConfSerializer

    def get_queryset(self):
        #queryset = monitoring_users.objects.all()
        return list(itertools.chain(monitoring_services.objects.all(), monitoring_services.objects.all()))

'''
########################################################################################3
"""
class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class TestList(generics.ListCreateAPIView):
    #permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = test_tb.objects.all()
    serializer_class = TestTBSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TestDetail(generics.RetrieveUpdateDestroyAPIView):
    #permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly,)
    queryset = test_tb.objects.all()
    serializer_class = TestTBSerializer



class TestList(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = test_tb.objects.all()
    serializer_class = TestTBSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class TestDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = test_tb.objects.all()
    serializer_class = TestTBSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class TestList(APIView):
    
    //List all snippets, or create a new snippet.
    
    def get(self, request, format=None):
        snippets = test_tb.objects.all()
        serializer = TestTBSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = TestTBSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TestDetail(APIView):
    
    //Retrieve, update or delete a snippet instance.
    
    def get_object(self, pk):
        try:
            return test_tb.objects.get(pk=pk)
        except test_tb.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = TestTBSerializer(snippet)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = TestTBSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        snippet = self.get_object(pk)
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def test_list(request, format=None):

    if request.method == 'GET':
        snippets = test_tb.objects.all()
        serializer = TestTBSerializer(snippets, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = TestTBSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
       	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def test_detail(request, pk, format=None):

    try:
       	snippet = test_tb.objects.get(pk=pk)
    except test_tb.DoesNotExist:
       	return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
       	serializer = TestTBSerializer(snippet)
       	return Response(serializer.data)

    elif request.method == 'PUT':
       	serializer = TestTBSerializer(snippet, data=request.data)
       	if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
       	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        snippet.delete()
       	return Response(status=status.HTTP_204_NO_CONTENT)

"""

