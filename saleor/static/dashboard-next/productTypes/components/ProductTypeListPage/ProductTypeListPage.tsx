import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface AttributeType {
  id: string;
  sortNumber?: number;
  name?: string;
}
interface AttributeEdgeType {
  node: AttributeType;
}
interface ProductTypeListPageProps {
  productTypes?: Array<{
    id: string;
    name?: string;
    hasVariants?: boolean;
    productAttributes?: {
      edges: AttributeEdgeType;
    };
    variantAttributes?: {
      edges: AttributeEdgeType;
    };
  }>;
}

const ProductTypeListPage: React.StatelessComponent<
  ProductTypeListPageProps
> = ({ productTypes }) => <div />;
ProductTypeListPage.displayName = "ProductTypeListPage";
export default ProductTypeListPage;
