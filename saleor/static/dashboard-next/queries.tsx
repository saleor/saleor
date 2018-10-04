import { DocumentNode } from "graphql";
import * as React from "react";
import { Query, QueryProps, QueryResult } from "react-apollo";

import Messages from "./components/messages";
import i18n from "./i18n";

interface TypedQueryInnerProps<TData, TVariables> {
  children: (result: QueryResult<TData, TVariables>) => React.ReactNode;
  skip?: boolean;
  variables?: TVariables;
}

export function TypedQuery<TData, TVariables>(query: DocumentNode) {
  const StrictTypedQuery: React.ComponentType<
    QueryProps<TData, TVariables>
  > = Query;
  return ({
    children,
    skip,
    variables
  }: TypedQueryInnerProps<TData, TVariables>) => (
    <Messages>
      {pushMessage => (
        <StrictTypedQuery
          fetchPolicy="cache-and-network"
          query={query}
          variables={variables}
          skip={skip}
        >
          {props => {
            if (props.error) {
              const msg = i18n.t("Something went wrong: {{ message }}", {
                message: props.error.message
              });
              pushMessage({ text: msg });
            }
            return children(props);
          }}
        </StrictTypedQuery>
      )}
    </Messages>
  );
}
