.. metadata::
   :content_order: 10
   :content_title: Core RST Concepts

.. _starting-point:

Starting Point: Understanding RST
=================================

This chapter covers the basic syntax of reStructuredText (RST) and how it integrates with Sphinx. We've defined a link target named `starting-point` just above this heading.

To create links within your own file or from another chapter, you would use:

.. code-block:: rst

    See this section: :ref:`starting-point`

---

Admonition Blocks
~~~~~~~~~~~~~~~~~

Admonition blocks are essential for drawing attention to specific types of information. They all use the same simple directive syntax.

.. note::
    This content is a standard **Note**. It is used for informational text that is helpful but not critical to proceeding.

.. tip::
    This is a **Tip**. Use it to provide shortcuts, best practices, or advice that improves the user experience.

.. important::
    This is an **Important** block. It highlights crucial information that the user must know before continuing. Treat it as mandatory reading.

.. warning::
    This is a **Warning**. Use it for potential pitfalls, non-critical errors, or sequences that require careful action.
    
.. caution::
    This is a **Caution** block. While similar to a Warning, it often implies a risk that needs careful consideration or avoidance to prevent problems.

---

Linking Targets
~~~~~~~~~~~~~~~

The power of Sphinx comes from cross-referencing. Any heading you create automatically becomes a link target. However, using anonymous targets (like `starting-point`) allows you to link to specific *points* in the text, not just headings.