# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""Core Layer — 数据模型与基础设施。"""

from src.core.models import (
    TemplateBlock, Section, ContextDoc, TreeNode,
    VersionMeta, SectionFile, StagingOp, StagingDoc,
    TemplateSectionRef, Template, Prompt,
    SectionData, VersionEntry, DraftChange, DraftState, TemplateData,
)
from src.core.sentinel_parser import SentinelParser
from src.core.file_system_ops import FileSystemOps
from src.core.backup_engine import BackupEngine

__all__ = [
    'TemplateBlock',
    'Section',
    'ContextDoc',
    'TreeNode',
    'VersionMeta',
    'SectionFile',
    'StagingOp',
    'StagingDoc',
    'TemplateSectionRef',
    'Template',
    'Prompt',
    'SectionData',
    'VersionEntry',
    'DraftChange',
    'DraftState',
    'TemplateData',
    'SentinelParser',
    'FileSystemOps',
    'BackupEngine',
]
