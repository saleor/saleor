import * as React from "react";

import Form from "../../components/Form";
import ProductDetailsForm from "../components/ProductDetailsForm";

interface ProductUpdateProps {
  id: string;
}
export const ProductUpdate: React.StatelessComponent<ProductUpdateProps> = ({
  id
}) => (
  <div>
    <Form onSubmit={() => {}}>
      {({ change, data, submit }) => (
        <ProductDetailsForm
          onBack={() => window.history.back()}
          onChange={() => {}}
        />
      )}
    </Form>
  </div>
);
export default ProductUpdate;
