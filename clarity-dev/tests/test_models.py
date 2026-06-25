"""
数据模型实例化测试 — IT-01-V2 DT-11。

每个数据模型类至少一个实例化 + 字段断言（≥12条）。
"""

import pytest
from src.core.models import (
    TemplateBlock,
    Section,
    ContextDoc,
    TreeNode,
    VersionMeta,
    SectionFile,
    StagingOp,
    StagingDoc,
    TemplateSectionRef,
    Template,
    Prompt,
)


# ── DT-03: TemplateBlock ────────────────────────────────────

class TestTemplateBlock:
    def test_fixed_block(self):
        """DT-03: FIXED 类型块实例化"""
        b = TemplateBlock(type='FIXED', content='# 项目背景')
        assert b.type == 'FIXED'
        assert b.content == '# 项目背景'

    def test_project_block(self):
        """DT-03: PROJECT 类型块实例化"""
        b = TemplateBlock(type='PROJECT', content='## 当前任务')
        assert b.type == 'PROJECT'
        assert b.content == '## 当前任务'


# ── DT-03: Section ──────────────────────────────────────────

class TestSection:
    def test_basic_section(self):
        """DT-03: Section 基本实例化"""
        s = Section(id='A', title='项目背景与角色', raw_content='# A\n...')
        assert s.id == 'A'
        assert s.title == '项目背景与角色'
        assert s.is_active is True
        assert s.fixed_blocks == []
        assert s.project_blocks == []

    def test_section_with_blocks(self):
        """DT-03: Section 含模板块"""
        fb = TemplateBlock(type='FIXED', content='固定内容')
        pb = TemplateBlock(type='PROJECT', content='项目内容')
        s = Section(id='B', title='任务窗口',
                    fixed_blocks=[fb], project_blocks=[pb])
        assert len(s.fixed_blocks) == 1
        assert len(s.project_blocks) == 1
        assert s.fixed_blocks[0].type == 'FIXED'
        assert s.project_blocks[0].type == 'PROJECT'


# ── DT-03: ContextDoc ───────────────────────────────────────

class TestContextDoc:
    def test_empty_doc(self):
        """DT-03: 空 ContextDoc"""
        doc = ContextDoc()
        assert doc.sections == []
        assert doc.template_name is None

    def test_doc_with_sections(self):
        """DT-03: ContextDoc 含多个段"""
        s1 = Section(id='A', title='背景')
        s2 = Section(id='B', title='任务')
        doc = ContextDoc(sections=[s1, s2], template_name='开发模板')
        assert len(doc.sections) == 2
        assert doc.template_name == '开发模板'


# ── DT-04: TreeNode ─────────────────────────────────────────

class TestTreeNode:
    def test_file_node(self):
        """DT-04: 文件节点（含 V2 新增 description）"""
        n = TreeNode(name='readme.md', path='readme.md', is_dir=False,
                     description='项目说明文件')
        assert n.name == 'readme.md'
        assert n.is_dir is False
        assert n.is_factory is False
        assert n.description == '项目说明文件'

    def test_dir_node(self):
        """DT-04: 目录节点含子节点"""
        child = TreeNode(name='a.md', path='docs/a.md', is_dir=False)
        n = TreeNode(name='docs', path='docs', is_dir=True, children=[child])
        assert n.is_dir is True
        assert len(n.children) == 1
        assert n.children[0].name == 'a.md'


# ── DT-05: VersionMeta ──────────────────────────────────────

class TestVersionMeta:
    def test_section_version(self):
        """DT-05: VersionMeta section 类型（无 id 字段）"""
        v = VersionMeta(
            target_type='section', target_id='B', version=3,
            storage_path='sections/.versions/任务窗口.v3.md',
            description='新增备忘区规范', created_at='2026-06-20T10:00:00',
            baselines=['v1-出厂基线'],
        )
        assert v.target_type == 'section'
        assert v.target_id == 'B'
        assert v.version == 3
        assert v.description == '新增备忘区规范'
        assert 'v1-出厂基线' in v.baselines
        # 关键验证：无 id 字段，无 note 字段（v4 已废除）
        assert not hasattr(v, 'id')
        assert not hasattr(v, 'note')

    def test_prompt_version(self):
        """DT-05: VersionMeta prompt 类型（V2 新增 target_type）"""
        v = VersionMeta(
            target_type='prompt', target_id='标准开局', version=2,
            storage_path='prompts/开局/.versions/标准开局.v2.md',
            description='措辞调整', created_at='2026-06-20T11:00:00',
            content='阅读 cos-context，开局。',
        )
        assert v.target_type == 'prompt'
        assert v.target_id == '标准开局'
        assert v.content == '阅读 cos-context，开局。'

    def test_file_version(self):
        """DT-05: VersionMeta file 类型"""
        v = VersionMeta(
            target_type='file', target_id='core/README.md', version=1,
            storage_path='backups/files/core/README.md/v1.md',
            description='初始备份', created_at='2026-06-20T09:00:00',
        )
        assert v.target_type == 'file'
        assert v.target_id == 'core/README.md'
        assert v.content is None


# ── DT-06: SectionFile ──────────────────────────────────────

class TestSectionFile:
    def test_basic(self):
        """DT-06: SectionFile 含 content/notes"""
        sf = SectionFile(
            name='项目背景与角色.md',
            content='## 项目背景\n这是背景内容。',
            notes='v1: 初始版本',
        )
        assert sf.name == '项目背景与角色.md'
        assert '项目背景' in sf.content
        assert sf.notes == 'v1: 初始版本'
        assert sf.version is None

    def test_with_version(self):
        """DT-06: SectionFile 关联当前版本"""
        ver = VersionMeta(
            target_type='section', target_id='A', version=2,
            storage_path='sections/.versions/背景.v2.md',
            description='补充角色', created_at='2026-06-20T10:00:00',
        )
        sf = SectionFile(name='背景.md', content='...', notes='v2',
                         version=ver)
        assert sf.version is not None
        assert sf.version.version == 2


# ── DT-07: StagingOp / StagingDoc ───────────────────────────

class TestStagingOp:
    def test_change_version_op(self):
        """DT-07: change_version 操作"""
        op = StagingOp(op='change_version', target='§B',
                       content='# 任务窗口\n新内容')
        assert op.op == 'change_version'
        assert op.target == '§B'
        assert op.adapt is False
        assert op.position is None

    def test_deactivate_op(self):
        """DT-07: deactivate 操作含 position"""
        op = StagingOp(op='deactivate', target='§C', position='after §B')
        assert op.op == 'deactivate'
        assert op.position == 'after §B'
        assert op.content is None


class TestStagingDoc:
    def test_pending_doc(self):
        """DT-07: StagingDoc pending 状态含多 ops"""
        op1 = StagingOp(op='change_version', target='§B', content='新§B')
        op2 = StagingOp(op='deactivate', target='§C')
        doc = StagingDoc(status='pending', ops=[op1, op2])
        assert doc.status == 'pending'
        assert len(doc.ops) == 2
        assert doc.ops[0].op == 'change_version'


# ── DT-08: TemplateSectionRef / Template ────────────────────

class TestTemplateSectionRef:
    def test_basic(self):
        """DT-08: TemplateSectionRef 基本字段"""
        ref = TemplateSectionRef(
            section_name='项目背景与角色.md', version=12, order=1,
        )
        assert ref.section_name == '项目背景与角色.md'
        assert ref.version == 12
        assert ref.order == 1
        assert ref.is_active is True


class TestTemplate:
    def test_basic(self):
        """DT-08: Template 含段引用列表"""
        ref1 = TemplateSectionRef(section_name='背景.md', version=12, order=1)
        ref2 = TemplateSectionRef(section_name='任务窗口.md', version=8, order=2)
        t = Template(
            name='默认开发模板',
            description='适用于软件开发的场景模板',
            sections=[ref1, ref2],
        )
        assert t.name == '默认开发模板'
        assert len(t.sections) == 2
        assert t.sections[0].section_name == '背景.md'
        assert t.sections[1].version == 8


# ── DT-09 / IT-13a: Prompt v3 ────────────────────────────────

class TestPrompt:
    def test_basic(self):
        """IT-13a: Prompt v3 基本实例化"""
        p = Prompt(
            description='标准开局措辞',
            content='阅读 cos-context，开局。',
            created_at='2026-06-21T10:00:00Z',
        )
        assert p.description == '标准开局措辞'
        assert p.content == '阅读 cos-context，开局。'
        assert p.created_at == '2026-06-21T10:00:00Z'
        # v3 无 category / versions 字段
        assert not hasattr(p, 'category')
        assert not hasattr(p, 'versions')

    def test_with_created_at(self):
        """IT-13a: Prompt v3 created_at 为 ISO 8601 时间戳"""
        p = Prompt(
            description='测试',
            content='正文',
            created_at='2026-06-21T00:00:00Z',
        )
        assert '2026-06-21' in p.created_at
        assert 'T' in p.created_at
