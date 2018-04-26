import Card, { CardContent } from "material-ui/Card";
import { withStyles } from "material-ui/styles";
import Typography from "material-ui/Typography";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductVariantProductProps {
  product?: {
    id: string;
    name: string;
    thumbnailUrl: string;
    variants: {
      totalCount: number;
    };
  };
  loading?: boolean;
  placeholderImage?: string;
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "60px 1fr"
  }
}));
const ProductVariantProduct = decorate<ProductVariantProductProps>(
  ({ classes, product, loading, placeholderImage }) => (
    <Card>
      <CardContent>
        <div className={classes.root}>
          <img src={loading ? placeholderImage : product.thumbnailUrl} />
          <div>
            <Typography>{loading ? <Skeleton /> : product.name}</Typography>
            <Typography variant="caption">
              {loading ? (
                <Skeleton />
              ) : (
                i18n.t("Variants:") + " " + product.variants.totalCount
              )}
            </Typography>
          </div>
        </div>
      </CardContent>
    </Card>
  )
);
export default ProductVariantProduct;
