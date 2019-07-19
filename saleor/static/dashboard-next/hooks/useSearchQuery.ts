import React from "react";

import { ChangeEvent } from "@saleor/hooks/useForm";

export type UseSearchQuery = [string, (event: ChangeEvent) => void];
function useSearchQuery(
  onFetch: (query: string) => void,
  initial?: string
): UseSearchQuery {
  const [query, setQuery] = React.useState(initial || "");
  const change = (event: ChangeEvent) => {
    const value = event.target.value;

    onFetch(value);
    setQuery(value);
  };

  return [query, change];
}

export default useSearchQuery;
