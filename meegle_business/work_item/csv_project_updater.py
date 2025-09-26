#!/usr/bin/env python3
"""
CSV Project Updater - 批量更新项目信息

根据 CSV 文件中的数据批量更新项目信息：
- 使用 Project Code (name 字段) 进行匹配
- 更新 Product name 到 field_28829a（如果为空）
- 更新 Description 到 description 字段（如果为空）
"""

import csv
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from ..timeline.extractor import TimelineExtractor
from .project_manager import ProjectManager
from meegle_sdk import MeegleSDK

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVProjectUpdater:
    """CSV 项目批量更新器"""
    
    def __init__(self, sdk: MeegleSDK):
        """
        初始化更新器
        
        Args:
            sdk: MeegleSDK 实例
        """
        self.sdk = sdk
        self.project_manager = ProjectManager(sdk)
        self.timeline_extractor = TimelineExtractor(sdk)
        
    def load_csv_data(self, csv_file_path: str) -> List[Dict[str, str]]:
        """
        从 CSV 文件加载项目数据
        
        Args:
            csv_file_path: CSV 文件路径
            
        Returns:
            项目数据列表
        """
        projects_data = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8-sig') as file:  # utf-8-sig 处理 BOM
                reader = csv.DictReader(file)
                row_count = 0
                for row in reader:
                    row_count += 1
                    # 清理数据并跳过空行
                    # 处理可能的 BOM 字符
                    code = row.get('Code', row.get('\ufeffCode', '')).strip()
                    product_name = row.get('Product name', '').strip()
                    description = row.get('Description', '').strip()
                    
                    # 调试信息
                    if row_count <= 3:
                        logger.debug(f"Row {row_count}: Code='{code}', Product name='{product_name}', Description='{description[:50]}...'")
                    
                    if code and code != '':  # 只处理有 Code 的行
                        projects_data.append({
                            'code': code,
                            'product_name': product_name,
                            'description': description
                        })
                        
            logger.info(f"从 CSV 文件加载了 {len(projects_data)} 条项目数据 (总共处理了 {row_count} 行)")
            return projects_data
            
        except Exception as e:
            logger.error(f"加载 CSV 文件失败: {e}")
            raise
    
    def get_all_projects(self) -> List[Dict]:
        """
        获取所有项目
        
        Returns:
            项目列表
        """
        try:
            projects = self.sdk.work_items.get_projects()
            logger.info(f"获取到 {len(projects)} 个项目")
            return projects
        except Exception as e:
            logger.error(f"获取项目列表失败: {e}")
            raise
    
    def find_project_by_code(self, projects: List[Dict], target_code: str) -> Optional[Dict]:
        """
        根据项目代码查找项目
        
        Args:
            projects: 项目列表
            target_code: 目标项目代码
            
        Returns:
            匹配的项目或 None
        """
        for project in projects:
            # 从 name 字段获取项目代码
            project_code = project.get('name', '').strip()
            if project_code == target_code:
                return project
        return None
    
    def should_update_field(self, current_value: any) -> bool:
        """
        判断是否应该更新字段（仅当字段为空时更新）
        
        Args:
            current_value: 当前字段值
            
        Returns:
            是否应该更新
        """
        if current_value is None:
            return True
        if isinstance(current_value, str) and current_value.strip() == '':
            return True
        if current_value == '-':  # CSV 中的占位符
            return True
        return False
    
    def analyze_update_needs(self, csv_file_path: str) -> Dict:
        """
        分析更新需求，但不执行实际更新
        
        Args:
            csv_file_path: CSV 文件路径
            
        Returns:
            分析结果
        """
        csv_data = self.load_csv_data(csv_file_path)
        all_projects = self.get_all_projects()
        
        analysis = {
            'total_csv_records': len(csv_data),
            'total_projects': len(all_projects),
            'matches_found': 0,
            'updates_needed': 0,
            'field_28829a_updates': 0,
            'description_updates': 0,
            'no_updates_needed': 0,
            'not_found': 0,
            'details': []
        }
        
        for csv_record in csv_data:
            code = csv_record['code']
            product_name = csv_record['product_name']
            description = csv_record['description']
            
            # 查找匹配的项目
            project = self.find_project_by_code(all_projects, code)
            
            if not project:
                analysis['not_found'] += 1
                analysis['details'].append({
                    'code': code,
                    'status': 'not_found',
                    'message': f'未找到代码为 {code} 的项目'
                })
                continue
            
            analysis['matches_found'] += 1
            
            # 检查是否需要更新
            current_field_28829a = project.get('field_28829a')
            current_description = project.get('description')
            
            needs_field_28829a_update = (
                product_name and 
                product_name != '-' and 
                self.should_update_field(current_field_28829a)
            )
            
            needs_description_update = (
                description and 
                description != '-' and 
                self.should_update_field(current_description)
            )
            
            if needs_field_28829a_update or needs_description_update:
                analysis['updates_needed'] += 1
                if needs_field_28829a_update:
                    analysis['field_28829a_updates'] += 1
                if needs_description_update:
                    analysis['description_updates'] += 1
                
                analysis['details'].append({
                    'code': code,
                    'project_id': project.get('id'),
                    'status': 'needs_update',
                    'updates': {
                        'field_28829a': {
                            'needed': needs_field_28829a_update,
                            'current': current_field_28829a,
                            'new': product_name if needs_field_28829a_update else None
                        },
                        'description': {
                            'needed': needs_description_update,
                            'current': current_description,
                            'new': description if needs_description_update else None
                        }
                    }
                })
            else:
                analysis['no_updates_needed'] += 1
                analysis['details'].append({
                    'code': code,
                    'project_id': project.get('id'),
                    'status': 'no_update_needed',
                    'message': '所有字段都已有值，跳过更新'
                })
        
        return analysis
    
    def batch_update_projects(self, csv_file_path: str, dry_run: bool = True) -> Dict:
        """
        批量更新项目
        
        Args:
            csv_file_path: CSV 文件路径
            dry_run: 是否为试运行（不执行实际更新）
            
        Returns:
            更新结果统计
        """
        csv_data = self.load_csv_data(csv_file_path)
        all_projects = self.get_all_projects()
        
        results = {
            'total_processed': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'skipped_updates': 0,
            'not_found': 0,
            'details': []
        }
        
        for csv_record in csv_data:
            results['total_processed'] += 1
            code = csv_record['code']
            product_name = csv_record['product_name']
            description = csv_record['description']
            
            logger.info(f"处理项目: {code}")
            
            # 查找匹配的项目
            project = self.find_project_by_code(all_projects, code)
            
            if not project:
                results['not_found'] += 1
                results['details'].append({
                    'code': code,
                    'status': 'not_found',
                    'message': f'未找到代码为 {code} 的项目'
                })
                logger.warning(f"未找到项目: {code}")
                continue
            
            project_id = project.get('id')
            
            # 检查是否需要更新
            current_field_28829a = project.get('field_28829a')
            current_description = project.get('description')
            
            needs_field_28829a_update = (
                product_name and 
                product_name != '-' and 
                self.should_update_field(current_field_28829a)
            )
            
            needs_description_update = (
                description and 
                description != '-' and 
                self.should_update_field(current_description)
            )
            
            if not needs_field_28829a_update and not needs_description_update:
                results['skipped_updates'] += 1
                results['details'].append({
                    'code': code,
                    'project_id': project_id,
                    'status': 'skipped',
                    'message': '所有字段都已有值，跳过更新'
                })
                logger.info(f"跳过项目 {code} (ID: {project_id})：所有字段都已有值")
                continue
            
            # 准备更新数据
            update_data = {}
            if needs_field_28829a_update:
                update_data['name'] = product_name  # ProjectManager 中 name 映射到 field_28829a
            if needs_description_update:
                update_data['description'] = description
            
            if dry_run:
                results['successful_updates'] += 1
                results['details'].append({
                    'code': code,
                    'project_id': project_id,
                    'status': 'would_update',
                    'updates': update_data,
                    'message': f'试运行：将更新 {", ".join(update_data.keys())}'
                })
                logger.info(f"试运行：项目 {code} (ID: {project_id}) 将更新: {update_data}")
            else:
                # 执行实际更新
                try:
                    result = self.project_manager.update_project_info(
                        project_id=project_id,
                        **update_data
                    )
                    
                    results['successful_updates'] += 1
                    results['details'].append({
                        'code': code,
                        'project_id': project_id,
                        'status': 'updated',
                        'updates': update_data,
                        'message': f'成功更新 {", ".join(update_data.keys())}'
                    })
                    logger.info(f"成功更新项目 {code} (ID: {project_id}): {update_data}")
                    
                except Exception as e:
                    results['failed_updates'] += 1
                    results['details'].append({
                        'code': code,
                        'project_id': project_id,
                        'status': 'failed',
                        'updates': update_data,
                        'error': str(e),
                        'message': f'更新失败: {e}'
                    })
                    logger.error(f"更新项目 {code} (ID: {project_id}) 失败: {e}")
        
        return results
    
    def print_analysis_summary(self, analysis: Dict):
        """
        打印分析摘要
        
        Args:
            analysis: 分析结果
        """
        print("\n" + "="*60)
        print("项目更新需求分析摘要")
        print("="*60)
        print(f"CSV 记录总数: {analysis['total_csv_records']}")
        print(f"系统项目总数: {analysis['total_projects']}")
        print(f"找到匹配项目: {analysis['matches_found']}")
        print(f"需要更新的项目: {analysis['updates_needed']}")
        print(f"  - 需要更新 field_28829a: {analysis['field_28829a_updates']}")
        print(f"  - 需要更新 description: {analysis['description_updates']}")
        print(f"无需更新的项目: {analysis['no_updates_needed']}")
        print(f"未找到的项目: {analysis['not_found']}")
        print("="*60)
    
    def print_update_summary(self, results: Dict, dry_run: bool = True):
        """
        打印更新结果摘要
        
        Args:
            results: 更新结果
            dry_run: 是否为试运行
        """
        mode = "试运行" if dry_run else "实际执行"
        print(f"\n" + "="*60)
        print(f"项目批量更新结果摘要 ({mode})")
        print("="*60)
        print(f"处理记录总数: {results['total_processed']}")
        print(f"成功更新: {results['successful_updates']}")
        print(f"更新失败: {results['failed_updates']}")
        print(f"跳过更新: {results['skipped_updates']}")
        print(f"未找到项目: {results['not_found']}")
        print("="*60)
