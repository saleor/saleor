import { useEffect, useState } from "react";

function useModalDialogOpen(
  open: boolean,
  cbs: {
    onClose?: () => void;
    onOpen?: () => void;
  }
): void {
  const [prevOpen, setPrevOpen] = useState(open);

  useEffect(() => {
    if (open !== prevOpen) {
      setPrevOpen(open);
      if (cbs.onOpen && open) {
        cbs.onOpen();
      }

      if (cbs.onClose && !open) {
        cbs.onClose();
      }
    }
  }, [open]);
}

export default useModalDialogOpen;
