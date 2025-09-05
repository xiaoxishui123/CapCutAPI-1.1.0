#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder='templates')

def test_template_rendering():
    """测试模板渲染功能"""
    try:
        print("开始测试模板渲染...")
        
        # 测试数据
        test_materials = [
            {
                'type': 'video',
                'url': 'test_video.mp4',
                'start': 0,
                'duration': 10,
                'name': '测试视频'
            },
            {
                'type': 'audio', 
                'url': 'test_audio.mp3',
                'start': 5,
                'duration': 8,
                'name': '测试音频'
            }
        ]
        
        timeline_html = '''
        <div class="multitrack-timeline">
            <div class="timeline-header">
                <div class="timeline-ruler">
                    <div class="ruler-mark">0:00</div>
                </div>
            </div>
            <div class="timeline-tracks">
                <div class="timeline-track" data-track-type="video">
                    <div class="track-label">视频轨道</div>
                    <div class="track-items">
                        <div class="timeline-block">测试视频</div>
                    </div>
                </div>
            </div>
        </div>
        '''
        
        # 添加draft_info数据
        draft_info = {
            'create_time': '2024-01-01 12:00:00',
            'update_time': '2024-01-01 12:30:00'
        }
        
        with app.app_context():
            result = render_template('preview.html', 
                                   draft_id='test_draft',
                                   materials=test_materials,
                                   total_duration=18.0,
                                   timeline_html=timeline_html,
                                   draft_info=draft_info)
            
            print(f"✅ 模板渲染成功！生成了 {len(result)} 个字符的HTML")
            print(f"HTML内容预览: {result[:200]}...")
            
            # 检查是否包含timeline内容
            if 'timeline' in result.lower():
                print("✅ HTML中包含timeline内容")
            else:
                print("❌ HTML中不包含timeline内容")
                
            return True
            
    except Exception as e:
        print(f"❌ 模板渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_template_rendering()
    sys.exit(0 if success else 1)