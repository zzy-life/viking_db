from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from volcengine.viking_knowledgebase import VikingKnowledgeBaseService


class VikingDbProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            host = credentials.get("host")
            ak = credentials.get("ak")
            sk = credentials.get("sk")
            
            if not all([host, ak, sk]):
                raise ValueError("缺少必要的认证信息：host、ak、sk")
                
            # 初始化服务并尝试连接
            viking_service = VikingKnowledgeBaseService(
                host=host,
                scheme="https",
                connection_timeout=10,
                socket_timeout=10
            )
            viking_service.set_ak(ak)
            viking_service.set_sk(sk)
            
            # 可以尝试一个简单的API调用来验证凭证
            # 这里仅作示例，具体实现可能需要根据实际API调整
            viking_service.list_collections(project="default")
            
        except Exception as e:
            raise ToolProviderCredentialValidationError(f"凭证验证失败: {str(e)}")
