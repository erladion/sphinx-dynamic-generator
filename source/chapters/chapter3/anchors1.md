---
content_order: 20
content_title: MyST Markdown Guide
---

# Introduction to MyST

This file demonstrates how to structure content using Markdown while still leveraging the full power of Sphinx directives.

## Step 1: Installation Checklist
{#installation-anchor}

(installation-anchor)=
This heading has a clean, inline anchor named `installation-anchor`. This is the preferred way to create link targets in MyST Markdown.

To link to this section from another document, you would use the standard Sphinx reference role:

```rst
See the :ref:`installation-anchor`.
```

### Custom Admonition

You can use standard Markdown features while still embedding Sphinx directives using the fenced code block syntax:

```{note}
Remember that all custom anchors must be unique across the entire project!
```