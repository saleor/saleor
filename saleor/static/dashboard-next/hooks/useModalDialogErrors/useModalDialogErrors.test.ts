import { renderHook } from "@testing-library/react-hooks";

import useModalDialogErrors from "./useModalDialogErrors";

const errors = ["err1", "err2"];

test("Does not render errors after close", () => {
  const { result, rerender } = renderHook(
    ({ errors, open }) => useModalDialogErrors(errors, open),
    {
      initialProps: {
        errors: [] as string[],
        open: false
      }
    }
  );

  // Open modal
  rerender({
    errors: [],
    open: true
  });
  expect(result.current.length).toBe(0);

  // Throw errors
  rerender({
    errors,
    open: true
  });
  expect(result.current.length).toBe(2);

  // Close modal
  rerender({
    errors,
    open: false
  });

  // Open modal
  rerender({
    errors,
    open: true
  });
  expect(result.current.length).toBe(0);
});
