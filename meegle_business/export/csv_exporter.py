"""
CSV exporter for timeline data
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from meegle_business.timeline.models import TimelineEntry, TimelineData
from config.settings import get_export_config

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    CSV exporter for timeline data
    
    Provides methods to export timeline data in CSV format
    compatible with Meegle templates
    """
    
    def __init__(self, output_dir: Optional[str] = None, encoding: str = None):
        """
        Initialize CSV Exporter
        
        Args:
            output_dir: Output directory path (uses config default if not provided)
            encoding: File encoding (uses config default if not provided)
        """
        export_config = get_export_config()
        
        self.output_dir = Path(output_dir or export_config['output_dir'])
        self.encoding = encoding or export_config['csv_encoding']
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # CSV headers (English)
        self.headers_en = [
            '', 'Project code', 'Project type', 'Project status', 'Project name',
            'Activity code', 'Market /region', 'Category / function', 'Entity',
            'Member email', 'Date', 'Work load / hours charged', 'Description / comments',
            'Submission date', "Manager's sign-off", 'Remark', '', '', ''
        ]
        
        # CSV headers (Chinese)
        self.headers_cn = [
            '', '项目代码', '项目类型', '项目状态', '项目描述',
            '活动代码', '市场', '产品线', '事业部',
            '员工邮箱', '日期', '耗时', '工作内容具体描述',
            '提交日期', '审批记录', '备注', '', '', ''
        ]
        
        # Example row
        self.example_row = [
            '', 'e.g. PRD-PH-ADVI-ICS-001-V3', 'Project / Product',
            '[Project status]', '[Project description]',
            'Development / Maintenance', 'Region', 'Function',
            'Entity', '[Email]', '[Date]', '[Hours]', '[Description]',
            '[Submit date]', '[Manager signoff]', '[Remark]', '', '', ''
        ]
    
    def export_timeline_to_csv(self, timeline_data: TimelineData, 
                              filename: str) -> Path:
        """
        Export timeline data to CSV file
        
        Args:
            timeline_data: TimelineData object to export
            filename: Base filename (without extension)
            
        Returns:
            Path to the created CSV file
            
        Raises:
            Exception: If export fails
        """
        if not timeline_data.entries:
            logger.warning(f"No data to export for {filename}")
            # Still create an empty file
            filepath = self._generate_filepath(filename)
            self._create_empty_csv(filepath)
            return filepath
        
        filepath = self._generate_filepath(filename)
        
        logger.info(f"Exporting {len(timeline_data.entries)} entries to {filepath}")
        
        try:
            with open(filepath, 'w', newline='', encoding=self.encoding) as f:
                writer = csv.writer(f)
                
                # Write headers and template rows
                self._write_csv_headers(writer)
                
                # Write data rows
                valid_entries = 0
                for entry in timeline_data.entries:
                    if entry.is_valid():
                        writer.writerow(entry.get_csv_row())
                        valid_entries += 1
                    else:
                        logger.warning(f"Skipping invalid entry: {entry}")
                
                logger.info(f"Successfully exported {valid_entries} valid entries to {filepath}")
                
        except Exception as e:
            logger.error(f"Failed to export timeline to CSV: {e}")
            raise
        
        return filepath
    
    def export_entries_to_csv(self, entries: List[TimelineEntry], 
                             filename: str) -> Path:
        """
        Export list of timeline entries to CSV
        
        Args:
            entries: List of TimelineEntry objects
            filename: Base filename (without extension)
            
        Returns:
            Path to the created CSV file
        """
        timeline_data = TimelineData(entries=entries)
        return self.export_timeline_to_csv(timeline_data, filename)
    
    def _generate_filepath(self, filename: str) -> Path:
        """
        Generate full file path with timestamp
        
        Args:
            filename: Base filename
            
        Returns:
            Path object with full file path
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        full_filename = f"{filename}_{timestamp}.csv"
        return self.output_dir / full_filename
    
    def _write_csv_headers(self, writer: csv.writer):
        """
        Write CSV headers and template rows
        
        Args:
            writer: CSV writer object
        """
        # Empty row
        writer.writerow([''] * len(self.headers_en))
        
        # English headers
        writer.writerow(self.headers_en)
        
        # Chinese headers  
        writer.writerow(self.headers_cn)
        
        # Example row
        writer.writerow(self.example_row)
    
    def _create_empty_csv(self, filepath: Path):
        """
        Create empty CSV file with headers only
        
        Args:
            filepath: Path to create CSV file
        """
        try:
            with open(filepath, 'w', newline='', encoding=self.encoding) as f:
                writer = csv.writer(f)
                self._write_csv_headers(writer)
            
            logger.info(f"Created empty CSV file: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to create empty CSV file: {e}")
            raise
    
    def export_multiple_timelines(self, timeline_dict: dict, 
                                 base_filename: str) -> List[Path]:
        """
        Export multiple timeline datasets
        
        Args:
            timeline_dict: Dictionary with keys as suffixes and TimelineData as values
            base_filename: Base filename for all exports
            
        Returns:
            List of created file paths
        """
        created_files = []
        
        for suffix, timeline_data in timeline_dict.items():
            filename = f"{base_filename}_{suffix}"
            try:
                filepath = self.export_timeline_to_csv(timeline_data, filename)
                created_files.append(filepath)
            except Exception as e:
                logger.error(f"Failed to export {filename}: {e}")
                continue
        
        logger.info(f"Exported {len(created_files)} timeline files")
        return created_files
    
    def get_export_summary(self, timeline_data: TimelineData) -> dict:
        """
        Get export summary information
        
        Args:
            timeline_data: TimelineData to summarize
            
        Returns:
            Dictionary with summary information
        """
        summary = timeline_data.get_summary()
        
        # Add export-specific info
        summary.update({
            'output_dir': str(self.output_dir),
            'encoding': self.encoding,
            'export_timestamp': datetime.now().isoformat()
        })
        
        return summary 