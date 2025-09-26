"""
Feature Reassignment Tool for Project Migration

This module provides functionality to reassign features from old projects to new projects
after project migration. It processes features from a specified view and updates their
project associations based on the old project names.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from meegle_sdk import MeegleSDK

logger = logging.getLogger(__name__)


@dataclass
class ReassignmentResult:
    """Result of feature reassignment operation"""
    feature_id: int
    feature_name: str
    old_project_name: Optional[str]
    new_project_id: Optional[int]
    success: bool
    error_message: Optional[str] = None


class FeatureReassignment:
    """
    Tool for reassigning features from old projects to new projects
    
    This class handles the process of:
    1. Getting features from a specified view
    2. Analyzing their current project associations
    3. Finding corresponding new projects based on old project names
    4. Updating features to point to new projects
    """
    
    def __init__(self, sdk: MeegleSDK):
        """
        Initialize Feature Reassignment tool
        
        Args:
            sdk: Meegle SDK instance
        """
        self.sdk = sdk
        self.old_project_type = "642ec373f4af608bb3cb1c90"
        self.new_project_type = "68afee24c92ef633f847d304"
        
        # Cache for project mappings
        self._old_projects_cache = None  # ID-based cache
        self._old_projects_name_cache = None  # Name-based cache
        self._new_projects_cache = None  # Name-based cache
        self._project_name_mapping = None
    
    def get_features_from_view(self, view_id: str) -> List[Dict[str, Any]]:
        """
        Get all feature work items from a specified view
        
        Args:
            view_id: View ID to get features from
            
        Returns:
            List of feature work items
        """
        logger.info(f"获取视图 {view_id} 中的所有工作项...")
        
        # Get all work item IDs from the view
        work_item_ids = self.sdk.work_items.get_all_work_items_in_view(view_id)
        logger.info(f"视图中找到 {len(work_item_ids)} 个工作项")
        
        if not work_item_ids:
            logger.warning("视图中没有找到工作项")
            return []
        
        # Get detailed information for all work items
        # We'll process them in batches to avoid API limits
        batch_size = 50
        all_features = []
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}: {len(batch_ids)} 个工作项")
            
            try:
                # Get work item details for this batch
                features_data = self.sdk.work_items.get_work_item_details(
                    work_item_ids=batch_ids,
                    work_item_type_key="story"  # Assuming features are of type "story"
                )
                
                if features_data and 'data' in features_data:
                    batch_features = features_data['data']
                    logger.info(f"批次中获取到 {len(batch_features)} 个 feature 详情")
                    all_features.extend(batch_features)
                else:
                    logger.warning(f"批次 {i//batch_size + 1} 没有返回有效数据")
                    
            except Exception as e:
                logger.error(f"获取批次 {i//batch_size + 1} 详情失败: {e}")
                continue
        
        logger.info(f"总共获取到 {len(all_features)} 个 feature")
        return all_features
    
    def analyze_feature_project_associations(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze project associations in features
        
        Args:
            features: List of feature work items
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("分析 feature 的项目关联...")
        
        project_field_counts = {}
        features_with_projects = []
        features_without_projects = []
        project_names = set()
        
        for feature in features:
            feature_id = feature.get('id')
            feature_name = feature.get('name', f'Feature_{feature_id}')
            fields = feature.get('fields', [])
            
            # Look for project-related fields
            project_info = None
            for field in fields:
                field_key = field.get('field_key', '')
                
                # Check various possible project field keys
                # Based on analysis, field_c0a56e contains the old project ID
                if field_key in ['field_c0a56e', 'field_f7f3d2', 'field_696f08'] or \
                   any(proj_key in field_key.lower() for proj_key in ['project']):
                    field_value = field.get('field_value')
                    if field_value:
                        project_field_counts[field_key] = project_field_counts.get(field_key, 0) + 1
                        
                        # Try to extract project name from field value
                        project_name = self._extract_project_name_from_field(field_value, field_key)
                        if project_name:
                            project_info = {
                                'field_key': field_key,
                                'field_value': field_value,
                                'project_name': project_name
                            }
                            project_names.add(project_name)
                            break
            
            if project_info:
                features_with_projects.append({
                    'feature_id': feature_id,
                    'feature_name': feature_name,
                    'project_info': project_info
                })
            else:
                features_without_projects.append({
                    'feature_id': feature_id,
                    'feature_name': feature_name
                })
        
        analysis = {
            'total_features': len(features),
            'features_with_projects': len(features_with_projects),
            'features_without_projects': len(features_without_projects),
            'project_field_counts': project_field_counts,
            'unique_project_names': list(project_names),
            'features_with_project_data': features_with_projects,
            'features_without_project_data': features_without_projects
        }
        
        logger.info(f"分析完成:")
        logger.info(f"  总 feature 数: {analysis['total_features']}")
        logger.info(f"  有项目关联的: {analysis['features_with_projects']}")
        logger.info(f"  无项目关联的: {analysis['features_without_projects']}")
        logger.info(f"  唯一项目名称: {len(analysis['unique_project_names'])}")
        logger.info(f"  项目字段统计: {analysis['project_field_counts']}")
        
        return analysis
    
    def _extract_project_name_from_field(self, field_value: Any, field_key: str) -> Optional[str]:
        """
        Extract project name from field value
        
        Args:
            field_value: Field value that may contain project information
            field_key: The field key to help determine how to process the value
            
        Returns:
            Project name if found, None otherwise
        """
        if not field_value:
            return None
        
        # Handle field_c0a56e which contains old project ID
        if field_key == 'field_c0a56e':
            try:
                project_id = int(field_value)
                # Look up project name by ID
                return self._get_project_name_by_id(project_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid project ID in {field_key}: {field_value}")
                return None
        
        # Handle other field value formats
        if isinstance(field_value, str):
            # If it's a string, it might be a project name directly
            return field_value.strip()
        elif isinstance(field_value, list) and field_value:
            # If it's a list, take the first item
            first_item = field_value[0]
            if isinstance(first_item, dict):
                # Look for common project name keys
                for key in ['name', 'label', 'title', 'text']:
                    if key in first_item:
                        return str(first_item[key]).strip()
                # If no standard key, return the first string value found
                for value in first_item.values():
                    if isinstance(value, str) and value.strip():
                        return value.strip()
            elif isinstance(first_item, str):
                return first_item.strip()
        elif isinstance(field_value, dict):
            # If it's a dict, look for project name keys
            for key in ['name', 'label', 'title', 'text']:
                if key in field_value:
                    return str(field_value[key]).strip()
        
        return None
    
    def _get_project_name_by_id(self, project_id: int) -> Optional[str]:
        """
        Get project name by project ID
        
        Args:
            project_id: Project ID to look up
            
        Returns:
            Project name if found, None otherwise
        """
        # Ensure old projects are cached
        if self._old_projects_cache is None:
            logger.info("缓存老项目列表...")
            old_projects = self.sdk.work_items.get_all_work_items([self.old_project_type])
            self._old_projects_cache = {proj.get('id'): proj for proj in old_projects}
            # Also create a name-based cache for mapping
            self._old_projects_name_cache = {proj.get('name'): proj for proj in old_projects}
        
        # Look up project by ID
        project = self._old_projects_cache.get(project_id)
        if project:
            return project.get('name')
        else:
            logger.warning(f"未找到 ID 为 {project_id} 的项目")
            return None
    
    def build_project_name_mapping(self) -> Dict[str, int]:
        """
        Build mapping from old project names to new project IDs
        
        Returns:
            Dictionary mapping old project names to new project IDs
        """
        logger.info("构建项目名称映射...")
        
        if self._project_name_mapping is not None:
            logger.info("使用缓存的项目名称映射")
            return self._project_name_mapping
        
        # Get old projects (ensure we have the name-based cache)
        if self._old_projects_cache is None:
            logger.info("获取老项目列表...")
            old_projects = self.sdk.work_items.get_all_work_items([self.old_project_type])
            self._old_projects_cache = {proj.get('id'): proj for proj in old_projects}
            self._old_projects_name_cache = {proj.get('name'): proj for proj in old_projects}
            logger.info(f"找到 {len(old_projects)} 个老项目")
        
        # Get new projects
        if self._new_projects_cache is None:
            logger.info("获取新项目列表...")
            new_projects = self.sdk.work_items.get_all_work_items([self.new_project_type])
            self._new_projects_cache = {proj.get('name'): proj for proj in new_projects}
            logger.info(f"找到 {len(new_projects)} 个新项目")
        
        # Build name mapping
        mapping = {}
        for old_name in self._old_projects_name_cache.keys():
            if old_name in self._new_projects_cache:
                new_project = self._new_projects_cache[old_name]
                new_project_id = new_project.get('id')
                if new_project_id:
                    mapping[old_name] = new_project_id
                    logger.debug(f"映射: {old_name} -> {new_project_id}")
        
        self._project_name_mapping = mapping
        logger.info(f"构建完成，找到 {len(mapping)} 个项目映射")
        
        return mapping
    
    def reassign_features_to_new_projects(self, view_id: str, dry_run: bool = True) -> List[ReassignmentResult]:
        """
        Reassign features from old projects to new projects
        
        Args:
            view_id: View ID containing features to reassign
            dry_run: If True, only analyze without making changes
            
        Returns:
            List of reassignment results
        """
        logger.info(f"开始重新分配 feature 到新项目 (dry_run={dry_run})...")
        
        # Step 1: Get features from view
        features = self.get_features_from_view(view_id)
        if not features:
            logger.warning("没有找到 feature，停止处理")
            return []
        
        # Step 2: Analyze project associations
        analysis = self.analyze_feature_project_associations(features)
        features_with_projects = analysis['features_with_project_data']
        
        if not features_with_projects:
            logger.warning("没有找到有项目关联的 feature")
            return []
        
        # Step 3: Build project name mapping
        project_mapping = self.build_project_name_mapping()
        if not project_mapping:
            logger.warning("没有找到项目名称映射")
            return []
        
        # Step 4: Process each feature
        results = []
        successful_reassignments = 0
        
        for feature_data in features_with_projects:
            feature_id = feature_data['feature_id']
            feature_name = feature_data['feature_name']
            project_info = feature_data['project_info']
            old_project_name = project_info['project_name']
            
            logger.info(f"处理 feature: {feature_name} (ID: {feature_id})")
            logger.info(f"  当前关联项目: {old_project_name}")
            
            # Check if we have a mapping for this project
            if old_project_name not in project_mapping:
                error_msg = f"未找到项目 '{old_project_name}' 的新项目映射"
                logger.warning(f"  {error_msg}")
                results.append(ReassignmentResult(
                    feature_id=feature_id,
                    feature_name=feature_name,
                    old_project_name=old_project_name,
                    new_project_id=None,
                    success=False,
                    error_message=error_msg
                ))
                continue
            
            new_project_id = project_mapping[old_project_name]
            logger.info(f"  新项目 ID: {new_project_id}")
            
            if dry_run:
                logger.info("  [DRY RUN] 跳过实际更新")
                results.append(ReassignmentResult(
                    feature_id=feature_id,
                    feature_name=feature_name,
                    old_project_name=old_project_name,
                    new_project_id=new_project_id,
                    success=True,
                    error_message="DRY RUN - 未执行实际更新"
                ))
                successful_reassignments += 1
            else:
                # Perform actual update
                try:
                    # Determine the correct field key based on the original field
                    original_field_key = project_info['field_key']
                    
                    if original_field_key == 'field_c0a56e':
                        # field_c0a56e contains old project ID, we update field_df5ff0 with new project ID
                        update_field_key = "field_df5ff0"
                        update_value = new_project_id
                    elif original_field_key == 'field_f7f3d2':
                        # Based on migration logic, old field_f7f3d2 maps to new field_696f08
                        update_field_key = "field_696f08"
                        update_value = str(new_project_id)
                    else:
                        # Default case - update the same field
                        update_field_key = original_field_key
                        update_value = str(new_project_id)
                    
                    # Update the feature
                    logger.info(f"  更新 feature {feature_id} 的项目关联 ({update_field_key})...")
                    self.sdk.workflows.update_work_item(
                        work_item_id=feature_id,
                        work_item_type_key="story",
                        update_fields=[{
                            "field_key": update_field_key,
                            "field_value": update_value
                        }]
                    )
                    
                    logger.info(f"  ✅ 成功更新 feature {feature_id}")
                    results.append(ReassignmentResult(
                        feature_id=feature_id,
                        feature_name=feature_name,
                        old_project_name=old_project_name,
                        new_project_id=new_project_id,
                        success=True
                    ))
                    successful_reassignments += 1
                    
                except Exception as e:
                    error_msg = f"更新失败: {str(e)}"
                    logger.error(f"  ❌ {error_msg}")
                    results.append(ReassignmentResult(
                        feature_id=feature_id,
                        feature_name=feature_name,
                        old_project_name=old_project_name,
                        new_project_id=new_project_id,
                        success=False,
                        error_message=error_msg
                    ))
        
        # Summary
        logger.info(f"重新分配完成:")
        logger.info(f"  处理的 feature 数: {len(results)}")
        logger.info(f"  成功重新分配: {successful_reassignments}")
        logger.info(f"  失败数: {len(results) - successful_reassignments}")
        
        return results
    
    def print_reassignment_summary(self, results: List[ReassignmentResult]):
        """
        Print summary of reassignment results
        
        Args:
            results: List of reassignment results
        """
        print("=" * 80)
        print("Feature 重新分配结果汇总")
        print("=" * 80)
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"总处理 feature 数: {len(results)}")
        print(f"成功重新分配: {len(successful)}")
        print(f"失败数: {len(failed)}")
        print()
        
        if successful:
            print("✅ 成功重新分配的 feature:")
            for result in successful:
                print(f"  • {result.feature_name} (ID: {result.feature_id})")
                print(f"    {result.old_project_name} -> 新项目 ID {result.new_project_id}")
                if result.error_message:
                    print(f"    注意: {result.error_message}")
            print()
        
        if failed:
            print("❌ 重新分配失败的 feature:")
            for result in failed:
                print(f"  • {result.feature_name} (ID: {result.feature_id})")
                print(f"    项目: {result.old_project_name}")
                print(f"    错误: {result.error_message}")
            print()
        
        print("=" * 80)
