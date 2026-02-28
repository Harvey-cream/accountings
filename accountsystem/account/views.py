from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TransactionIcon

class GetIconsView(APIView):
    """获取所有图标列表"""
    def get(self, request, format=None):
        # 按照 group 分组或者直接全部返回
        icons = TransactionIcon.objects.all().values('id', 'name', 'icon', 'group', 'type')
        
        # 转换为列表
        icon_list = list(icons)
        
        return Response({
            'code': 200,
            'message': 'success',
            'data': icon_list
        }, status=status.HTTP_200_OK)
