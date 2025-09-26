#!/usr/bin/env python3
"""
Project Migrator - 项目迁移工具

从老的项目 work item 类型迁移到新的项目 work item 类型：
- 老的项目类型: 642ec373f4af608bb3cb1c90
- 新的项目类型: 68afee24c92ef633f847d304
- 迁移字段: name, business, description, role_owners
- 字段映射: field_f7f3d2 -> field_696f08 (关联的 feature work items)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from meegle_sdk import MeegleSDK
from .business_field_mapper import BusinessFieldMapper

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """迁移结果"""
    old_project_id: int
    new_project_id: Optional[int]
    success: bool
    error_message: Optional[str] = None
    migrated_fields: List[str] = None


class ProjectMigrator:
    """项目迁移器"""
    
    # 项目类型常量
    OLD_PROJECT_TYPE = "642ec373f4af608bb3cb1c90"
    NEW_PROJECT_TYPE = "68afee24c92ef633f847d304"
    
    # 字段映射
    FIELD_MAPPING = {
        "field_f7f3d2": "field_696f08"  # 关联的 feature work items
    }
    
    # 角色映射
    ROLE_MAPPING = {
        "assignee": "role_project_owner"  # 老项目的 assignee 映射到新项目的 role_project_owner
    }
    
    def __init__(self, sdk: MeegleSDK):
        """
        初始化迁移器
        
        Args:
            sdk: MeegleSDK 实例
        """
        self.sdk = sdk
        self.business_mapper = BusinessFieldMapper()
        
        # 配置默认的业务线映射策略
        # 由于新旧项目的 business 字段都是 ID 格式，默认直接传递
        self.business_mapper.set_default_business("DIRECT_PASS")  # 特殊标记表示直接传递
    
    def configure_business_mapping(self, mapping: Dict[str, str] = None, 
                                  default_business: Optional[str] = None,
                                  strict_mode: bool = False):
        """
        配置业务线字段映射
        
        Args:
            mapping: 老业务线到新业务线的映射字典
            default_business: 默认业务线值，None 表示跳过该字段
            strict_mode: 是否启用严格模式（找不到映射时抛出异常）
        """
        if mapping:
            self.business_mapper.set_business_mapping(mapping)
        if default_business is not None:
            self.business_mapper.set_default_business(default_business)
        self.business_mapper.set_strict_mode(strict_mode)
    
    def _extract_business_from_fields(self, fields: List[Dict[str, Any]]) -> Optional[str]:
        """
        从 fields 数组中提取 business 字段值
        
        Args:
            fields: 项目的 fields 数组
            
        Returns:
            business 字段的值，如果不存在则返回 None
        """
        for field in fields:
            if field.get('field_key') == 'business':
                return field.get('field_value')
        return None
    
    def _extract_description_from_fields(self, fields: List[Dict[str, Any]]) -> str:
        """
        从 fields 数组中提取 description 字段值
        
        Args:
            fields: 项目的 fields 数组
            
        Returns:
            description 字段的值
        """
        for field in fields:
            if field.get('field_key') == 'description':
                return field.get('field_value', '')
        return ''
    
    def _extract_role_owners_from_fields(self, fields: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        从 fields 数组中提取 role_owners 字段值，并处理角色映射
        
        Args:
            fields: 项目的 fields 数组
            
        Returns:
            处理了角色映射的 role_owners 字段值
        """
        for field in fields:
            if field.get('field_key') == 'role_owners':
                role_owners = field.get('field_value')
                if role_owners:
                    # 处理角色映射
                    mapped_role_owners = []
                    for role_owner in role_owners:
                        old_role = role_owner.get('role')
                        if old_role in self.ROLE_MAPPING:
                            new_role = self.ROLE_MAPPING[old_role]
                            mapped_role_owner = role_owner.copy()
                            mapped_role_owner['role'] = new_role
                            mapped_role_owners.append(mapped_role_owner)
                            logger.info(f"角色映射: {old_role} -> {new_role}")
                        else:
                            # 角色不需要映射，直接使用
                            mapped_role_owners.append(role_owner)
                    return mapped_role_owners
                return role_owners
        return None
        
    def get_old_projects(self) -> List[Dict[str, Any]]:
        """
        获取所有老的项目
        
        Returns:
            老项目列表
        """
        try:
            logger.info("获取所有老的项目...")
            old_projects = self.sdk.work_items.get_all_work_items(
                work_item_type_keys=[self.OLD_PROJECT_TYPE]
            )
            logger.info(f"找到 {len(old_projects)} 个老项目")
            return old_projects
        except Exception as e:
            logger.error(f"获取老项目失败: {e}")
            raise
    
    def get_project_details(self, project_id: int, project_type: str) -> Optional[Dict[str, Any]]:
        """
        获取项目详细信息
        
        Args:
            project_id: 项目 ID
            project_type: 项目类型
            
        Returns:
            项目详细信息或 None
        """
        try:
            projects = self.sdk.work_items.get_work_items_by_ids(
                work_item_ids=[project_id],
                work_item_type_key=project_type
            )
            return projects[0] if projects else None
        except Exception as e:
            logger.error(f"获取项目 {project_id} 详情失败: {e}")
            return None
    
    def extract_migration_data(self, old_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        从老项目中提取需要迁移的数据
        
        Args:
            old_project: 老项目数据
            
        Returns:
            需要迁移的字段数据
        """
        migration_data = {}
        
        # 基础字段
        migration_data['name'] = old_project.get('name', '')
        
        # 处理 business 字段
        # 重新分析确认：新项目类型确实支持 business 字段
        # 需要正确迁移 business 字段值
        old_business = self._extract_business_from_fields(old_project.get('fields', []))
        if old_business:
            # 使用业务线映射器处理 business 值
            mapped_business = self.business_mapper.map_business_value(old_business)
            if mapped_business is not None:
                migration_data['business'] = mapped_business
                logger.info(f"项目 {old_project.get('name')} business 字段: {old_business} -> {mapped_business}")
            else:
                logger.info(f"项目 {old_project.get('name')} business 字段 {old_business} 被跳过（无映射）")
            
        # 从 fields 数组中提取 description
        fields = old_project.get('fields', [])
        migration_data['description'] = self._extract_description_from_fields(fields)
        
        # 从 fields 数组中提取 role_owners 字段
        role_owners = self._extract_role_owners_from_fields(fields)
        if role_owners:
            migration_data['role_owners'] = role_owners
        
        # 处理字段映射 - 从 fields 数组中提取
        for field in fields:
            field_key = field.get('field_key')
            if field_key in self.FIELD_MAPPING:
                new_field_key = self.FIELD_MAPPING[field_key]
                field_value = field.get('field_value')
                
                # 如果是 field_696f08 (关联功能字段)，需要验证和清理
                if new_field_key == 'field_696f08' and field_value:
                    cleaned_value = self._clean_related_features(field_value, old_project.get('name', ''))
                    if cleaned_value:
                        migration_data[new_field_key] = cleaned_value
                        logger.debug(f"映射字段 {field_key} -> {new_field_key} (已清理)")
                    else:
                        logger.info(f"跳过字段 {field_key}，所有关联功能都已过期")
                else:
                    migration_data[new_field_key] = field_value
                    logger.debug(f"映射字段 {field_key} -> {new_field_key}")
        
        return migration_data
    
    def create_field_value_pairs(self, migration_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        创建字段值对列表用于创建新项目
        
        Args:
            migration_data: 迁移数据
            
        Returns:
            字段值对列表
        """
        field_value_pairs = []
        
        # 处理 business 字段
        if migration_data.get('business'):
            field_value_pairs.append({
                "field_key": "business",
                "field_value": migration_data['business']
            })
        
        if migration_data.get('description'):
            field_value_pairs.append({
                "field_key": "description",
                "field_value": migration_data['description']
            })
        
        # role_owners 字段
        if migration_data.get('role_owners'):
            field_value_pairs.append({
                "field_key": "role_owners",
                "field_value": migration_data['role_owners']
            })
        
        # 映射的关联字段
        if migration_data.get('field_696f08'):
            field_value_pairs.append({
                "field_key": "field_696f08",
                "field_value": migration_data['field_696f08']
            })
        
        return field_value_pairs
    
    def _clean_related_features(self, field_value: Any, project_name: str = "") -> Any:
        """
        清理关联功能字段值，移除可能过期的引用
        
        Args:
            field_value: 原始字段值
            project_name: 项目名称（用于日志）
            
        Returns:
            清理后的字段值，如果所有值都无效则返回 None
        """
        if not field_value:
            return None
            
        # 如果是字符串类型，直接返回（可能是单个ID）
        if isinstance(field_value, str):
            if field_value.strip():
                logger.info(f"项目 {project_name}: 保留关联功能 {field_value}")
                return field_value.strip()
            return None
            
        # 如果是列表类型，过滤空值
        elif isinstance(field_value, list):
            cleaned_list = []
            for item in field_value:
                if isinstance(item, str) and item.strip():
                    cleaned_list.append(item.strip())
                elif isinstance(item, dict) and item.get('value'):
                    # 处理可能的对象格式 {"value": "id", "label": "name"}
                    cleaned_list.append(item)
                    
            if cleaned_list:
                logger.info(f"项目 {project_name}: 保留 {len(cleaned_list)} 个关联功能")
                return cleaned_list
            else:
                logger.info(f"项目 {project_name}: 所有关联功能都已清理")
                return None
                
        # 如果是字典类型，检查是否有有效值
        elif isinstance(field_value, dict):
            if field_value.get('value') or field_value.get('id'):
                logger.info(f"项目 {project_name}: 保留关联功能对象")
                return field_value
            return None
            
        # 其他类型，尝试转换为字符串
        else:
            str_value = str(field_value).strip()
            if str_value and str_value != 'None':
                logger.info(f"项目 {project_name}: 保留关联功能 {str_value}")
                return str_value
            return None
    
    def _create_project_with_fallback(self, project_name: str, old_project_id: int, 
                                    field_value_pairs: List[Dict[str, Any]],
                                    migration_data: Dict[str, Any]) -> MigrationResult:
        """
        创建项目，支持失败回退策略
        
        Args:
            project_name: 项目名称
            old_project_id: 老项目ID
            field_value_pairs: 字段值对列表
            migration_data: 迁移数据
            
        Returns:
            迁移结果
        """
        # 尝试1: 包含所有字段
        try:
            logger.info(f"创建新项目: {project_name}")
            create_response = self.sdk.work_items.create_work_item(
                work_item_type_key=self.NEW_PROJECT_TYPE,
                name=project_name,
                field_value_pairs=field_value_pairs
            )
            
            new_project_id = None
            if isinstance(create_response, dict):
                new_project_id = create_response.get('data')
            
            if new_project_id:
                logger.info(f"成功创建新项目 {project_name}, 新 ID: {new_project_id}")
                return MigrationResult(
                    old_project_id=old_project_id,
                    new_project_id=new_project_id,
                    success=True,
                    migrated_fields=list(migration_data.keys())
                )
        except Exception as e:
            error_msg = str(e)
            
            # 检查是否是 Related features 字段过期错误
            if "Related features" in error_msg and "expired" in error_msg:
                logger.warning(f"项目 {project_name}: Related features 字段过期，尝试移除该字段")
                
                # 尝试2: 移除 field_696f08 字段
                filtered_pairs = [pair for pair in field_value_pairs 
                                if pair.get('field_key') != 'field_696f08']
                
                try:
                    logger.info(f"重新创建项目（跳过 Related features）: {project_name}")
                    create_response = self.sdk.work_items.create_work_item(
                        work_item_type_key=self.NEW_PROJECT_TYPE,
                        name=project_name,
                        field_value_pairs=filtered_pairs
                    )
                    
                    new_project_id = None
                    if isinstance(create_response, dict):
                        new_project_id = create_response.get('data')
                    
                    if new_project_id:
                        logger.info(f"成功创建新项目（跳过 Related features）{project_name}, 新 ID: {new_project_id}")
                        return MigrationResult(
                            old_project_id=old_project_id,
                            new_project_id=new_project_id,
                            success=True,
                            migrated_fields=[field.get('field_key') for field in filtered_pairs],
                            error_message=f"跳过了 Related features 字段（配置过期）"
                        )
                except Exception as e2:
                    logger.warning(f"项目 {project_name}: 跳过 Related features 后仍然失败: {str(e2)}")
                    
                    # 尝试3: 只保留基本字段
                    basic_pairs = [pair for pair in field_value_pairs 
                                 if pair.get('field_key') in ['business', 'description']]
                    
                    try:
                        logger.info(f"创建基本项目（仅保留 business 和 description）: {project_name}")
                        create_response = self.sdk.work_items.create_work_item(
                            work_item_type_key=self.NEW_PROJECT_TYPE,
                            name=project_name,
                            field_value_pairs=basic_pairs
                        )
                        
                        new_project_id = None
                        if isinstance(create_response, dict):
                            new_project_id = create_response.get('data')
                        
                        if new_project_id:
                            logger.info(f"成功创建基本项目 {project_name}, 新 ID: {new_project_id}")
                            return MigrationResult(
                                old_project_id=old_project_id,
                                new_project_id=new_project_id,
                                success=True,
                                migrated_fields=[field.get('field_key') for field in basic_pairs],
                                error_message=f"仅迁移了基本字段，跳过了 Related features 和 role_owners"
                            )
                    except Exception as e3:
                        logger.error(f"项目 {project_name}: 基本项目创建也失败: {str(e3)}")
            
            # 所有尝试都失败
            error_msg = f"创建项目失败，未返回有效的项目 ID"
            logger.error(error_msg)
            return MigrationResult(
                old_project_id=old_project_id,
                new_project_id=None,
                success=False,
                error_message=error_msg
            )
    
    def migrate_single_project(self, old_project: Dict[str, Any]) -> MigrationResult:
        """
        迁移单个项目
        
        Args:
            old_project: 老项目数据
            
        Returns:
            迁移结果
        """
        old_project_id = old_project.get('id')
        project_name = old_project.get('name', f'Project_{old_project_id}')
        
        logger.info(f"开始迁移项目: {project_name} (ID: {old_project_id})")
        
        try:
            # 提取迁移数据
            migration_data = self.extract_migration_data(old_project)
            
            # 创建字段值对
            field_value_pairs = self.create_field_value_pairs(migration_data)
            
            # 尝试创建项目，支持失败重试
            return self._create_project_with_fallback(
                project_name=project_name,
                old_project_id=old_project_id,
                field_value_pairs=field_value_pairs,
                migration_data=migration_data
            )
                
        except Exception as e:
            error_msg = f"迁移项目 {project_name} 失败: {e}"
            logger.error(error_msg)
            return MigrationResult(
                old_project_id=old_project_id,
                new_project_id=None,
                success=False,
                error_message=error_msg
            )
    
    def migrate_all_projects(self, dry_run: bool = True, limit: Optional[int] = None) -> List[MigrationResult]:
        """
        迁移所有项目
        
        Args:
            dry_run: 是否为试运行（不执行实际迁移）
            limit: 限制迁移的项目数量（用于测试）
            
        Returns:
            迁移结果列表
        """
        logger.info(f"开始批量项目迁移 ({'试运行' if dry_run else '实际执行'})")
        
        # 获取所有老项目
        old_projects = self.get_old_projects()
        
        if limit:
            old_projects = old_projects[:limit]
            logger.info(f"限制迁移项目数量为: {limit}")
        
        results = []
        
        for i, old_project in enumerate(old_projects, 1):
            project_name = old_project.get('name', f'Project_{old_project.get("id")}')
            logger.info(f"处理项目 {i}/{len(old_projects)}: {project_name}")
            
            if dry_run:
                # 试运行 - 只提取数据，不实际创建
                migration_data = self.extract_migration_data(old_project)
                logger.info(f"试运行 - 将迁移字段: {list(migration_data.keys())}")
                results.append(MigrationResult(
                    old_project_id=old_project.get('id'),
                    new_project_id=None,
                    success=True,
                    migrated_fields=list(migration_data.keys())
                ))
            else:
                # 实际迁移
                result = self.migrate_single_project(old_project)
                results.append(result)
        
        return results
    
    def print_migration_summary(self, results: List[MigrationResult], dry_run: bool = True):
        """
        打印迁移摘要
        
        Args:
            results: 迁移结果列表
            dry_run: 是否为试运行
        """
        mode = "试运行" if dry_run else "实际执行"
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        print(f"\n" + "="*60)
        print(f"项目迁移摘要 ({mode})")
        print("="*60)
        print(f"总项目数: {total}")
        print(f"成功迁移: {successful}")
        print(f"迁移失败: {failed}")
        
        if not dry_run and successful > 0:
            print(f"\n新创建的项目 ID:")
            for result in results:
                if result.success and result.new_project_id:
                    print(f"  老项目 {result.old_project_id} -> 新项目 {result.new_project_id}")
        
        if failed > 0:
            print(f"\n失败的项目:")
            for result in results:
                if not result.success:
                    print(f"  项目 {result.old_project_id}: {result.error_message}")
        
        print("="*60)
    
    def analyze_migration_feasibility(self) -> Dict[str, Any]:
        """
        分析迁移可行性
        
        Returns:
            分析结果
        """
        logger.info("分析迁移可行性...")
        
        analysis = {
            "old_projects_count": 0,
            "sample_fields": [],
            "field_mapping_analysis": {},
            "potential_issues": []
        }
        
        try:
            # 获取老项目
            old_projects = self.get_old_projects()
            analysis["old_projects_count"] = len(old_projects)
            
            if old_projects:
                # 分析前几个项目的字段结构
                sample_project = old_projects[0]
                analysis["sample_fields"] = list(sample_project.keys())
                
                # 分析字段映射
                fields = sample_project.get('fields', [])
                for field in fields:
                    field_key = field.get('field_key')
                    if field_key in self.FIELD_MAPPING:
                        analysis["field_mapping_analysis"][field_key] = {
                            "maps_to": self.FIELD_MAPPING[field_key],
                            "has_value": bool(field.get('field_value'))
                        }
            
            # 检查工作项类型
            work_item_types = self.sdk.work_items.get_work_item_types()
            old_type_exists = any(wt.get('type_key') == self.OLD_PROJECT_TYPE for wt in work_item_types)
            new_type_exists = any(wt.get('type_key') == self.NEW_PROJECT_TYPE for wt in work_item_types)
            
            if not old_type_exists:
                analysis["potential_issues"].append(f"老项目类型 {self.OLD_PROJECT_TYPE} 不存在")
            if not new_type_exists:
                analysis["potential_issues"].append(f"新项目类型 {self.NEW_PROJECT_TYPE} 不存在")
            
        except Exception as e:
            analysis["potential_issues"].append(f"分析过程中出错: {e}")
        
        return analysis
