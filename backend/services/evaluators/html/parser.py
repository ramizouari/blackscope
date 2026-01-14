from typing import Generator, Any
from bs4 import BeautifulSoup, Tag
import re
import bs4
from ..base import BaseExecutionNode, StreamableMessage, ContextData, NodeAssertionFailure
from ..connectivity import AccessCheckNode


class HtmlParsingNode(BaseExecutionNode, node_name="html_validator"):
    __dependencies__ = (AccessCheckNode,)

    def _evaluate_impl(
        self, *args, context: ContextData = None, **kwargs
    ) -> Generator[StreamableMessage, None, bs4.BeautifulSoup]:
        """
        Validates HTML for issues that can affect parsing.
        Only checks for problems that impact HTML parsing, not accessibility or best practices.
        """
        # Get response from connectivity validator

        response = context.history[AccessCheckNode.node_name].value
        if not response or not response.ok:
            yield StreamableMessage(
                message="Cannot validate HTML: response unavailable or failed.",
                level="error",
            )
            return None

        try:
            html_content = response.text

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # 1. Check for duplicate IDs (affects DOM parsing and querySelector)
            ids = {}
            for tag in soup.find_all(id=True):
                tag_id = tag.get("id")
                if tag_id in ids:
                    ids[tag_id] += 1
                else:
                    ids[tag_id] = 1

            duplicate_ids = {k: v for k, v in ids.items() if v > 1}
            if duplicate_ids:
                for dup_id, count in duplicate_ids.items():
                    yield StreamableMessage(
                        message=f"Duplicate ID '{dup_id}' found {count} times. IDs must be unique for proper DOM parsing.",
                        level="bug",
                    )

            # 2. Check for invalid nesting that affects parsing
            invalid_nesting = []
            for p_tag in soup.find_all("p"):
                if p_tag.find("p"):
                    invalid_nesting.append("<p> nested inside <p>")
                if p_tag.find(["div", "section", "article", "aside", "header", "footer"]):
                    invalid_nesting.append("Block element nested inside <p>")

            for a_tag in soup.find_all("a"):
                if a_tag.find("a"):
                    invalid_nesting.append("<a> nested inside <a>")

            if invalid_nesting:
                unique_issues = set(invalid_nesting)
                for issue in unique_issues:
                    yield StreamableMessage(
                        message=f"Invalid nesting detected: {issue}. This can cause parsing issues.",
                        level="bug",
                    )

            # 3. Check for malformed attributes that affect parsing
            for tag in soup.find_all(True):
                for attr_name in tag.attrs:
                    if attr_name in ["href", "src", "action"] and not tag[attr_name]:
                        yield StreamableMessage(
                            message=f"Empty '{attr_name}' attribute on <{tag.name}> tag may cause parsing issues.",
                            level="warning",
                        )

            # 4. Check for incorrect DOCTYPE or missing DOCTYPE
            if not html_content.strip().lower().startswith("<!doctype"):
                yield StreamableMessage(
                    message="Missing DOCTYPE declaration. Browsers may use quirks mode which affects HTML parsing.",
                    level="warning",
                )

            # 5. Check for unclosed comment blocks
            if "<!--" in html_content and html_content.count("<!--") != html_content.count("-->"):
                yield StreamableMessage(
                    message="Mismatched HTML comment tags (<!-- and -->). This can cause content to be hidden.",
                    level="bug",
                )

            # 6. Check for script/style tags that might be improperly closed
            for script in soup.find_all("script"):
                if script.string and "</script>" in script.string.lower():
                    yield StreamableMessage(
                        message="<script> tag contains '</script>' in its content. This will prematurely close the script tag.",
                        level="bug",
                    )

            for style in soup.find_all("style"):
                if style.string and "</style>" in style.string.lower():
                    yield StreamableMessage(
                        message="<style> tag contains '</style>' in its content. This will prematurely close the style tag.",
                        level="bug",
                    )

            # 7. Check for forms without action (affects form parsing)
            forms_without_action = soup.find_all("form", action=False)
            if forms_without_action:
                yield StreamableMessage(
                    message=f"Found {len(forms_without_action)} form(s) without 'action' attribute. This may affect form submission parsing.",
                    level="warning",
                )

            # 8. Check for tables with improper structure (affects table parsing)
            for table in soup.find_all("table"):
                trs_outside_tbody_thead_tfoot = [tr for tr in table.find_all("tr", recursive=False)]
                if trs_outside_tbody_thead_tfoot:
                    yield StreamableMessage(
                        message="Table has <tr> elements directly under <table> without <tbody>. Browsers will auto-insert <tbody> affecting DOM structure.",
                        level="warning",
                    )

            yield StreamableMessage(message="HTML parsing validation completed.", level="info")
            return soup

        except Exception as e:
            raise NodeAssertionFailure(f"Failed to parse HTML: {str(e)}")
