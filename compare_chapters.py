import fitz
import json
import re

# 读取PDF
doc = fitz.open('2025-2026年第一学期教学日历（药物化学）.pdf')
full_text = ""
for page in doc:
    full_text += page.get_text() + "\n"

# 读取data.json
with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 按章节整理数据库药物
db_chapters = {}
for drug in data:
    ch = drug['chapter']
    if ch not in db_chapters:
        db_chapters[ch] = {'master': [], 'familiarize': []}
    db_chapters[ch][drug['type']].append(drug['cn'])

# 保存到文件
with open('comparison_report.txt', 'w', encoding='utf-8') as out:
    out.write("=" * 60 + "\n")
    out.write("详细章节对比报告\n")
    out.write("=" * 60 + "\n")
    
    # 定义章节映射
    chapter_patterns = [
        ("第五章", "第五章 镇静催眠药和抗癫痫药"),
        ("第六章", "第六章 精神神经疾病治疗药"),
        ("第七章", "第七章 神经退行性疾病治疗药物"),
        ("第八章", "第八章 镇痛药"),
        ("第九章", "第九章 非甾体抗炎药"),
        ("第十章", "第十章 拟胆碱药和抗胆碱药"),
        ("第十一章", "第十一章 抗变态反应药物"),
        ("第十二章", "第十二章 消化系统药物"),
        ("第十三章", "第十三章 降血糖药和骨质疏松治疗药"),
        ("第十四章", "第十四章 作用于肾上腺素受体的药物"),
        ("第十五章", "第十五章 抗高血压药和利尿药"),
        ("第十六章", "第十六章 心脏疾病用药物和血脂调节药"),
        ("第十七章", "第十七章 甾体激素类药物"),
        ("第十八章", "第十八章 抗生素"),
        ("第十九章", "第十九章 合成抗菌药"),
        ("第二十章", "第二十章 抗病毒药"),
        ("第二十一章", "第二十一章 抗肿瘤药物"),
    ]
    
    # 遍历每个章节
    for ch_pdf_key, ch_db_key in chapter_patterns:
        out.write(f"\n{'='*60}\n")
        out.write(f"【{ch_pdf_key}】\n")
        out.write(f"{'='*60}\n")
        
        # 从PDF提取该章节内容
        start_idx = full_text.find(ch_pdf_key)
        if start_idx == -1:
            out.write(f"PDF中未找到{ch_pdf_key}\n")
            continue
        
        # 找到下一章的开始位置
        next_ch_idx = len(full_text)
        for next_ch, _ in chapter_patterns:
            if next_ch != ch_pdf_key:
                idx = full_text.find(next_ch, start_idx + 10)
                if idx != -1 and idx < next_ch_idx:
                    next_ch_idx = idx
        
        chapter_text = full_text[start_idx:next_ch_idx]
        # 清理文本
        chapter_text = chapter_text.replace('\n', ' ').replace('\r', '')
        
        out.write(f"\n【PDF原文片段】:\n{chapter_text[:800]}...\n")
        
        # 输出数据库内容
        if ch_db_key in db_chapters:
            out.write(f"\n【数据库熟悉】: {db_chapters[ch_db_key]['familiarize']}\n")
            out.write(f"\n【数据库掌握】: {db_chapters[ch_db_key]['master']}\n")
        else:
            out.write(f"\n数据库中未找到章节: {ch_db_key}\n")

print("报告已保存到 comparison_report.txt")
