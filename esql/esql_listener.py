# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.
from antlr4 import ParserRuleContext

from esql.errors import ESQLSyntaxError
from esql.EsqlBaseParser import EsqlBaseParser
from esql.EsqlBaseParserListener import EsqlBaseParserListener


class ESQLValidatorListener(EsqlBaseParserListener):
    """Validate specific fields for ESQL query event types."""

    def __init__(self, schema: dict = {}):
        """Initialize the listener with a schema."""
        self.schema = schema # schema is a dictionary of field names and types
        self.field_list = [] # list of fields used in the query
        self.indices = [] # indices used in the query (e.g. 'logs-*')
        self.get_event_datasets = [] # event.dataset field values used in the query

    def enterQualifiedName(self, ctx: EsqlBaseParser.QualifiedNameContext):  # noqa: N802
        """Extract field from context (ctx)."""

        if not isinstance(ctx.parentCtx, EsqlBaseParser.EvalCommandContext):
            field = ctx.getText()
            self.field_list.append(field)

            if field not in self.schema:
                raise ESQLSyntaxError(f"Invalid field: {field}")

            if field == 'event.dataset':
                self.get_event_datasets.append(ctx.parentCtx.getText())

    def enterSourceIdentifier(self, ctx: EsqlBaseParser.SourceIdentifierContext):  # noqa: N802
        """Extract index and fields from context (ctx)."""

        # Check if the parent context is NOT 'FromCommandContext'
        if not isinstance(ctx.parentCtx, EsqlBaseParser.FromCommandContext):
            # Extract field from context (ctx)
            # The implementation depends on your parse tree structure
            # For example, if the field name is directly the text of this context:
            field = ctx.getText()
            self.field_list.append(field)

            if field not in self.schema:
                raise ValueError(f"Invalid field: {field}")
        else:
            # check index against integrations?
            self.indices.append(ctx.getText())


    def check_literal_type(self, ctx: ParserRuleContext):
        """Check the type of a literal against the schema."""
        field, context_type = self.find_associated_field_and_context(ctx)

        if field and field in self.schema:
            expected_type = self.schema[field]
            actual_type = self.get_literal_type(ctx, context_type)

            if expected_type != actual_type:
                raise ValueError(f"Field '{field}' in context '{context_type}'"
                                 f"expects type '{expected_type}', but got '{actual_type}'")

    def find_associated_field_and_context(self, ctx: ParserRuleContext):
        """Find the field and context type associated with a literal."""
        parent_ctx = ctx.parentCtx
        while parent_ctx:
            if isinstance(parent_ctx, EsqlBaseParser.ComparisonContext):
                # Adjust this logic based on your parse tree structure
                # Example: If the field name is the text of the first child of the operator expression
                field_ctx = parent_ctx.operatorExpression(0).getChild(0)
                field = field_ctx.getText() if field_ctx else None
                return field, 'Comparison'
            elif isinstance(parent_ctx, EsqlBaseParser.LogicalInContext):
                field_ctx = parent_ctx.valueExpression(0).getChild(0)
                return field_ctx.getText() if field_ctx else None, 'LogicalIn'
            # Add additional conditions for other contexts where constants appear
            parent_ctx = parent_ctx.parentCtx
        return None, None

    def get_literal_type(self, ctx: ParserRuleContext, context_type: str):
        """Get the type of a literal."""
        # Determine the type of the literal based on the context type
        if context_type == 'Comparison' or context_type == 'LogicalIn':
            if isinstance(ctx, EsqlBaseParser.StringLiteralContext):
                return 'keyword'  # currently a 'string'
            elif isinstance(ctx, (EsqlBaseParser.IntegerLiteralContext, EsqlBaseParser.QualifiedIntegerLiteralContext)):
                return 'integer'
            elif isinstance(ctx, EsqlBaseParser.DecimalLiteralContext):
                return 'decimal'
            elif isinstance(ctx, EsqlBaseParser.BooleanLiteralContext):
                return 'boolean'
            # Add more conditions based on context_type and other types of literals as needed
        else:
            return 'unknown'

    def get_event_dataset(self, ctx: ParserRuleContext):
        """Get the event dataset."""
        parent_ctx = ctx.parentCtx
        while parent_ctx:
            if isinstance(parent_ctx, EsqlBaseParser.WhereCommandContext):
                return parent_ctx.sourceIdentifier().getText()
            parent_ctx = parent_ctx.parentCtx
        return None

    # Override methods to use check_literal_type
    def enterNullLiteral(self, ctx: EsqlBaseParser.NullLiteralContext):  # noqa: N802
        """Check the type of a null literal against the schema."""
        self.check_literal_type(ctx)

    def enterQualifiedIntegerLiteral(self, ctx: EsqlBaseParser.QualifiedIntegerLiteralContext):  # noqa: N802
        """Check the type of a qualified integer literal against the schema."""
        self.check_literal_type(ctx)

    def enterDecimalLiteral(self, ctx: EsqlBaseParser.DecimalLiteralContext):  # noqa: N802
        """Check the type of a decimal literal against the schema."""
        self.check_literal_type(ctx)

    def enterIntegerLiteral(self, ctx: EsqlBaseParser.IntegerLiteralContext):  # noqa: N802
        """Check the type of an integer literal against the schema."""
        self.check_literal_type(ctx)

    def enterBooleanLiteral(self, ctx: EsqlBaseParser.BooleanLiteralContext):  # noqa: N802
        """Check the type of a boolean literal against the schema."""
        self.check_literal_type(ctx)

    def enterStringLiteral(self, ctx: EsqlBaseParser.StringLiteralContext):  # noqa: N802
        """Check the type of a string literal against the schema."""
        self.check_literal_type(ctx)

    def enterNumericArrayLiteral(self, ctx: EsqlBaseParser.NumericArrayLiteralContext):  # noqa: N802
        """Check the type of a numeric array literal against the schema."""
        self.check_literal_type(ctx)

    def enterBooleanArrayLiteral(self, ctx: EsqlBaseParser.BooleanArrayLiteralContext):  # noqa: N802
        """Check the type of a boolean array literal against the schema."""
        self.check_literal_type(ctx)

    def enterStringArrayLiteral(self, ctx: EsqlBaseParser.StringArrayLiteralContext):  # noqa: N802
        """Check the type of a string array literal against the schema."""
        self.check_literal_type(ctx)
