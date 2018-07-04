import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
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
    gridTemplateColumns: "60px 1fr",
  },
  thumbnail: {
    maxWidth: "60px"
  }
}));

const ProductVariantProduct = decorate<ProductVariantProductProps>(
  ({ classes, product, loading, placeholderImage }) => (
    <Card>
      <CardContent>
        <div className={classes.root}>
          <img className={classes.thumbnail} src={product ? product.thumbnailUrl : placeholderImage } />
          <div>
            <Typography>{product ? product.name : <Skeleton /> }</Typography>
            <Typography variant="caption">
              {product ? (
                i18n.t("Variants:") + " " + product.variants.totalCount
              ) : (
                <Skeleton />
              )}
            </Typography>
          </div>
        </div>
      </CardContent>
    </Card>
  )
);
export default ProductVariantProduct;
