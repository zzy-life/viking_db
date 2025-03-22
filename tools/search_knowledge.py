from collections.abc import Generator
from typing import Any, Optional
import json

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from volcengine.viking_knowledgebase import VikingKnowledgeBaseService


class SearchKnowledgeTool(Tool):
    def _serialize_response(self, obj):
        """递归地将复杂对象转换为可序列化的字典"""
        if hasattr(obj, '__dict__'):
            # 对于Point类等对象，转换为字典
            return {k: self._serialize_response(v) for k, v in obj.__dict__.items() 
                    if not k.startswith('_')}  # 跳过私有属性
        elif isinstance(obj, list):
            # 处理列表
            return [self._serialize_response(item) for item in obj]
        elif isinstance(obj, dict):
            # 处理字典
            return {k: self._serialize_response(v) for k, v in obj.items()}
        else:
            # 基本类型直接返回
            return obj

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        # 从参数中获取凭证和设置
        host = tool_parameters.get("host")
        ak = tool_parameters.get("ak")
        sk = tool_parameters.get("sk")
        
        # 基本参数验证
        if not host or not ak or not sk:
            yield self.create_text_message("错误：需要提供Host、Access Key和Secret Key")
            return
            
        # 从参数中获取查询
        query = tool_parameters.get("query")
        if not query:
            yield self.create_text_message("错误：需要提供查询内容")
            return
            
        # 获取collection_name或resource_id
        collection_name = tool_parameters.get("collection_name")
        resource_id = tool_parameters.get("resource_id")
        
        if not collection_name and not resource_id:
            yield self.create_text_message("错误：必须提供collection_name或resource_id其中之一")
            return
            
        # 获取项目信息和其他参数
        project = tool_parameters.get("project", "default")
        rerank_switch = tool_parameters.get("rerank_switch", False)
        retrieve_count = tool_parameters.get("retrieve_count", 25)
        limit = tool_parameters.get("limit", 10)
        dense_weight = tool_parameters.get("dense_weight", 0.5)
        
        # 从tool_parameters中获取doc_filter并转换
        doc_filter_str = tool_parameters.get("doc_filter")
        query_param = {}
        if doc_filter_str:
            try:
                doc_filter = json.loads(doc_filter_str)
                query_param['doc_filter'] = doc_filter
            except json.JSONDecodeError as e:
                yield self.create_text_message(f"错误：doc_filter JSON格式无效: {str(e)}")
                return
        
        try:
            # 初始化Viking Knowledge Base服务
            viking_knowledgebase_service = VikingKnowledgeBaseService(
                host=host,
                scheme="https",
                connection_timeout=300,
                socket_timeout=300
            )
            viking_knowledgebase_service.set_ak(ak)
            viking_knowledgebase_service.set_sk(sk)
            
            # 构建post_processing参数
            post_processing = {
                "rerank_switch": rerank_switch,
                "retrieve_count": retrieve_count,
            }
            
            # 构建API调用参数
            api_args = {
                "query": query,
                "query_param": query_param,
                "project": project,
                "limit": limit,
                "dense_weight": dense_weight,
                "post_processing": post_processing
            }
            
            # 根据提供的参数使用collection_name或resource_id
            if collection_name:
                api_args["collection_name"] = collection_name
            elif resource_id:
                api_args["resource_id"] = resource_id
                
            # 调用search_knowledge API
            result = viking_knowledgebase_service.search_knowledge(**api_args)
            
            # 将结果转换为可序列化的字典
            serialized_result = self._serialize_response(result)
            
            # 返回处理后的结果
            yield self.create_json_message(serialized_result)
            
        except Exception as e:
            yield self.create_text_message(f"错误: {str(e)}") 