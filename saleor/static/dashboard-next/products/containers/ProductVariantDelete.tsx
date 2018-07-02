import * as React from "react";
import { Redirect } from "react-router-dom";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import { productUrl } from "../index";
import { TypedVariantDeleteMutation, variantDeleteMutation } from "../mutations";

interface VariantDeleteProviderProps {
  productId: string;
  variantId: string;
  children: ((deleteVariant: () => void) => React.ReactElement<any>);
}

const VariantDeleteProvider: React.StatelessComponent<
  VariantDeleteProviderProps
> = ({ productId, variantId, children }) => (
  <TypedVariantDeleteMutation
    mutation={variantDeleteMutation}
    variables={{ id: variantId }}
  >
    {(deleteVariant, { called, loading, error }) => {
      if (called && !loading) {
        return <Redirect to={productUrl(productId)} push={false} />;
      }
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children(() => deleteVariant());
    }}
  </TypedVariantDeleteMutation>
);

export default VariantDeleteProvider;
