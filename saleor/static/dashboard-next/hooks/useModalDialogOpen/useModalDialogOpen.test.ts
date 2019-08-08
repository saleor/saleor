import { renderHook } from "@testing-library/react-hooks";

import useModalDialogOpen from "./useModalDialogOpen";

const onClose = jest.fn();
const onOpen = jest.fn();

const cbs = {
  onClose,
  onOpen
};

test("Does not render errors after close", () => {
  const { rerender } = renderHook(
    ({ open, cbs }) => useModalDialogOpen(open, cbs),
    {
      initialProps: {
        cbs,
        open: false
      }
    }
  );

  // Open modal
  rerender({
    cbs,
    open: true
  });
  expect(onOpen).toBeCalledTimes(1);
  expect(onClose).toBeCalledTimes(0);

  // Rerender modal
  rerender({
    cbs,
    open: true
  });
  expect(onOpen).toBeCalledTimes(1);
  expect(onClose).toBeCalledTimes(0);

  // Close modal
  rerender({
    cbs,
    open: false
  });
  expect(onOpen).toBeCalledTimes(1);
  expect(onClose).toBeCalledTimes(1);

  // Open modal
  rerender({
    cbs,
    open: true
  });
  expect(onOpen).toBeCalledTimes(2);
  expect(onClose).toBeCalledTimes(1);
});
