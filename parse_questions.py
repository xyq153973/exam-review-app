#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题库解析脚本 - 将markdown格式题库转换为JSON
"""

import json
import re
import os

def parse_question_file(filepath, source_name):
    """解析题库文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    questions = []
    
    # 按题目分割 - 使用答案作为分隔标记
    # 题目格式：数字．题目内容 \n A．选项 \n B．选项 \n C．选项 \n D．选项 \n 答案：X
    lines = content.split('\n')
    
    current_question = None
    current_options = {}
    current_content_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 检测题目开始 - 数字．开头
        question_match = re.match(r'^(\d+)．(.+)', line)
        if question_match and not line.startswith('A．') and not line.startswith('B．') and not line.startswith('C．') and not line.startswith('D．'):
            # 保存上一题
            if current_question and current_options:
                questions.append(finalize_question(current_question, current_options, current_content_lines, source_name))
            
            # 开始新题
            current_question = {
                'id': None,
                'content': question_match.group(2),
                'options': {},
                'answer': None,
                'knowledge': None,
                'category': None,
                'difficulty': None,
                'question_id': None
            }
            current_options = {}
            current_content_lines = []
            i += 1
            continue
        
        # 检测选项
        option_match = re.match(r'^([A-D])．(.+)', line)
        if option_match and current_question:
            option_key = option_match.group(1)
            option_text = option_match.group(2)
            # 处理多行选项
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if re.match(r'^[A-D]．', next_line) or next_line.startswith('答案') or next_line.startswith('知识点'):
                    break
                if next_line and not next_line.startswith('试题'):
                    option_text += ' ' + next_line
                j += 1
            current_options[option_key] = option_text.strip()
            i = j
            continue
        
        # 检测答案
        answer_match = re.match(r'^答案[：:]\s*([A-D])', line)
        if answer_match and current_question:
            current_question['answer'] = answer_match.group(1)
            i += 1
            continue
        
        # 检测知识点
        knowledge_match = re.match(r'^知识点[：:]\s*(.+)', line)
        if knowledge_match and current_question:
            current_question['knowledge'] = knowledge_match.group(1).strip()
            i += 1
            continue
        
        # 检测试题分类
        category_match = re.match(r'^试题分类[：:]\s*(.+)', line)
        if category_match and current_question:
            current_question['category'] = category_match.group(1).strip()
            i += 1
            continue
        
        # 检测难度
        difficulty_match = re.match(r'^难度[：:]\s*(.+)', line)
        if difficulty_match and current_question:
            current_question['difficulty'] = difficulty_match.group(1).strip()
            i += 1
            continue
        
        # 检测试题编号
        qid_match = re.match(r'^试题编号[：:]\s*(.+)', line)
        if qid_match and current_question:
            current_question['question_id'] = qid_match.group(1).strip()
            i += 1
            continue
        
        # 题目内容的多行文本
        if current_question and line and not line.startswith('试题') and not line.startswith('答案') and not line.startswith('知识点') and not line.startswith('难度'):
            if not re.match(r'^[A-D]．', line):
                current_content_lines.append(line)
        
        i += 1
    
    # 保存最后一题
    if current_question and current_options:
        questions.append(finalize_question(current_question, current_options, current_content_lines, source_name))
    
    return questions

def finalize_question(q, options, content_lines, source_name):
    """完成题目构建"""
    # 合并多行题目内容
    full_content = q['content']
    if content_lines:
        full_content = full_content + ' ' + ' '.join(content_lines)
    
    # 清理选项文本中的英文翻译（题库2有中英双语）
    cleaned_options = {}
    for key, text in options.items():
        # 移除英文翻译部分
        if '\\\n' in text:
            text = text.split('\\\n')[0]
        # 移除纯英文行
        lines = text.split('\n')
        chinese_lines = []
        for line in lines:
            # 如果一行主要是英文（超过70%是英文字符），跳过
            if line.strip():
                english_chars = len(re.findall(r'[a-zA-Z]', line))
                total_chars = len(re.findall(r'[\u4e00-\u9fff a-zA-Z]', line))
                if total_chars > 0 and english_chars / total_chars > 0.7:
                    continue
                chinese_lines.append(line)
        cleaned_options[key] = ' '.join(chinese_lines).strip()
    
    return {
        'id': q['question_id'] or f"{source_name}_{len(options)}",
        'content': full_content.strip(),
        'options': cleaned_options,
        'answer': q['answer'],
        'knowledge': q['knowledge'],
        'category': q['category'] or '通用类',
        'difficulty': q['difficulty'] or '适中',
        'source': source_name
    }

def main():
    # 解析题库1
    print("解析题库1...")
    q1 = parse_question_file('/tmp/tiku1.md', '通用题库')
    print(f"题库1解析完成，共 {len(q1)} 题")
    
    # 解析题库2
    print("解析题库2...")
    q2 = parse_question_file('/tmp/tiku2.md', '科创板题库')
    print(f"题库2解析完成，共 {len(q2)} 题")
    
    # 合并题库
    all_questions = q1 + q2
    print(f"总计 {len(all_questions)} 题")
    
    # 提取知识点列表
    knowledge_points = set()
    for q in all_questions:
        if q['knowledge']:
            # 提取知识点层级
            parts = q['knowledge'].split('/')
            for part in parts:
                knowledge_points.add(part.strip())
    
    print(f"知识点数量: {len(knowledge_points)}")
    
    # 保存JSON
    output = {
        'questions': all_questions,
        'knowledgePoints': sorted(list(knowledge_points)),
        'stats': {
            'total': len(all_questions),
            'tiku1': len(q1),
            'tiku2': len(q2)
        }
    }
    
    output_path = '/Users/icelyn/.qianfan/workspace/98c0878449ff4f33a2e4b42e0c9535a8/exam-app/questions.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"题库已保存到: {output_path}")

if __name__ == '__main__':
    main()
