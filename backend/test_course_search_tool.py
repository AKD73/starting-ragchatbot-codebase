"""Tests for CourseSearchTool.execute output evaluation."""
import pytest
from unittest.mock import MagicMock
from search_tools import CourseSearchTool
from vector_store import SearchResults


def make_store(documents=None, metadata=None, error=None):
    """Build a mock VectorStore whose search() returns controlled results."""
    store = MagicMock()
    if error is not None:
        store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[], error=error
        )
    else:
        docs = documents or []
        metas = metadata or []
        store.search.return_value = SearchResults(
            documents=docs,
            metadata=metas,
            distances=[0.1] * len(docs),
        )
    return store


# ---------------------------------------------------------------------------
# Error path
# ---------------------------------------------------------------------------

class TestExecuteErrors:
    def test_returns_error_message_from_store(self):
        store = make_store(error="No course found matching 'Nonexistent'")
        tool = CourseSearchTool(store)
        result = tool.execute(query="anything", course_name="Nonexistent")
        assert result == "No course found matching 'Nonexistent'"

    def test_returns_generic_search_error(self):
        store = make_store(error="Search error: collection empty")
        tool = CourseSearchTool(store)
        result = tool.execute(query="loops")
        assert "Search error" in result


# ---------------------------------------------------------------------------
# Empty results
# ---------------------------------------------------------------------------

class TestExecuteEmpty:
    def test_no_results_no_filters(self):
        store = make_store(documents=[], metadata=[])
        tool = CourseSearchTool(store)
        result = tool.execute(query="recursion")
        assert result == "No relevant content found."

    def test_no_results_with_course_filter(self):
        store = make_store(documents=[], metadata=[])
        tool = CourseSearchTool(store)
        result = tool.execute(query="recursion", course_name="Python 101")
        assert "No relevant content found" in result
        assert "Python 101" in result

    def test_no_results_with_lesson_filter(self):
        store = make_store(documents=[], metadata=[])
        tool = CourseSearchTool(store)
        result = tool.execute(query="variables", lesson_number=3)
        assert "No relevant content found" in result
        assert "lesson 3" in result

    def test_no_results_with_both_filters(self):
        store = make_store(documents=[], metadata=[])
        tool = CourseSearchTool(store)
        result = tool.execute(query="variables", course_name="Intro", lesson_number=2)
        assert "No relevant content found" in result
        assert "Intro" in result
        assert "lesson 2" in result


# ---------------------------------------------------------------------------
# Successful results — content formatting
# ---------------------------------------------------------------------------

class TestExecuteFormatting:
    def test_single_result_contains_document_text(self):
        store = make_store(
            documents=["Variables store values."],
            metadata=[{"course_title": "Python Basics", "lesson_number": 1}],
        )
        tool = CourseSearchTool(store)
        result = tool.execute(query="variables")
        assert "Variables store values." in result

    def test_single_result_header_with_lesson(self):
        store = make_store(
            documents=["Lists are ordered sequences."],
            metadata=[{"course_title": "Python Basics", "lesson_number": 2}],
        )
        tool = CourseSearchTool(store)
        result = tool.execute(query="lists")
        assert "[Python Basics - Lesson 2]" in result

    def test_single_result_header_without_lesson(self):
        store = make_store(
            documents=["Overview content."],
            metadata=[{"course_title": "Data Science", "lesson_number": None}],
        )
        tool = CourseSearchTool(store)
        result = tool.execute(query="overview")
        assert "[Data Science]" in result
        assert "Lesson" not in result

    def test_multiple_results_separated_by_blank_lines(self):
        store = make_store(
            documents=["First chunk.", "Second chunk."],
            metadata=[
                {"course_title": "ML Course", "lesson_number": 1},
                {"course_title": "ML Course", "lesson_number": 2},
            ],
        )
        tool = CourseSearchTool(store)
        result = tool.execute(query="machine learning")
        assert "First chunk." in result
        assert "Second chunk." in result
        # Two results are joined by double newline
        assert "\n\n" in result

    def test_missing_course_title_falls_back_to_unknown(self):
        store = make_store(
            documents=["Some content."],
            metadata=[{}],  # no course_title key
        )
        tool = CourseSearchTool(store)
        result = tool.execute(query="content")
        assert "[unknown]" in result


# ---------------------------------------------------------------------------
# Source tracking (last_sources)
# ---------------------------------------------------------------------------

class TestLastSources:
    def test_sources_populated_after_search(self):
        store = make_store(
            documents=["Content A.", "Content B."],
            metadata=[
                {"course_title": "Course X", "lesson_number": 1},
                {"course_title": "Course X", "lesson_number": 2},
            ],
        )
        tool = CourseSearchTool(store)
        tool.execute(query="topic")
        assert tool.last_sources == ["Course X - Lesson 1", "Course X - Lesson 2"]

    def test_sources_without_lesson_number(self):
        store = make_store(
            documents=["Overview."],
            metadata=[{"course_title": "Course Y", "lesson_number": None}],
        )
        tool = CourseSearchTool(store)
        tool.execute(query="overview")
        assert tool.last_sources == ["Course Y"]

    def test_sources_empty_on_no_results(self):
        store = make_store(documents=[], metadata=[])
        tool = CourseSearchTool(store)
        tool.execute(query="nothing")
        assert tool.last_sources == []

    def test_sources_not_set_on_error(self):
        store = make_store(error="Search error: oops")
        tool = CourseSearchTool(store)
        tool.last_sources = ["stale"]
        tool.execute(query="anything")
        # Error path returns early before touching last_sources
        assert tool.last_sources == ["stale"]

    def test_sources_reset_between_calls(self):
        store = make_store(
            documents=["Doc."],
            metadata=[{"course_title": "Course Z", "lesson_number": 5}],
        )
        tool = CourseSearchTool(store)
        tool.execute(query="first call")
        tool.execute(query="second call")
        # Should reflect only the most recent call
        assert tool.last_sources == ["Course Z - Lesson 5"]


# ---------------------------------------------------------------------------
# VectorStore call forwarding
# ---------------------------------------------------------------------------

class TestStoreCallForwarding:
    def test_passes_query_to_store(self):
        store = make_store(documents=[], metadata=[])
        tool = CourseSearchTool(store)
        tool.execute(query="neural networks")
        store.search.assert_called_once_with(
            query="neural networks", course_name=None, lesson_number=None
        )

    def test_passes_course_name_to_store(self):
        store = make_store(documents=[], metadata=[])
        tool = CourseSearchTool(store)
        tool.execute(query="loops", course_name="Intro to Python")
        store.search.assert_called_once_with(
            query="loops", course_name="Intro to Python", lesson_number=None
        )

    def test_passes_lesson_number_to_store(self):
        store = make_store(documents=[], metadata=[])
        tool = CourseSearchTool(store)
        tool.execute(query="functions", lesson_number=4)
        store.search.assert_called_once_with(
            query="functions", course_name=None, lesson_number=4
        )

    def test_passes_all_filters_to_store(self):
        store = make_store(documents=[], metadata=[])
        tool = CourseSearchTool(store)
        tool.execute(query="decorators", course_name="Advanced Python", lesson_number=7)
        store.search.assert_called_once_with(
            query="decorators", course_name="Advanced Python", lesson_number=7
        )
