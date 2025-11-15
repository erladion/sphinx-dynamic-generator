from docutils.parsers.rst import Directive
from docutils import nodes
import yaml
import re

class MetadataDirective(Directive):
    """
    Parses a YAML block of custom metadata (order, content destination, etc.)
    and stores it in a custom Docutils node for the generator script to read.
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        try:
            # Parse the content block as YAML
            metadata = yaml.safe_load("\n".join(self.content))
            if not metadata:
                metadata = {}
        except Exception as e:
            error = self.state_machine.reporter.error(
                f'Error parsing custom metadata YAML: {e}',
                nodes.literal_block(self.block_text, self.block_text), line=self.lineno
            )
            return [error]

        # Create a custom Docutils node to hold the metadata data.
        # This node will be ignored by the final HTML builder but is visible 
        # to your Python script during the Sphinx environment build phase.
        metadata_node = metadata_node_class(metadata=metadata)
        
        # Ensure the node is included in the document structure
        return [metadata_node]

# Define a custom node class to hold the metadata dictionary
# This is a standard Docutils approach for custom data.
class metadata_node_class(nodes.General, nodes.Element):
    pass

class MetadataEndDirective(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    
    def run(self):
        return []

def setup(app):
    def skip_node(self, node):
        """Standard handler that skips the node and all its children."""
        raise nodes.SkipNode

    def noop(self, node):
        """No-op handler for visiting/departing the node."""
        pass

    # Add custom node and directive roles
    app.add_node(metadata_node_class, html=(skip_node, None), latex=(skip_node, None), text=(skip_node, None))
    
    # Register the directives
    app.add_directive('metadata', MetadataDirective)
    app.add_directive('metadata-end', MetadataEndDirective)

    return {
        'version': '2.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }