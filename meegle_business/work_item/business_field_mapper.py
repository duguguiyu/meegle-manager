#!/usr/bin/env python3
"""
Business 字段映射器

处理新旧项目类型之间的业务线字段兼容性问题
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class BusinessFieldMapper:
    """业务线字段映射器"""
    
    def __init__(self):
        """初始化映射器"""
        # 默认的业务线映射表（老业务线 -> 新业务线）
        self.business_mapping = {
            # 如果发现老项目有这些业务线值，映射到新的业务线值
            # 示例：
            # "eKYC": "Identity Verification",
            # "Risk Control": "Risk Management", 
            # "Data Platform": "Data Analytics",
        }
        
        # 默认业务线（当找不到映射时使用）
        self.default_business = None  # 设为 None 表示跳过该字段
        
        # 是否启用严格模式（找不到映射时抛出异常）
        self.strict_mode = False
    
    def set_business_mapping(self, mapping: Dict[str, str]):
        """
        设置业务线映射表
        
        Args:
            mapping: 老业务线到新业务线的映射字典
        """
        self.business_mapping = mapping
        logger.info(f"设置业务线映射: {mapping}")
    
    def set_default_business(self, default_business: Optional[str]):
        """
        设置默认业务线
        
        Args:
            default_business: 默认业务线值，None 表示跳过该字段
        """
        self.default_business = default_business
        logger.info(f"设置默认业务线: {default_business}")
    
    def set_strict_mode(self, strict: bool):
        """
        设置严格模式
        
        Args:
            strict: 是否启用严格模式
        """
        self.strict_mode = strict
        logger.info(f"设置严格模式: {strict}")
    
    def map_business_value(self, old_business: Optional[str]) -> Optional[str]:
        """
        映射业务线值
        
        Args:
            old_business: 老项目的业务线值
            
        Returns:
            映射后的新业务线值，None 表示跳过该字段
            
        Raises:
            ValueError: 严格模式下找不到映射时抛出异常
        """
        # 如果老业务线为空，返回 None（跳过字段）
        if not old_business:
            return None
        
        # 查找映射
        if old_business in self.business_mapping:
            new_business = self.business_mapping[old_business]
            logger.debug(f"业务线映射: '{old_business}' -> '{new_business}'")
            return new_business
        
        # 未找到映射的处理
        if self.strict_mode:
            raise ValueError(f"严格模式下找不到业务线 '{old_business}' 的映射")
        
        if self.default_business is not None:
            if self.default_business == "DIRECT_PASS":
                logger.info(f"业务线 '{old_business}' 未找到映射，直接传递原值")
                return old_business
            else:
                logger.warning(f"业务线 '{old_business}' 未找到映射，使用默认值: '{self.default_business}'")
                return self.default_business
        else:
            logger.info(f"业务线 '{old_business}' 未找到映射，跳过该字段")
            return None
    
    def should_include_business_field(self, mapped_business: Optional[str]) -> bool:
        """
        判断是否应该包含业务线字段
        
        Args:
            mapped_business: 映射后的业务线值
            
        Returns:
            是否应该包含该字段
        """
        return mapped_business is not None
    
    def get_mapping_stats(self, business_values: List[Optional[str]]) -> Dict[str, Any]:
        """
        获取映射统计信息
        
        Args:
            business_values: 业务线值列表
            
        Returns:
            映射统计信息
        """
        stats = {
            "total_values": len(business_values),
            "empty_values": 0,
            "mapped_values": 0,
            "unmapped_values": 0,
            "default_values": 0,
            "skipped_values": 0,
            "mapping_details": {}
        }
        
        for business in business_values:
            if not business:
                stats["empty_values"] += 1
                continue
                
            mapped = self.map_business_value(business)
            
            if business in self.business_mapping:
                stats["mapped_values"] += 1
                stats["mapping_details"][business] = mapped
            elif mapped == self.default_business:
                stats["default_values"] += 1
            elif mapped is None:
                stats["skipped_values"] += 1
            else:
                stats["unmapped_values"] += 1
        
        return stats


# 预定义的映射配置
COMMON_BUSINESS_MAPPINGS = {
    # eKYC 相关
    "eKYC": "Identity Verification",
    "Identity Verification": "Identity Verification", 
    "KYC": "Identity Verification",
    
    # 风控相关
    "Risk Control": "Risk Management",
    "Risk Management": "Risk Management",
    "Fraud Detection": "Risk Management",
    
    # 数据相关
    "Data Platform": "Data Analytics",
    "Data Analytics": "Data Analytics",
    "Big Data": "Data Analytics",
    
    # 信贷相关
    "Credit Scoring": "Credit Assessment",
    "Credit Assessment": "Credit Assessment",
    "Lending": "Credit Assessment",
}
