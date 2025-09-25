#!/usr/bin/env python3
"""
BGM排序功能验证测试脚本
用于验证修复后的BGM智能排序功能是否正常工作
"""

import json
import logging
import sys
import traceback
from typing import List, Dict, Any, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def safe_bgm_ranking(bgm_input: Union[List, Dict, str, None]) -> List[Dict]:
    """
    安全的BGM排序函数 - 修复rank属性设置错误
    
    Args:
        bgm_input: BGM输入数据，可能是列表、字典、字符串或None
        
    Returns:
        List[Dict]: 排序后的BGM列表，每个BGM都有rank属性
    """
    try:
        logger.info(f"开始BGM安全排序，输入类型: {type(bgm_input)}")
        
        # 第一步：输入验证和标准化
        bgm_list = []
        
        if bgm_input is None:
            logger.warning("BGM输入为None，返回空列表")
            return []
        
        # 处理字符串输入（JSON格式）
        if isinstance(bgm_input, str):
            try:
                bgm_input = json.loads(bgm_input)
            except json.JSONDecodeError:
                logger.error("BGM输入字符串不是有效的JSON格式")
                return []
        
        # 处理字典输入
        if isinstance(bgm_input, dict):
            # 如果是空字典，返回空列表
            if not bgm_input:
                logger.warning("BGM输入为空字典，返回空列表")
                return []
            
            # 尝试从字典中提取BGM列表
            for key in ['bgm_candidates', 'bgm_list', 'items', 'data', 'results']:
                if key in bgm_input and isinstance(bgm_input[key], list):
                    bgm_list = bgm_input[key]
                    break
            else:
                # 如果没找到列表，将字典本身作为单个BGM
                bgm_list = [bgm_input]
        
        # 处理列表输入
        elif isinstance(bgm_input, list):
            bgm_list = bgm_input
        
        else:
            logger.error(f"不支持的BGM输入类型: {type(bgm_input)}")
            return []
        
        # 第二步：验证和清理BGM列表
        safe_bgm_list = []
        for i, bgm in enumerate(bgm_list):
            try:
                # 确保BGM是字典类型
                if not isinstance(bgm, dict):
                    logger.warning(f"BGM项 {i} 不是字典类型，跳过: {type(bgm)}")
                    continue
                
                # 创建安全的BGM副本
                safe_bgm = {}
                
                # 复制所有属性
                for key, value in bgm.items():
                    safe_bgm[key] = value
                
                # 确保必要的属性存在
                safe_bgm.setdefault("score", 0.0)
                safe_bgm.setdefault("weight", 1.0)
                safe_bgm.setdefault("bpm", 120)
                safe_bgm.setdefault("duration", 30)
                safe_bgm.setdefault("title", f"BGM_{i+1}")
                safe_bgm.setdefault("id", f"bgm_{i+1}")
                
                # 类型转换和验证
                try:
                    safe_bgm["score"] = float(safe_bgm["score"])
                    safe_bgm["weight"] = float(safe_bgm["weight"])
                    safe_bgm["bpm"] = int(safe_bgm["bpm"])
                    safe_bgm["duration"] = int(safe_bgm["duration"])
                except (ValueError, TypeError) as e:
                    logger.warning(f"BGM {i} 属性类型转换失败: {e}")
                    # 使用默认值
                    safe_bgm["score"] = 0.0
                    safe_bgm["weight"] = 1.0
                    safe_bgm["bpm"] = 120
                    safe_bgm["duration"] = 30
                
                safe_bgm_list.append(safe_bgm)
                
            except Exception as e:
                logger.error(f"处理BGM项 {i} 时发生错误: {e}")
                continue
        
        if not safe_bgm_list:
            logger.warning("没有有效的BGM项目，返回空列表")
            return []
        
        # 第三步：智能排序
        logger.info(f"开始对 {len(safe_bgm_list)} 个BGM进行排序")
        
        # 多维度排序算法
        sorted_bgm_list = sorted(safe_bgm_list, key=lambda x: (
            x["score"] * x["weight"],  # 主要排序：加权分数
            x["bpm"],                  # 次要排序：BPM
            x["duration"]              # 第三排序：时长
        ), reverse=True)
        
        # 第四步：安全地分配rank属性
        for i, bgm in enumerate(sorted_bgm_list):
            try:
                bgm["rank"] = i + 1
            except Exception as e:
                logger.error(f"设置BGM rank失败: {e}")
                # 如果字典设置失败，强制创建新字典
                sorted_bgm_list[i] = dict(bgm)
                sorted_bgm_list[i]["rank"] = i + 1
        
        logger.info(f"BGM排序完成，共处理 {len(sorted_bgm_list)} 个项目")
        return sorted_bgm_list
        
    except Exception as e:
        logger.error(f"BGM排序过程中发生严重错误: {e}")
        return []

class BGMRankingValidator:
    """BGM排序功能验证器"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        try:
            logger.info(f"🧪 运行测试: {test_name}")
            result = test_func()
            if result:
                logger.info(f"✅ 测试通过: {test_name}")
                self.passed_tests += 1
                self.test_results.append({"test": test_name, "status": "PASS", "error": None})
            else:
                logger.error(f"❌ 测试失败: {test_name}")
                self.failed_tests += 1
                self.test_results.append({"test": test_name, "status": "FAIL", "error": "测试返回False"})
        except Exception as e:
            logger.error(f"❌ 测试异常: {test_name} - {e}")
            self.failed_tests += 1
            self.test_results.append({"test": test_name, "status": "ERROR", "error": str(e)})
    
    def test_normal_bgm_list(self) -> bool:
        """测试正常的BGM列表"""
        bgm_list = [
            {"id": "bgm1", "title": "轻松愉快", "score": 0.95, "weight": 1.2, "bpm": 120, "duration": 30},
            {"id": "bgm2", "title": "商务专业", "score": 0.88, "weight": 1.0, "bpm": 110, "duration": 35},
            {"id": "bgm3", "title": "时尚动感", "score": 0.92, "weight": 1.1, "bpm": 128, "duration": 28}
        ]
        
        result = safe_bgm_ranking(bgm_list)
        
        # 验证结果
        if len(result) != 3:
            logger.error(f"期望3个BGM，实际得到{len(result)}个")
            return False
        
        # 验证rank属性
        for i, bgm in enumerate(result):
            if "rank" not in bgm:
                logger.error(f"BGM {i} 缺少rank属性")
                return False
            if bgm["rank"] != i + 1:
                logger.error(f"BGM {i} rank错误，期望{i+1}，实际{bgm['rank']}")
                return False
        
        # 验证排序正确性（第一个应该是最高分）
        if result[0]["id"] != "bgm1":  # score 0.95 * weight 1.2 = 1.14
            logger.error(f"排序错误，第一个应该是bgm1，实际是{result[0]['id']}")
            return False
        
        logger.info("正常BGM列表测试通过")
        return True
    
    def test_empty_input(self) -> bool:
        """测试空输入"""
        test_cases = [None, [], {}, ""]
        
        for i, test_input in enumerate(test_cases):
            result = safe_bgm_ranking(test_input)
            if result != []:
                logger.error(f"空输入测试{i}失败，期望空列表，实际得到{result}")
                return False
        
        logger.info("空输入测试通过")
        return True
    
    def test_malformed_input(self) -> bool:
        """测试格式错误的输入"""
        test_cases = [
            "invalid json",
            {"invalid": "structure"},
            [None, "string", 123],
            [{"missing_required_fields": True}]
        ]
        
        for i, test_input in enumerate(test_cases):
            try:
                result = safe_bgm_ranking(test_input)
                # 应该返回空列表或处理后的结果，不应该抛出异常
                if not isinstance(result, list):
                    logger.error(f"格式错误输入测试{i}失败，返回类型不是列表")
                    return False
            except Exception as e:
                logger.error(f"格式错误输入测试{i}失败，抛出异常: {e}")
                return False
        
        logger.info("格式错误输入测试通过")
        return True
    
    def test_json_string_input(self) -> bool:
        """测试JSON字符串输入"""
        bgm_list = [
            {"id": "bgm1", "title": "测试BGM", "score": 0.9, "weight": 1.0, "bpm": 120, "duration": 30}
        ]
        json_string = json.dumps(bgm_list)
        
        result = safe_bgm_ranking(json_string)
        
        if len(result) != 1:
            logger.error(f"JSON字符串测试失败，期望1个BGM，实际得到{len(result)}个")
            return False
        
        if "rank" not in result[0] or result[0]["rank"] != 1:
            logger.error("JSON字符串测试失败，rank属性错误")
            return False
        
        logger.info("JSON字符串输入测试通过")
        return True
    
    def test_nested_dict_input(self) -> bool:
        """测试嵌套字典输入"""
        nested_input = {
            "bgm_candidates": [
                {"id": "bgm1", "title": "嵌套BGM1", "score": 0.8, "weight": 1.0, "bpm": 120, "duration": 30},
                {"id": "bgm2", "title": "嵌套BGM2", "score": 0.9, "weight": 1.0, "bpm": 110, "duration": 25}
            ]
        }
        
        result = safe_bgm_ranking(nested_input)
        
        if len(result) != 2:
            logger.error(f"嵌套字典测试失败，期望2个BGM，实际得到{len(result)}个")
            return False
        
        # 验证排序（score 0.9 应该排在前面）
        if result[0]["score"] != 0.9:
            logger.error("嵌套字典测试失败，排序错误")
            return False
        
        logger.info("嵌套字典输入测试通过")
        return True
    
    def test_missing_attributes(self) -> bool:
        """测试缺少属性的BGM"""
        bgm_list = [
            {"id": "bgm1", "title": "不完整BGM"},  # 缺少score, weight等
            {"id": "bgm2", "score": "invalid", "weight": "invalid"}  # 无效类型
        ]
        
        result = safe_bgm_ranking(bgm_list)
        
        if len(result) != 2:
            logger.error(f"缺少属性测试失败，期望2个BGM，实际得到{len(result)}个")
            return False
        
        # 验证默认值被正确设置
        for bgm in result:
            required_attrs = ["score", "weight", "bpm", "duration", "rank"]
            for attr in required_attrs:
                if attr not in bgm:
                    logger.error(f"缺少属性测试失败，BGM缺少{attr}属性")
                    return False
        
        logger.info("缺少属性测试通过")
        return True
    
    def test_rank_assignment_stress(self) -> bool:
        """压力测试rank属性分配"""
        # 创建大量BGM进行测试
        bgm_list = []
        for i in range(100):
            bgm_list.append({
                "id": f"bgm_{i}",
                "title": f"BGM {i}",
                "score": 0.5 + (i % 50) * 0.01,  # 0.5-0.99的分数
                "weight": 1.0,
                "bpm": 120 + (i % 40),
                "duration": 30 + (i % 20)
            })
        
        result = safe_bgm_ranking(bgm_list)
        
        if len(result) != 100:
            logger.error(f"压力测试失败，期望100个BGM，实际得到{len(result)}个")
            return False
        
        # 验证所有rank属性
        for i, bgm in enumerate(result):
            if "rank" not in bgm:
                logger.error(f"压力测试失败，BGM {i} 缺少rank属性")
                return False
            if bgm["rank"] != i + 1:
                logger.error(f"压力测试失败，BGM {i} rank错误")
                return False
        
        # 验证排序正确性
        for i in range(len(result) - 1):
            current_score = result[i]["score"] * result[i]["weight"]
            next_score = result[i + 1]["score"] * result[i + 1]["weight"]
            if current_score < next_score:
                logger.error(f"压力测试失败，排序错误在位置{i}")
                return False
        
        logger.info("压力测试通过")
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始BGM排序功能验证测试")
        logger.info("=" * 60)
        
        # 运行所有测试
        self.run_test("正常BGM列表测试", self.test_normal_bgm_list)
        self.run_test("空输入测试", self.test_empty_input)
        self.run_test("格式错误输入测试", self.test_malformed_input)
        self.run_test("JSON字符串输入测试", self.test_json_string_input)
        self.run_test("嵌套字典输入测试", self.test_nested_dict_input)
        self.run_test("缺少属性测试", self.test_missing_attributes)
        self.run_test("压力测试", self.test_rank_assignment_stress)
        
        # 输出测试结果
        logger.info("=" * 60)
        logger.info("📊 测试结果汇总")
        logger.info(f"✅ 通过测试: {self.passed_tests}")
        logger.info(f"❌ 失败测试: {self.failed_tests}")
        logger.info(f"📈 成功率: {self.passed_tests/(self.passed_tests + self.failed_tests)*100:.1f}%")
        
        if self.failed_tests > 0:
            logger.error("❌ 存在失败的测试，请检查修复")
            for result in self.test_results:
                if result["status"] != "PASS":
                    logger.error(f"  - {result['test']}: {result['status']} - {result['error']}")
            return False
        else:
            logger.info("🎉 所有测试通过！BGM排序功能修复成功")
            return True

def main():
    """主函数"""
    try:
        validator = BGMRankingValidator()
        success = validator.run_all_tests()
        
        if success:
            logger.info("🎯 验证结论：BGM排序功能修复成功，可以安全使用")
            sys.exit(0)
        else:
            logger.error("⚠️ 验证结论：BGM排序功能仍存在问题，需要进一步修复")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"验证过程中发生严重错误: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()