import sys
import os
import time
import traceback
import yaml

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from tools.config_generator import generate_config_via_ai
from core.config import load_config, get_llm_config
from core.generator import generate_outline, write_chapters_from_outline
from drivers.factory import get_driver

def run_automation_loop():
    print("🚀 启动全自动小说生成引擎...")
    FIXED_IDEA = "作恶多端的产品经理，平日专门压榨程序员，给程序员提出各种无理需求，老天爷看不下去了，把他丢到异世界，变成了一个妓女，在异世界赎罪" 
    # FIXED_IDEA = None 

    loop_count = 0
    
    while True:
        loop_count += 1
        print(f"\n\n{'='*50}")
        print(f"🔄 开始执行第 {loop_count} 轮自动生成任务")
        print(f"{'='*50}")
        
        try:
            # 1. 自动生成 Config
            if FIXED_IDEA:
                print(f"\n[Step 1] 使用固定创意生成配置: {FIXED_IDEA}")
                current_idea = FIXED_IDEA
            else:
                print("\n[Step 1] 生成随机小说配置...")
                current_idea = None
            
            # 不再传递 target_model, 依赖 config_generator 自动从 env/config 读取
            config_path = generate_config_via_ai(idea=current_idea, model_name=None, auto_save=True)
            
            if not config_path:
                print("⚠️ Config 生成失败，休息 10 秒后重试...")
                time.sleep(10)
                continue
                
            print(f"Config 已生成: {config_path}")
            
            # 2. 加载 Config
            print("\n[Step 2] 加载配置...")
            config = load_config(config_path)
            
            # Update specific generation parameters for automation
            novel_config = config.get("novel", {})
            title = novel_config.get("title", f"AutoNovel_{int(time.time())}")
            
            # 3. 初始化 LLM (使用 get_llm_config 统一获取配置)
            # 这样会优先读取 ENV 中的 LLM_MODEL, 其次 Config 中的 model_name
            llm_config = get_llm_config(config)
            
            provider = llm_config['provider']
            api_key = llm_config['api_key']
            base_url = llm_config['base_url']
            model_name = llm_config['model_name']

            print(f"当前使用的模型: {model_name}")
            llm = get_driver(provider, api_key, model_name, base_url)
            
            # 4. 生成大纲
            print(f"\n[Step 3] 生成《{title}》大纲...")
            chapter_count = config.get("novel", {}).get("chapter_count", 10)
            sections = config.get("novel", {}).get("sections_per_chapter", 2)
            meta = config.get("novel", {}).get("details", {})
            idea = config.get("novel", {}).get("idea", "No Idea")
            
            # Ensure generate_outline args match: llm, title, idea, chapter_count, sections_per_chapter, meta, novel_config
            outline = generate_outline(llm, title, idea, chapter_count, sections, meta, novel_config)
            
            if not outline:
                print("⚠️ 大纲生成失败，跳过本次循环。")
                continue
                
            # 5. 生成正文
            print(f"\n[Step 4] 开始撰写《{title}》正文...")
            words_per_section = config.get("novel", {}).get("words_per_section", 2000)
            
            write_chapters_from_outline(llm, title, outline, meta, words_per_section)
            
            print(f"\n✅ 《{title}》生成流程结束！")
            
        except Exception as e:
            print(f"\n❌ 本轮自动生成发生严重错误: {e}")
            traceback.print_exc()
        
        print("\n⏳ 休息 10 秒后开始下一轮...")
        time.sleep(10)

if __name__ == "__main__":
    try:
        run_automation_loop()
    except KeyboardInterrupt:
        print("\n程序已手动停止。")
