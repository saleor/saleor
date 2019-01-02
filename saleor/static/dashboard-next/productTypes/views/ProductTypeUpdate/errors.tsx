import * as React from "react";

import { UserError } from "../../../types";

interface ProductTypeUpdateErrorsState {
  addAttributeErrors: UserError[];
  editAttributeErrors: UserError[];
  formErrors: UserError[];
}
interface ProductTypeUpdateErrorsProps {
  children: (
    props: {
      errors: ProductTypeUpdateErrorsState;
      set: {
        addAttributeErrors: (errors: UserError[]) => void;
        editAttributeErrors: (errors: UserError[]) => void;
        formErrors: (errors: UserError[]) => void;
      };
    }
  ) => React.ReactNode;
}

export class ProductTypeUpdateErrors extends React.Component<
  ProductTypeUpdateErrorsProps,
  ProductTypeUpdateErrorsState
> {
  state: ProductTypeUpdateErrorsState = {
    addAttributeErrors: [],
    editAttributeErrors: [],
    formErrors: []
  };

  render() {
    return this.props.children({
      errors: this.state,
      set: {
        addAttributeErrors: (addAttributeErrors: UserError[]) =>
          this.setState({ addAttributeErrors }),
        editAttributeErrors: (editAttributeErrors: UserError[]) =>
          this.setState({ editAttributeErrors }),
        formErrors: (formErrors: UserError[]) => this.setState({ formErrors })
      }
    });
  }
}
export default ProductTypeUpdateErrors;
