import { ApolloError } from "apollo-client";
import { DocumentNode } from "graphql";
import React from "react";
import {
  Mutation,
  MutationFn,
  MutationResult,
  MutationUpdaterFn
} from "react-apollo";

import useNotifier from "./hooks/useNotifier";
import i18n from "./i18n";

export interface TypedMutationInnerProps<TData, TVariables> {
  children: (
    mutateFn: MutationFn<TData, TVariables>,
    result: MutationResult<TData>
  ) => React.ReactNode;
  onCompleted?: (data: TData) => void;
  onError?: (error: ApolloError) => void;
  variables?: TVariables;
}

export function TypedMutation<TData, TVariables>(
  mutation: DocumentNode,
  update?: MutationUpdaterFn<TData>
) {
  class StrictTypedMutation extends Mutation<TData, TVariables> {}
  return (props: TypedMutationInnerProps<TData, TVariables>) => {
    const notify = useNotifier();
    // Obviously, this is workaround to the problem described here:
    // https://github.com/DefinitelyTyped/DefinitelyTyped/issues/32588
    const {
      children,
      onCompleted,
      onError,
      variables
    } = props as JSX.LibraryManagedAttributes<
      typeof StrictTypedMutation,
      typeof props
    >;
    return (
      <StrictTypedMutation
        mutation={mutation}
        onCompleted={onCompleted}
        onError={err => {
          const msg = i18n.t("Something went wrong: {{ message }}", {
            message: err.message
          });
          notify({ text: msg });
          if (onError) {
            onError(err);
          }
        }}
        variables={variables}
        update={update}
      >
        {children}
      </StrictTypedMutation>
    );
  };
}
