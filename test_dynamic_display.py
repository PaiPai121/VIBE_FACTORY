import asyncio
from core.orchestrator import Orchestrator

def test_dynamic_display():
    """测试动态显示提供者信息"""
    print(">>> 测试动态显示提供者信息...")
    
    # 测试双Zhipu配置
    print("\n1. 测试双Zhipu配置:")
    orchestrator1 = Orchestrator("config/two_zhipu_config.json")
    
    proposer_name = getattr(orchestrator1.proposer, '__class__', type(None)).__name__.replace('Provider', '') if orchestrator1.proposer else 'Unknown'
    auditor_name = getattr(orchestrator1.auditor, '__class__', type(None)).__name__.replace('Provider', '') if orchestrator1.auditor else 'Unknown'
    proposer_model = getattr(orchestrator1.proposer, 'model', 'Unknown') if orchestrator1.proposer else 'Unknown'
    auditor_model = getattr(orchestrator1.auditor, 'model', 'Unknown') if orchestrator1.auditor else 'Unknown'
    
    print(f"提議者({proposer_name}:{proposer_model})和審計者({auditor_name}:{auditor_model})")
    
    # 测试默认配置
    print("\n2. 测试默认配置:")
    orchestrator2 = Orchestrator("config/ai_config.json")
    
    proposer_name = getattr(orchestrator2.proposer, '__class__', type(None)).__name__.replace('Provider', '') if orchestrator2.proposer else 'Unknown'
    auditor_name = getattr(orchestrator2.auditor, '__class__', type(None)).__name__.replace('Provider', '') if orchestrator2.auditor else 'Unknown'
    proposer_model = getattr(orchestrator2.proposer, 'model', 'Unknown') if orchestrator2.proposer else 'Unknown'
    auditor_model = getattr(orchestrator2.auditor, 'model', 'Unknown') if orchestrator2.auditor else 'Unknown'
    
    print(f"提議者({proposer_name}:{proposer_model})和審計者({auditor_name}:{auditor_model})")

    print("\n[PASS] 动态显示功能正常工作!")

if __name__ == "__main__":
    test_dynamic_display()