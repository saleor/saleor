# JIRA Story: Refactor LineInfo Base Class

## Story Type
Technical Debt / Code Improvement

## Title
Refactor `LineInfo` base class: Fix type annotation consistency and implement `variant_discounted_price` property

## Description
This story addresses code consistency and completeness issues in the `LineInfo` base class located in `saleor/core/pricing/interface.py`. The changes improve type annotation consistency and provide a base implementation for the `variant_discounted_price` property that was previously raising `NotImplementedError`.

## Background
The `LineInfo` dataclass serves as a base class for `CheckoutLineInfo` and `EditableOrderLineInfo`, which both implement their own versions of `variant_discounted_price`. However, the base class had:
1. Inconsistent type annotation (`str | None` vs `Optional[str]`)
2. An unimplemented `variant_discounted_price` property that raised `NotImplementedError`

## Changes Made

### 1. Type Annotation Consistency
- **Changed**: `voucher_code: str | None` → `voucher_code: Optional[str]`
- **Reason**: Maintains consistency with the rest of the codebase which uses `Optional[...]` from the `typing` module

### 2. Implemented `variant_discounted_price` Property
- **Added**: Base implementation of `variant_discounted_price` property
- **Functionality**:
  - Handles both `CheckoutLine` and `OrderLine` types (which have different attribute names for undiscounted prices)
  - Applies catalogue discounts using the existing `get_catalogue_discounts()` method
  - Returns a properly quantized `Money` object
  - Includes proper error handling and fallbacks
  - Maintains compatibility with existing subclass implementations

## Technical Details

### Files Modified
- `saleor/core/pricing/interface.py`

### Implementation Details
The `variant_discounted_price` implementation:
- Checks for `undiscounted_unit_price` (CheckoutLine) or `undiscounted_base_unit_price` (OrderLine)
- Calculates total price by multiplying undiscounted unit price by quantity
- Applies catalogue promotion discounts
- Ensures the result is non-negative using `zero_money()`
- Quantizes the final price using `quantize_price()`

### Dependencies
- Uses existing methods: `get_catalogue_discounts()`
- Imports: `quantize_price` from `...core.prices`, `zero_money` from `...core.taxes`
- Type hints: `Money` from `prices` package

## Acceptance Criteria

- [x] Type annotation for `voucher_code` is consistent with the rest of the codebase (`Optional[str]`)
- [x] `variant_discounted_price` property is implemented in the base `LineInfo` class
- [x] Implementation handles both `CheckoutLine` and `OrderLine` types
- [x] Implementation correctly applies catalogue discounts
- [x] Implementation returns a properly quantized `Money` object
- [x] Code passes linting checks
- [x] Implementation includes proper type hints and documentation
- [x] Base implementation doesn't break existing subclass implementations

## Testing Considerations

### Unit Tests
- Verify `variant_discounted_price` returns correct value for `CheckoutLine`
- Verify `variant_discounted_price` returns correct value for `OrderLine`
- Verify catalogue discounts are properly applied
- Verify edge cases (no discounts, zero quantity, etc.)

### Integration Tests
- Ensure existing tests for `CheckoutLineInfo.variant_discounted_price` still pass
- Ensure existing tests for `EditableOrderLineInfo.variant_discounted_price` still pass
- Verify no regressions in pricing calculations

## Impact Assessment

### Risk Level
**Low** - This is a base class improvement that:
- Maintains backward compatibility (subclasses can still override)
- Follows existing patterns from subclass implementations
- Only affects the base class behavior when directly used

### Affected Areas
- `LineInfo` base class and any code that directly uses it
- Subclasses (`CheckoutLineInfo`, `EditableOrderLineInfo`) are unaffected as they override this property

## Related Issues
- N/A (standalone improvement)

## Notes
- The base implementation follows the same pattern as `EditableOrderLineInfo.variant_discounted_price`
- Subclasses can still override this method for more specific behavior (e.g., `CheckoutLineInfo` handles price overrides and channel listings)
- This change makes the base class more complete and usable on its own

