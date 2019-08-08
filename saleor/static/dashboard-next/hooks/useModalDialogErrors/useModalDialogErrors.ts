import useModalDialogOpen from "../useModalDialogOpen";
import useStateFromProps from "../useStateFromProps";

function useModalDialogErrors<TError>(
  errors: TError[],
  open: boolean
): TError[] {
  const [state, setState] = useStateFromProps(errors);

  useModalDialogOpen(open, {
    onClose: () => setState([])
  });

  return state;
}

export default useModalDialogErrors;
