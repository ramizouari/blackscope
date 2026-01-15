from typing import Generator, Any
from bs4 import BeautifulSoup, Tag
import re

from ..base import BaseExecutionNode, ContextData
from ..errors import NodeAssertionFailure
from ..messages import StreamableMessage, Metric, MetricsList, MetricsMessage
from ..connectivity import AccessCheckNode


class HtmlComplianceNode(BaseExecutionNode, node_name="html_compliance"):
    """
    Validates and analyzes HTML content for structural integrity, security vulnerabilities,
    accessibility adherence, and best practice compliance. Provides a mechanism to report
    identified issues and apply corrective measures, ensuring the HTML is improved and
    ready for further processing. The results are delivered via streamable messages.
    """
    __dependencies__ = (AccessCheckNode.node_name,)

    def _evaluate_impl(
        self, *args, context: ContextData = None, **kwargs
    ) -> Generator[StreamableMessage, None, str | None]:
        """
        Validates HTML for potential issues including bugs, vulnerabilities, and improvements.
        Returns corrected HTML for further analysis.
        """

        response = context.history[AccessCheckNode.node_name].value
        if not response or not response.ok:
            yield StreamableMessage(
                message="Cannot validate HTML: response unavailable or failed.",
                level="error",
            )
            return None

        try:
            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")

            # Track corrections for corrected HTML output
            corrections_made = []
            # Track issues by category for final assessment
            issues_by_category = {
                "Structure": [],
                "Security": [],
                "Accessibility": [],
                "Best Practices": [],
            }

            # 1. Check for missing DOCTYPE
            if not html_content.strip().lower().startswith("<!doctype"):
                msg = "Missing DOCTYPE declaration. Modern HTML should include <!DOCTYPE html>."
                yield StreamableMessage(message=msg, level="improvement")
                issues_by_category["Structure"].append(msg)

            # 2. Check for html, head, and body tags
            if not soup.html:
                msg = "Missing <html> tag. Document structure is incomplete."
                yield StreamableMessage(message=msg, level="bug")
                issues_by_category["Structure"].append(msg)
            if not soup.head:
                msg = "Missing <head> tag. Document structure is incomplete."
                yield StreamableMessage(message=msg, level="bug")
                issues_by_category["Structure"].append(msg)
            if not soup.body:
                msg = "Missing <body> tag. Document structure is incomplete."
                yield StreamableMessage(message=msg, level="bug")
                issues_by_category["Structure"].append(msg)

            # 3. Check for charset declaration
            meta_charset = soup.find("meta", charset=True) or soup.find(
                "meta", attrs={"http-equiv": "Content-Type"}
            )
            if not meta_charset:
                msg = "Missing charset declaration. Add <meta charset='UTF-8'> in <head> to prevent encoding issues."
                yield StreamableMessage(message=msg, level="improvement")
                issues_by_category["Best Practices"].append(msg)

            # 4. Check for viewport meta tag (mobile responsiveness)
            if not soup.find("meta", attrs={"name": "viewport"}):
                msg = "Missing viewport meta tag. Add <meta name='viewport' content='width=device-width, initial-scale=1.0'> for mobile responsiveness."
                yield StreamableMessage(message=msg, level="improvement")
                issues_by_category["Best Practices"].append(msg)

            # 5. Check for title tag
            if not soup.title or not soup.title.string or not soup.title.string.strip():
                msg = "Missing or empty <title> tag. Every page should have a descriptive title."
                yield StreamableMessage(message=msg, level="warning")
                issues_by_category["Best Practices"].append(msg)

            # 6. Security: Check for inline JavaScript (XSS vulnerability)
            inline_scripts = soup.find_all("script", src=False)
            for script in inline_scripts:
                if script.string and re.search(r"eval\s*\(|document\.write\s*\(", script.string):
                    msg = "Potentially unsafe inline JavaScript using eval() or document.write(). This can lead to XSS vulnerabilities."
                    yield StreamableMessage(message=msg, level="vulnerability")
                    issues_by_category["Security"].append(msg)
                    break

            # 7. Security: Check for missing Content Security Policy
            csp_meta = soup.find("meta", attrs={"http-equiv": "Content-Security-Policy"})
            if not csp_meta:
                msg = "No Content Security Policy (CSP) meta tag found. Consider adding CSP to mitigate XSS attacks."
                yield StreamableMessage(message=msg, level="improvement")
                issues_by_category["Security"].append(msg)

            # 8. Check for images without alt attributes (accessibility)
            images_without_alt = soup.find_all("img", alt=False)
            if images_without_alt:
                msg = f"Found {len(images_without_alt)} image(s) without 'alt' attributes. This impacts accessibility and SEO."
                yield StreamableMessage(message=msg, level="warning")
                issues_by_category["Accessibility"].append(msg)
                # Add alt attributes to corrections
                for img in images_without_alt:
                    img["alt"] = ""
                    corrections_made.append("Added empty alt attributes to images")

            # 9. Check for links without href or with javascript: protocol (security)
            suspicious_links = soup.find_all("a", href=re.compile(r"^javascript:", re.I))
            if suspicious_links:
                msg = f"Found {len(suspicious_links)} link(s) using 'javascript:' protocol. This can be a security risk and accessibility issue."
                yield StreamableMessage(message=msg, level="vulnerability")
                issues_by_category["Security"].append(msg)

            # 10. Check for external links without rel="noopener" or rel="noreferrer"
            external_links = soup.find_all("a", target="_blank")
            unsafe_external_links = [
                link
                for link in external_links
                if not link.get("rel") or "noopener" not in link.get("rel", [])
            ]
            if unsafe_external_links:
                msg = f"Found {len(unsafe_external_links)} link(s) with target='_blank' without rel='noopener'. This can lead to security vulnerabilities (tabnabbing)."
                yield StreamableMessage(message=msg, level="vulnerability")
                issues_by_category["Security"].append(msg)
                # Fix external links
                for link in unsafe_external_links:
                    rel_values = link.get("rel", [])
                    if isinstance(rel_values, str):
                        rel_values = rel_values.split()
                    if "noopener" not in rel_values:
                        rel_values.append("noopener")
                    link["rel"] = " ".join(rel_values)
                    corrections_made.append("Added rel='noopener' to external links")

            # 11. Check for deprecated HTML tags
            deprecated_tags = ["center", "font", "marquee", "blink", "frame", "frameset"]
            for tag_name in deprecated_tags:
                deprecated = soup.find_all(tag_name)
                if deprecated:
                    msg = f"Found deprecated <{tag_name}> tag(s) ({len(deprecated)} occurrence(s)). Use CSS instead."
                    yield StreamableMessage(message=msg, level="warning")
                    issues_by_category["Best Practices"].append(msg)

            # 12. Check for forms without action attribute
            forms_without_action = soup.find_all("form", action=False)
            if forms_without_action:
                msg = f"Found {len(forms_without_action)} form(s) without 'action' attribute."
                yield StreamableMessage(message=msg, level="bug")
                issues_by_category["Structure"].append(msg)

            # 13. Check for input fields without labels (accessibility)
            inputs = soup.find_all("input", type=lambda t: t not in ["hidden", "submit", "button"])
            inputs_without_labels = []
            for inp in inputs:
                input_id = inp.get("id")
                if not input_id or not soup.find("label", attrs={"for": input_id}):
                    # Check if input is wrapped in a label
                    parent_label = inp.find_parent("label")
                    if not parent_label:
                        inputs_without_labels.append(inp)

            if inputs_without_labels:
                msg = f"Found {len(inputs_without_labels)} input field(s) without associated labels. This impacts accessibility."
                yield StreamableMessage(message=msg, level="warning")
                issues_by_category["Accessibility"].append(msg)

            # 14. Check for duplicate IDs
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
                    msg = f"Duplicate ID '{dup_id}' found {count} times. IDs must be unique."
                    yield StreamableMessage(message=msg, level="bug")
                    issues_by_category["Structure"].append(msg)

            # 15. Check for mixed content (HTTP resources on HTTPS pages)
            if context.url.startswith("https://"):
                http_resources = []
                for tag in soup.find_all(["img", "script", "link", "iframe"]):
                    src = tag.get("src") or tag.get("href")
                    if src and src.startswith("http://"):
                        http_resources.append(src)

                if http_resources:
                    msg = f"Found {len(http_resources)} HTTP resource(s) on HTTPS page. This can cause mixed content warnings and security issues."
                    yield StreamableMessage(message=msg, level="vulnerability")
                    issues_by_category["Security"].append(msg)

            # 16. Check for inline styles (maintainability)
            inline_styles = soup.find_all(style=True)
            if len(inline_styles) > 10:
                msg = f"Found {len(inline_styles)} elements with inline styles. Consider using external CSS for better maintainability."
                yield StreamableMessage(message=msg, level="improvement")
                issues_by_category["Best Practices"].append(msg)

            # 17. Check for missing language attribute
            html_tag = soup.find("html")
            if html_tag and not html_tag.get("lang"):
                msg = "Missing 'lang' attribute on <html> tag. This helps screen readers and search engines."
                yield StreamableMessage(message=msg, level="warning")
                issues_by_category["Accessibility"].append(msg)
                # Add lang attribute
                html_tag["lang"] = "en"
                corrections_made.append("Added lang='en' to html tag")

            # 18. Check for empty heading tags
            for i in range(1, 7):
                empty_headings = [h for h in soup.find_all(f"h{i}") if not h.get_text(strip=True)]
                if empty_headings:
                    msg = f"Found {len(empty_headings)} empty <h{i}> tag(s). Empty headings confuse screen readers."
                    yield StreamableMessage(message=msg, level="warning")
                    issues_by_category["Accessibility"].append(msg)

            # 19. Check for tables without proper structure
            tables = soup.find_all("table")
            for table in tables:
                if not table.find("th") and not table.find("caption"):
                    msg = "Table found without header cells (<th>) or caption. This impacts accessibility."
                    yield StreamableMessage(message=msg, level="warning")
                    issues_by_category["Accessibility"].append(msg)
                    break

            # 20. Check for iframes without title
            iframes_without_title = soup.find_all("iframe", title=False)
            if iframes_without_title:
                msg = f"Found {len(iframes_without_title)} iframe(s) without 'title' attribute. This impacts accessibility."
                yield StreamableMessage(message=msg, level="warning")
                issues_by_category["Accessibility"].append(msg)
                # Add title to iframes
                for iframe in iframes_without_title:
                    iframe["title"] = "Embedded content"
                    corrections_made.append("Added title to iframes")

            # Calculate scores for each category
            total_issues = sum(len(issues) for issues in issues_by_category.values())
            category_metrics = []

            for category, issues in issues_by_category.items():
                if issues:
                    # Score decreases with more issues (max 100, min 0)
                    score = max(0, 100 - len(issues) * 10)
                    feedback = f"{len(issues)} issue(s) found in {category}"
                else:
                    score = 100
                    feedback = f"No issues found in {category}"

                category_metrics.append(
                    Metric(
                        name=category,
                        score=score,
                        feedback=feedback,
                        issues=issues if issues else None
                    )
                )

            # Calculate overall score
            overall_score = max(0, 100 - total_issues * 5) if total_issues > 0 else 100
            overall_feedback = f"Found {total_issues} total issue(s) across all categories" if total_issues > 0 else "No HTML compliance issues found"

            # Yield final assessment
            yield MetricsMessage(
                message="HTML Compliance Assessment",
                details=MetricsList(
                    name="HTML Compliance Assessment",
                    metrics=category_metrics,
                    score=overall_score,
                    feedback=overall_feedback,
                )
            )

            # Generate corrected HTML if corrections were made
            if corrections_made:
                corrected_html = str(soup.prettify())
                yield StreamableMessage(
                    message=f"Applied {len(set(corrections_made))} type(s) of corrections to HTML.",
                    level="info",
                )
                return corrected_html
            else:
                yield StreamableMessage(
                    message="No automatic corrections applied.", level="info"
                )
                return html_content

        except Exception as e:
            self.logger.exception(e)
            raise NodeAssertionFailure(f"Failed to parse HTML: {str(e)}")

    @property
    def full_name(self):
        return "HTML Compliance Assessment"