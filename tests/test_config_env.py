import os
import sys

# Ensure we can import from core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import get_llm_config

def test_config_priority():
    print("正在测试配置优先级...")
    
    # CASE 1: Env vars set
    # 我们设置 Provider 为 gemini，这样 get_llm_config 才会去读 GEMINI_API_KEY
    os.environ["LLM_PROVIDER"] = "gemini"
    os.environ["GEMINI_API_KEY"] = "env_key"
    os.environ["LLM_MODEL"] = "env_model"
    os.environ["LLM_BASE_URL"] = "env_url"
    
    config = {
        "provider": "file_provider",
        "api_key": "file_key",
        "model_name": "file_model",
        "base_url": "file_url"
    }
    
    res = get_llm_config(config)
    
    assert res["provider"] == "gemini", f"预期 gemini, 实际得到 {res['provider']}"
    assert res["api_key"] == "env_key", f"预期 env_key, 实际得到 {res['api_key']}"
    assert res["model_name"] == "env_model", f"预期 env_model, 实际得到 {res['model_name']}"
    assert res["base_url"] == "env_url", f"预期 env_url, 实际得到 {res['base_url']}"
    print("✅ 测试用例 1: 环境变量优先级测试通过")
    
    # CASE 2: No Env vars, fallback to config
    del os.environ["LLM_PROVIDER"]
    del os.environ["GEMINI_API_KEY"]
    del os.environ["LLM_MODEL"]
    del os.environ["LLM_BASE_URL"]
    
    res = get_llm_config(config)
    assert res["provider"] == "file_provider", f"预期 file_provider, 实际得到 {res['provider']}"
    assert res["api_key"] == "file_key", f"预期 file_key, 实际得到 {res['api_key']}"
    assert res["model_name"] == "file_model", f"预期 file_model, 实际得到 {res['model_name']}"
    assert res["base_url"] == "file_url", f"预期 file_url, 实际得到 {res['base_url']}"
    print("✅ 测试用例 2: 配置文件回退测试通过")
    
    # CASE 3: No Defaults (Strict Mode)
    # User requested NO default models. So if we pass empty config and no env vars, model should be None.
    res = get_llm_config({})
    assert res["provider"] == "gemini", f"预期默认 provider 为 gemini, 实际得到 {res['provider']}"
    assert res["model_name"] is None, f"预期 model_name 为 None (禁止默认值), 实际得到 {res['model_name']}"
    print("✅ 测试用例 3: 无默认值模式测试通过 (严格模式)")

if __name__ == "__main__":
    try:
        test_config_priority()
        print("\n🎉 所有测试通过！")
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生意外错误: {e}")
        sys.exit(1)
