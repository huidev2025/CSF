"""
SentinelParser V2 测试 — IT-02-V2 DT-08~11。

≥20条测试：context解析≥8 + 段文件解析≥5 + staging解析≥5 + MSG计数器≥2
"""

import pytest
from pathlib import Path
import tempfile

from src.core.sentinel_parser import SentinelParser
from src.core.models import (
    ContextDoc, Section, SectionFile, StagingDoc, StagingOp,
)


# ── 夹具 ────────────────────────────────────────────────────

SAMPLE_CONTEXT = """<!-- @SECTION:A -->
# 项目背景与角色

<!-- @TEMPLATE:FIXED -->
这是框架固定内容。
<!-- @/TEMPLATE:FIXED -->

<!-- @TEMPLATE:PROJECT -->
这是项目可变内容。
<!-- @/TEMPLATE:PROJECT -->
<!-- @/SECTION:A -->

<!-- @SECTION:B -->
## 任务窗口

当前任务列表：IT-01, IT-02
<!-- @/SECTION:B -->

<!-- @SECTION:INBOX -->
### 收件箱

<!-- @MSG:1 -->
消息内容
<!-- @/MSG:1 -->

<!-- @MSG:NEXT:10 -->
<!-- @/SECTION:INBOX -->"""

SAMPLE_SECTION_FILE = """# 项目背景与角色

> 段ID: A
> 创建: 2026-06-20

<!-- @SEC:CONTENT -->
## 项目背景

这是项目背景内容。

<!-- @TEMPLATE:FIXED -->
框架内容块
<!-- @/TEMPLATE:FIXED -->
<!-- @/SEC:CONTENT -->

<!-- @SEC:NOTES -->
v1: 初始版本
v2: 补充角色描述
<!-- @/SEC:NOTES -->"""

SAMPLE_STAGING = """# Clarity Staging — 待处理指令

status: pending
> 写入时间：2026-06-20T15:00:00

<!-- @STAGING:1 op="change_version" target="§B" -->
## 操作1：换版本 §B

将 cos-context.md 中 §B 的全部内容替换为：

<!-- @STG:CONTENT:START -->
## §B 任务窗口

新版本内容
<!-- @STG:CONTENT:END -->
<!-- @/STAGING:1 -->

<!-- @STAGING:2 op="deactivate" target="§INBOX" -->
## 操作2：撤下 §INBOX
<!-- @/STAGING:2 -->"""


@pytest.fixture
def parser():
    return SentinelParser()


def _write_temp(name: str, content: str) -> str:
    p = Path(tempfile.gettempdir()) / name
    p.write_text(content, encoding='utf-8')
    return str(p)


# ── DT-08: Context 解析测试（≥8条）──────────────────────────

class TestContextParsing:
    def test_single_section(self, parser):
        """DT-08: 单段解析"""
        text = """<!-- @SECTION:A -->
# 标题
内容文本
<!-- @/SECTION:A -->"""
        doc = parser.parse_context_text(text)
        assert len(doc.sections) == 1
        assert doc.sections[0].id == 'A'
        assert doc.sections[0].title == '标题'

    def test_multi_section(self, parser):
        """DT-08: 多段解析"""
        doc = parser.parse_context_text(SAMPLE_CONTEXT)
        assert len(doc.sections) == 3
        ids = [s.id for s in doc.sections]
        assert 'A' in ids
        assert 'B' in ids
        assert 'INBOX' in ids

    def test_section_with_fixed_and_project(self, parser):
        """DT-08: 段含 FIXED + PROJECT 块"""
        doc = parser.parse_context_text(SAMPLE_CONTEXT)
        sec_a = doc.sections[0]
        assert len(sec_a.fixed_blocks) == 1
        assert len(sec_a.project_blocks) == 1
        assert sec_a.fixed_blocks[0].type == 'FIXED'
        assert '框架固定内容' in sec_a.fixed_blocks[0].content
        assert sec_a.project_blocks[0].type == 'PROJECT'
        assert '项目可变内容' in sec_a.project_blocks[0].content

    def test_assemble_roundtrip(self, parser):
        """DT-08: assemble_context 往返一致"""
        doc = parser.parse_context_text(SAMPLE_CONTEXT)
        assembled = parser.assemble_context(doc)
        doc2 = parser.parse_context_text(assembled)
        assert len(doc2.sections) == len(doc.sections)
        for i in range(len(doc.sections)):
            assert doc2.sections[i].id == doc.sections[i].id

    def test_get_section(self, parser):
        """DT-08: get_section 提取指定段"""
        doc = parser.parse_context_text(SAMPLE_CONTEXT)
        sec = parser.get_section(doc, 'B')
        assert sec is not None
        assert sec.id == 'B'
        assert '任务窗口' in sec.title

    def test_get_section_not_found(self, parser):
        """DT-08: get_section 段不存在"""
        doc = parser.parse_context_text(SAMPLE_CONTEXT)
        sec = parser.get_section(doc, 'Z')
        assert sec is None

    def test_replace_section(self, parser):
        """DT-08: replace_section 替换后验证"""
        doc = parser.parse_context_text(SAMPLE_CONTEXT)
        new_content = '<!-- @SECTION:B -->\n## 新任务\n新内容\n<!-- @/SECTION:B -->'
        result = parser.replace_section(doc, 'B', new_content)
        assert '新任务' in result
        assert '<!-- @SECTION:B -->' in result

    def test_empty_file_tolerance(self, parser):
        """DT-08: 空文件容忍"""
        doc = parser.parse_context_text('')
        assert len(doc.sections) == 0

    def test_no_closing_sentinel_fallback(self, parser):
        """DT-08: 缺闭合哨兵的回退逻辑"""
        text = """<!-- @SECTION:A -->
# 标题
无闭合哨兵的内容
<!-- @SECTION:B -->
# 第二个段
<!-- @/SECTION:B -->"""
        doc = parser.parse_context_text(text)
        assert len(doc.sections) == 2
        assert doc.sections[0].id == 'A'

    def test_context_doc_template_name_none(self, parser):
        """DT-08: ContextDoc template_name 默认为 None"""
        doc = parser.parse_context_text(SAMPLE_CONTEXT)
        assert doc.template_name is None


# ── DT-09: 段文件解析测试（≥5条）────────────────────────────

class TestSectionFileParsing:
    def test_normal_section_file(self, parser):
        """DT-09: 正常段文件解析"""
        f = _write_temp('项目背景.v3.md', SAMPLE_SECTION_FILE)
        sf = parser.parse_section_file(f)
        assert sf.name == '项目背景.v3.md'
        assert '项目背景' in sf.content
        assert 'v1: 初始版本' in sf.notes
        assert sf.version is not None
        assert sf.version.version == 3

    def test_section_file_no_version(self, parser):
        """DT-09: 无版本号段文件"""
        content = """<!-- @SEC:CONTENT -->
内容
<!-- @/SEC:CONTENT -->
<!-- @SEC:NOTES -->
备注
<!-- @/SEC:NOTES -->"""
        f = _write_temp('新段.md', content)
        sf = parser.parse_section_file(f)
        assert sf.name == '新段.md'
        assert sf.version is None

    def test_section_file_no_header(self, parser):
        """DT-09: 无文件头段文件（容忍）"""
        content = """<!-- @SEC:CONTENT -->
直接内容区
<!-- @/SEC:CONTENT -->
<!-- @SEC:NOTES -->
直接笔记区
<!-- @/SEC:NOTES -->"""
        f = _write_temp('无头段.md', content)
        sf = parser.parse_section_file(f)
        assert '直接内容区' in sf.content
        assert '直接笔记区' in sf.notes

    def test_section_file_content_with_fixed(self, parser):
        """DT-09: 内容区含 FIXED 块"""
        sf = parser.parse_section_file(
            _write_temp('含fixed段.md', SAMPLE_SECTION_FILE))
        assert '框架内容块' in sf.content
        assert '@TEMPLATE:FIXED' in sf.content

    def test_section_file_missing_notes_tolerant(self, parser):
        """DT-09: 缺 @SEC:NOTES 的容忍处理"""
        content = """<!-- @SEC:CONTENT -->
只有内容区
<!-- @/SEC:CONTENT -->"""
        f = _write_temp('无笔记段.md', content)
        sf = parser.parse_section_file(f)
        assert '只有内容区' in sf.content
        assert sf.notes == ''

    def test_section_file_missing_content_tolerant(self, parser):
        """DT-09: 缺 @SEC:CONTENT 的容忍处理"""
        content = """<!-- @SEC:NOTES -->
只有笔记区
<!-- @/SEC:NOTES -->"""
        f = _write_temp('无内容段.md', content)
        sf = parser.parse_section_file(f)
        assert sf.content == ''
        assert '只有笔记区' in sf.notes


# ── DT-10: Staging 解析测试（≥5条）──────────────────────────

class TestStagingParsing:
    def test_pending_status(self, parser):
        """DT-10: pending 状态解析"""
        f = _write_temp('pending.md', SAMPLE_STAGING)
        doc = parser.parse_staging(f)
        assert doc.status == 'pending'
        assert len(doc.ops) == 2

    def test_processing_status(self, parser):
        """DT-10: processing 状态解析"""
        content = """status: processing
<!-- @STAGING:1 op="activate" target="§C" -->
<!-- @/STAGING:1 -->"""
        f = _write_temp('processing.md', content)
        doc = parser.parse_staging(f)
        assert doc.status == 'processing'

    def test_single_op(self, parser):
        """DT-10: 单操作解析"""
        content = """status: pending
<!-- @STAGING:1 op="deactivate" target="§D" -->
## 撤下 §D
<!-- @/STAGING:1 -->"""
        f = _write_temp('single.md', content)
        doc = parser.parse_staging(f)
        assert len(doc.ops) == 1
        assert doc.ops[0].op == 'deactivate'
        assert doc.ops[0].target == '§D'

    def test_multi_op(self, parser):
        """DT-10: 多操作解析"""
        f = _write_temp('multi.md', SAMPLE_STAGING)
        doc = parser.parse_staging(f)
        assert len(doc.ops) == 2
        assert doc.ops[0].op == 'change_version'
        assert doc.ops[0].target == '§B'
        assert doc.ops[1].op == 'deactivate'
        assert doc.ops[1].target == '§INBOX'

    def test_change_version_with_content(self, parser):
        """DT-10: change_version 含 content"""
        f = _write_temp('cv.md', SAMPLE_STAGING)
        doc = parser.parse_staging(f)
        op0 = doc.ops[0]
        assert op0.content is not None
        assert '§B 任务窗口' in op0.content
        assert '新版本内容' in op0.content

    def test_activate_with_adapt(self, parser):
        """DT-10: activate 含 adapt="true" """
        content = """status: pending
<!-- @STAGING:1 op="activate" target="§E" adapt="true" -->
## 激活 §E
<!-- @/STAGING:1 -->"""
        f = _write_temp('adapt.md', content)
        doc = parser.parse_staging(f)
        assert doc.ops[0].adapt is True

    def test_missing_status_tolerant(self, parser):
        """DT-10: 缺 status 头的容忍"""
        content = """<!-- @STAGING:1 op="change_version" target="§B" -->
<!-- @/STAGING:1 -->"""
        f = _write_temp('nostatus.md', content)
        doc = parser.parse_staging(f)
        assert doc.status == 'pending'  # default
        assert len(doc.ops) == 1

    def test_parse_staging_status_method(self, parser):
        """DT-10: parse_staging_status 轻量方法"""
        f = _write_temp('status_check.md', 'status: processing\ncontent...')
        assert parser.parse_staging_status(f) == 'processing'

    def test_parse_staging_status_none(self, parser):
        """DT-10: parse_staging_status 无 status 返回 None"""
        f = _write_temp('nostatus2.md', 'just content')
        assert parser.parse_staging_status(f) is None


# ── DT-11: MSG 计数器解析（≥2条）────────────────────────────

class TestMsgCounter:
    def test_extract_counter(self, parser):
        """DT-11: 正常提取 @MSG:NEXT:N"""
        text = '<!-- @MSG:NEXT:10 -->'
        assert parser.parse_msg_counter(text) == 10

    def test_no_counter_returns_zero(self, parser):
        """DT-11: 无计数器返回 0"""
        assert parser.parse_msg_counter('') == 0
        assert parser.parse_msg_counter('<!-- @MSG:1 -->') == 0

    def test_counter_in_context(self, parser):
        """DT-11: 从 SAMPLE_CONTEXT 中提取计数器"""
        assert parser.parse_msg_counter(SAMPLE_CONTEXT) == 10


# ── 综合往返测试 ────────────────────────────────────────────

class TestIntegration:
    def test_parse_context_file(self, parser):
        """完整文件解析：写入→读取→解析"""
        f = _write_temp('cos-context.md', SAMPLE_CONTEXT)
        doc = parser.parse_context(f)
        assert len(doc.sections) == 3

    def test_parse_context_via_path(self, parser):
        """从文件路径直接解析 context"""
        f = _write_temp('ctx.md', SAMPLE_CONTEXT)
        doc = parser.parse_context(f)
        assert len(doc.sections) == 3
