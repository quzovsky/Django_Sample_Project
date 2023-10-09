from rest_framework import status, generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView

from accounts.permissions import IsCharityOwner, IsBenefactor
from charities.models import Task, Benefactor
from charities.serializers import (
    TaskSerializer, CharitySerializer, BenefactorSerializer
)


class BenefactorRegistration(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BenefactorSerializer
    def perform_create(self, serializer):
        benefactor = serializer.save(user=self.request.user)



class CharityRegistration(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CharitySerializer
    def perform_create(self, serializer):
        charity = serializer.save(user=self.request.user)


class Tasks(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.all_related_tasks_to_user(self.request.user)

    def post(self, request, *args, **kwargs):
        data = {
            **request.data,
            "charity_id": request.user.charity.id
        }
        serializer = self.serializer_class(data = data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            self.permission_classes = [IsAuthenticated, ]
        else:
            self.permission_classes = [IsCharityOwner, ]

        return [permission() for permission in self.permission_classes]

    def filter_queryset(self, queryset):
        filter_lookups = {}
        for name, value in Task.filtering_lookups:
            param = self.request.GET.get(value)
            if param:
                filter_lookups[name] = param
        exclude_lookups = {}
        for name, value in Task.excluding_lookups:
            param = self.request.GET.get(value)
            if param:
                exclude_lookups[name] = param

        return queryset.filter(**filter_lookups).exclude(**exclude_lookups)


class TaskRequest(APIView):
    permission_classes= (IsBenefactor,)
    def get(self,request,task_id):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if task.state != Task.TaskStatus.PENDING:
            data={'detail': 'This task is not pending.'}
            return Response(data=data,status=status.HTTP_404_NOT_FOUND)
        else:
            task.assign_to_benefactor(Benefactor.objects.get(user=request.user))
            data={'detail': 'Request sent.'}
            return Response(data=data,status=status.HTTP_200_OK)
        


class TaskResponse(APIView):
    pass


class DoneTask(APIView):
    pass