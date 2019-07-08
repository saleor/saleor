import { useState } from "react";

import { PAGINATE_BY } from "../config";

function useRowChange() {
  const [rowNumber, setRowNumber] = useState(PAGINATE_BY);

  function onRowChange(event: React.ChangeEvent<any>) {
    setRowNumber(event.target.value);
  }

  return {
    rowNumber,
    onRowChange
  };
}

export default useRowChange;
