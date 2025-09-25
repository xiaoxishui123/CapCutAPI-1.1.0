#!/usr/bin/env python3
"""
工作流配置验证测试脚本
验证修复版短视频工作流配置的完整性和正确性
"""

import yaml
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorkflowValidator:
    """工作流配置验证器"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.validation_results = []
        self.errors = []
        self.warnings = []
    
    def load_config(self) -> bool:
        """加载工作流配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"成功加载配置文件: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return False
    
    def validate_basic_structure(self) -> bool:
        """验证基本结构"""
        logger.info("🔍 验证基本结构...")
        
        # 检查Dify工作流基本结构
        required_sections = ['app', 'kind', 'version', 'workflow']
        missing_sections = []
        
        for section in required_sections:
            if section not in self.config:
                missing_sections.append(section)
        
        if missing_sections:
            self.errors.append(f"缺少必要的配置节: {missing_sections}")
            return False
        
        # 验证workflow结构
        workflow = self.config.get('workflow', {})
        required_workflow_sections = ['graph']
        
        for section in required_workflow_sections:
            if section not in workflow:
                self.errors.append(f"workflow中缺少{section}节")
                return False
        
        # 验证graph结构
        graph = workflow.get('graph', {})
        required_graph_sections = ['nodes', 'edges']
        
        for section in required_graph_sections:
            if section not in graph:
                self.errors.append(f"graph中缺少{section}节")
                return False
        
        logger.info("✅ 基本结构验证通过")
        return True
    
    def validate_nodes(self) -> bool:
        """验证节点配置"""
        logger.info("🔍 验证节点配置...")
        
        workflow = self.config.get('workflow', {})
        graph = workflow.get('graph', {})
        nodes = graph.get('nodes', [])
        
        if not isinstance(nodes, list):
            self.errors.append("nodes必须是列表类型")
            return False
        
        # 检查是否有节点
        if not nodes:
            self.errors.append("工作流中没有定义任何节点")
            return False
        
        # 将节点列表转换为字典以便查找
        nodes_dict = {}
        for node in nodes:
            node_id = node.get('id')
            if node_id:
                nodes_dict[node_id] = node
        
        # 查找关键节点（使用更灵活的匹配）
        node_ids = list(nodes_dict.keys())
        
        # 检查是否有BGM相关节点
        bgm_nodes = [node_id for node_id in node_ids if 'bgm' in node_id.lower()]
        if not bgm_nodes:
            self.warnings.append("未找到BGM相关节点，可能影响BGM功能")
        
        # 检查代码节点
        code_nodes = []
        for node_id, node_data in nodes_dict.items():
            if isinstance(node_data, dict) and node_data.get('data', {}).get('type') == 'code':
                code_nodes.append(node_id)
        
        if not code_nodes:
            self.warnings.append("未找到代码节点，可能缺少自定义逻辑")
        
        # 验证BGM智能排序节点（如果存在）
        bgm_ranking_nodes = [node_id for node_id in node_ids if 'ranking' in node_id.lower() and 'bgm' in node_id.lower()]
        
        for bgm_node_id in bgm_ranking_nodes:
            bgm_node = nodes_dict.get(bgm_node_id, {})
            if bgm_node.get('data', {}).get('type') != 'code':
                self.warnings.append(f"BGM排序节点{bgm_node_id}类型不是code")
                continue
            
            # 检查BGM节点是否包含safe_bgm_ranking函数
            bgm_code = bgm_node.get('data', {}).get('code', '')
            if 'safe_bgm_ranking' not in bgm_code:
                self.warnings.append(f"BGM排序节点{bgm_node_id}可能缺少safe_bgm_ranking函数")
            
            if 'rank' not in bgm_code:
                self.warnings.append(f"BGM排序节点{bgm_node_id}可能缺少rank属性处理")
        
        logger.info("✅ 节点配置验证通过")
        return True
    
    def validate_edges(self) -> bool:
        """验证边配置"""
        logger.info("🔍 验证边配置...")
        
        workflow = self.config.get('workflow', {})
        graph = workflow.get('graph', {})
        edges = graph.get('edges', [])
        
        if not isinstance(edges, list):
            self.errors.append("edges必须是列表类型")
            return False
        
        # 收集所有节点ID - 修复节点收集逻辑
        nodes_list = graph.get('nodes', [])
        if isinstance(nodes_list, list):
            nodes = set(node.get('id') for node in nodes_list if isinstance(node, dict) and node.get('id'))
        else:
            nodes = set(nodes_list.keys()) if isinstance(nodes_list, dict) else set()
        
        if not edges:
            self.warnings.append("工作流中没有定义任何边")
            return True
        
        # 验证边的有效性
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                self.errors.append(f"边{i}必须是字典类型")
                continue
            
            # Dify工作流中边的字段可能是source/target而不是source_node_id/target_node_id
            source = edge.get('source') or edge.get('source_node_id')
            target = edge.get('target') or edge.get('target_node_id')
            
            if not source or not target:
                self.errors.append(f"边{i}缺少source/target字段")
                continue
            
            if source not in nodes:
                self.warnings.append(f"边{i}的源节点{source}可能不存在")
            
            if target not in nodes:
                self.warnings.append(f"边{i}的目标节点{target}可能不存在")
        
        # 验证BGM分支逻辑（更灵活的检查）
        bgm_condition_nodes = [node_id for node_id in nodes if 'bgm' in node_id.lower() and 'condition' in node_id.lower()]
        
        for bgm_node in bgm_condition_nodes:
            bgm_condition_edges = [e for e in edges if (e.get('source') or e.get('source_node_id')) == bgm_node]
            if len(bgm_condition_edges) < 2:
                self.warnings.append(f"BGM条件节点{bgm_node}可能需要至少2条输出边（启用和禁用BGM）")
        
        logger.info("✅ 边配置验证通过")
        return True
    
    def validate_bgm_functionality(self) -> bool:
        """验证BGM功能完整性"""
        logger.info("🔍 验证BGM功能完整性...")
        
        workflow = self.config.get('workflow', {})
        graph = workflow.get('graph', {})
        nodes = graph.get('nodes', [])
        
        # 将节点列表转换为字典以便查找
        nodes_dict = {}
        for node in nodes:
            node_id = node.get('id')
            if node_id:
                nodes_dict[node_id] = node
        
        # 查找BGM相关节点
        bgm_condition_nodes = [node_id for node_id in nodes_dict.keys() if 'bgm' in node_id.lower() and 'condition' in node_id.lower()]
        bgm_ranking_nodes = [node_id for node_id in nodes_dict.keys() if 'bgm' in node_id.lower() and 'ranking' in node_id.lower()]
        
        if not bgm_condition_nodes:
            self.warnings.append("未找到BGM条件检查节点")
        
        if not bgm_ranking_nodes:
            self.warnings.append("未找到BGM智能排序节点")
        
        # 验证BGM排序节点的代码
        for bgm_node_id in bgm_ranking_nodes:
            bgm_ranking = nodes_dict.get(bgm_node_id, {})
            bgm_code = bgm_ranking.get('data', {}).get('code', '')
            
            if not bgm_code:
                self.warnings.append(f"BGM排序节点{bgm_node_id}没有代码内容")
                continue
            
            required_functions = ['safe_bgm_ranking', 'ensure_object_initialization']
            
            for func in required_functions:
                if func not in bgm_code:
                    self.warnings.append(f"BGM排序节点{bgm_node_id}可能缺少{func}函数")
            
            # 检查错误处理
            if 'try:' not in bgm_code or 'except:' not in bgm_code:
                self.warnings.append(f"BGM排序节点{bgm_node_id}可能缺少异常处理")
            
            # 检查rank属性安全设置
            if 'rank' not in bgm_code:
                self.warnings.append(f"BGM排序节点{bgm_node_id}可能缺少rank属性处理")
        
        logger.info("✅ BGM功能完整性验证通过")
        return True
    
    def validate_environment_variables(self) -> bool:
        """验证环境变量配置"""
        logger.info("🔍 验证环境变量配置...")
        
        workflow = self.config.get('workflow', {})
        env_vars = workflow.get('environment_variables', [])
        
        if not isinstance(env_vars, list):
            self.errors.append("environment_variables必须是列表类型")
            return False
        
        if not env_vars:
            self.warnings.append("工作流中没有定义环境变量")
            return True
        
        # 检查环境变量格式
        var_names = []
        for var in env_vars:
            if isinstance(var, dict):
                # Dify工作流中环境变量可能使用name字段而不是key
                var_name = var.get('name') or var.get('key')
                if var_name:
                    var_names.append(var_name.lower())
        
        # 检查重要的环境变量
        important_vars = ['mcp_bridge_url', 'capcut_api_url', 'enable_bgm']
        missing_vars = []
        
        for var in important_vars:
            if var.lower() not in var_names:
                missing_vars.append(var)
        
        if missing_vars:
            self.warnings.append(f"可能缺少重要环境变量: {missing_vars}")
        
        logger.info("✅ 环境变量配置验证通过")
        return True
    
    def validate_data_flow(self) -> bool:
        """验证数据流完整性"""
        logger.info("🔍 验证数据流完整性...")
        
        workflow = self.config.get('workflow', {})
        graph = workflow.get('graph', {})
        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])
        
        # 将节点列表转换为字典以便查找
        nodes_dict = {}
        for node in nodes:
            node_id = node.get('id')
            if node_id:
                nodes_dict[node_id] = node
        
        if not edges:
            self.warnings.append("工作流中没有定义边连接")
            return True
        
        # 构建图结构
        graph_structure = {}
        for edge in edges:
            # Dify工作流中边可能使用source/target字段
            source = edge.get('source') or edge.get('source_node_id')
            target = edge.get('target') or edge.get('target_node_id')
            if source and target:
                if source not in graph_structure:
                    graph_structure[source] = []
                graph_structure[source].append(target)
        
        # 检查从start到end的路径（如果存在这些节点）
        def has_path(start, end, visited=None):
            if visited is None:
                visited = set()
            if start == end:
                return True
            if start in visited:
                return False
            visited.add(start)
            for neighbor in graph_structure.get(start, []):
                if has_path(neighbor, end, visited.copy()):
                    return True
            return False
        
        # 查找可能的开始和结束节点
        start_nodes = [node_id for node_id in nodes_dict.keys() if 'start' in node_id.lower()]
        end_nodes = [node_id for node_id in nodes_dict.keys() if 'end' in node_id.lower()]
        
        if start_nodes and end_nodes:
            path_exists = False
            for start_node in start_nodes:
                for end_node in end_nodes:
                    if has_path(start_node, end_node):
                        path_exists = True
                        break
                if path_exists:
                    break
            
            if not path_exists:
                self.warnings.append("可能没有从开始节点到结束节点的有效路径")
        
        # 检查BGM分支路径
        bgm_condition_nodes = [node_id for node_id in nodes_dict.keys() if 'bgm' in node_id.lower() and 'condition' in node_id.lower()]
        bgm_ranking_nodes = [node_id for node_id in nodes_dict.keys() if 'bgm' in node_id.lower() and 'ranking' in node_id.lower()]
        
        for bgm_condition in bgm_condition_nodes:
            if bgm_condition in graph_structure:
                bgm_targets = graph_structure[bgm_condition]
                has_ranking_connection = any(target in bgm_ranking_nodes for target in bgm_targets)
                if not has_ranking_connection:
                    # 检查是否有条件边指向BGM排序
                    bgm_condition_edges = [e for e in edges if (e.get('source') or e.get('source_node_id')) == bgm_condition]
                    has_bgm_path = any((e.get('target') or e.get('target_node_id')) in bgm_ranking_nodes for e in bgm_condition_edges)
                    if not has_bgm_path:
                        self.warnings.append(f"BGM条件检查节点{bgm_condition}可能没有正确连接到BGM排序节点")
        
        logger.info("✅ 数据流完整性验证通过")
        return True
    
    def validate_code_syntax(self) -> bool:
        """验证代码节点语法"""
        logger.info("🔍 验证代码节点语法...")
        
        workflow = self.config.get('workflow', {})
        graph = workflow.get('graph', {})
        nodes = graph.get('nodes', [])
        
        if not nodes:
            self.warnings.append("工作流中没有定义节点")
            return True
        
        code_nodes_found = 0
        
        for node in nodes:
            node_id = node.get('id')
            if not node_id:
                continue
                
            # 检查节点类型
            node_type = node.get('data', {}).get('type') or node.get('type')
            
            if node_type == 'code':
                code_nodes_found += 1
                code = node.get('data', {}).get('code', '')
                
                if not code:
                    self.warnings.append(f"代码节点{node_id}没有代码内容")
                    continue
                
                try:
                    # 尝试编译Python代码
                    compile(code, f'<{node_id}>', 'exec')
                    
                    # 检查是否包含BGM相关的安全代码
                    if 'bgm' in node_id.lower():
                        if 'safe_bgm_ranking' not in code:
                            self.warnings.append(f"BGM节点{node_id}可能缺少safe_bgm_ranking函数")
                        if 'rank' in code and 'try:' not in code:
                            self.warnings.append(f"BGM节点{node_id}的rank操作可能缺少异常处理")
                    
                except SyntaxError as e:
                    self.errors.append(f"代码节点{node_id}语法错误: {e}")
                    return False
                except Exception as e:
                    self.warnings.append(f"代码节点{node_id}可能存在问题: {e}")
        
        if code_nodes_found == 0:
            self.warnings.append("工作流中没有找到代码节点")
        
        logger.info("✅ 代码节点语法验证通过")
        return True
    
    def run_validation(self) -> bool:
        """运行完整验证"""
        logger.info("🚀 开始工作流配置验证")
        logger.info("=" * 60)
        
        if not self.load_config():
            return False
        
        validation_steps = [
            ("基本结构", self.validate_basic_structure),
            ("节点配置", self.validate_nodes),
            ("边配置", self.validate_edges),
            ("BGM功能", self.validate_bgm_functionality),
            ("环境变量", self.validate_environment_variables),
            ("数据流", self.validate_data_flow),
            ("代码语法", self.validate_code_syntax)
        ]
        
        passed_steps = 0
        total_steps = len(validation_steps)
        
        for step_name, step_func in validation_steps:
            try:
                if step_func():
                    passed_steps += 1
                    self.validation_results.append({"step": step_name, "status": "PASS"})
                else:
                    self.validation_results.append({"step": step_name, "status": "FAIL"})
            except Exception as e:
                logger.error(f"验证步骤{step_name}发生异常: {e}")
                self.validation_results.append({"step": step_name, "status": "ERROR"})
                self.errors.append(f"验证步骤{step_name}异常: {e}")
        
        # 输出验证结果
        logger.info("=" * 60)
        logger.info("📊 验证结果汇总")
        logger.info(f"✅ 通过步骤: {passed_steps}/{total_steps}")
        logger.info(f"❌ 错误数量: {len(self.errors)}")
        logger.info(f"⚠️ 警告数量: {len(self.warnings)}")
        
        if self.errors:
            logger.error("❌ 发现的错误:")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        if self.warnings:
            logger.warning("⚠️ 发现的警告:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        success = len(self.errors) == 0
        if success:
            logger.info("🎉 工作流配置验证通过！")
        else:
            logger.error("❌ 工作流配置验证失败，请修复错误后重试")
        
        return success
    
    def generate_report(self) -> str:
        """生成验证报告"""
        report = f"""# 工作流配置验证报告

## 配置文件
- 文件路径: {self.config_path}
- 验证时间: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}

## 验证结果
"""
        
        for result in self.validation_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            report += f"- {status_icon} {result['step']}: {result['status']}\n"
        
        if self.errors:
            report += "\n## 错误列表\n"
            for i, error in enumerate(self.errors, 1):
                report += f"{i}. {error}\n"
        
        if self.warnings:
            report += "\n## 警告列表\n"
            for i, warning in enumerate(self.warnings, 1):
                report += f"{i}. {warning}\n"
        
        report += f"\n## 总结\n"
        report += f"- 验证步骤: {len(self.validation_results)}\n"
        report += f"- 通过步骤: {sum(1 for r in self.validation_results if r['status'] == 'PASS')}\n"
        report += f"- 错误数量: {len(self.errors)}\n"
        report += f"- 警告数量: {len(self.warnings)}\n"
        
        return report

def main():
    """主函数"""
    # 配置文件路径
    config_files = [
        "/home/dify/MCP_Bridge_Project/configs/优化版短视频工作流_修复版.yml",
        "/home/dify/MCP_Bridge_Project/configs/优化版短视频工作流.yml"
    ]
    
    all_passed = True
    
    for config_file in config_files:
        if not os.path.exists(config_file):
            logger.warning(f"配置文件不存在: {config_file}")
            continue
        
        logger.info(f"\n{'='*80}")
        logger.info(f"验证配置文件: {config_file}")
        logger.info(f"{'='*80}")
        
        validator = WorkflowValidator(config_file)
        success = validator.run_validation()
        
        if not success:
            all_passed = False
        
        # 生成报告
        report = validator.generate_report()
        report_file = config_file.replace('.yml', '_validation_report.md')
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"验证报告已保存: {report_file}")
        except Exception as e:
            logger.error(f"保存验证报告失败: {e}")
    
    if all_passed:
        logger.info("\n🎯 所有工作流配置验证通过！")
        sys.exit(0)
    else:
        logger.error("\n⚠️ 部分工作流配置验证失败，请检查错误并修复")
        sys.exit(1)

if __name__ == "__main__":
    main()