import * as React from "react";
import Grid from "material-ui/Grid";
import Typography from "material-ui/Typography";
import Button from "material-ui/Button";
import { Link } from "react-router-dom";

import { CategoryPropertiesQuery } from "../gql-types";
import ProductChildElement from "./ProductChildElement";
import { categoryAddUrl } from "../";
import i18n from "../../i18n";

interface ProductListProps {
  products?: CategoryPropertiesQuery["category"]["products"]["edges"];
  handleLoadMore();
  canLoadMore: boolean;
}

export const ProductList: React.StatelessComponent<ProductListProps> = ({
  products,
  handleLoadMore,
  canLoadMore
}) => (
  <>
    <Grid container>
      {products === undefined ? (
        <Grid item xs={12} sm={6} md={4} lg={3} xl={2}>
          <ProductChildElement
            loading={true}
            label=""
            url=""
            price=""
            thumbnail=""
          />
        </Grid>
      ) : products.length > 0 ? (
        products.map(edge => (
          <Grid item key={edge.node.id} xs={12} sm={6} md={4} lg={3} xl={2}>
            <ProductChildElement
              url="#"
              label={edge.node.name}
              price={edge.node.price.localized}
              thumbnail={edge.node.thumbnailUrl}
            />
          </Grid>
        ))
      ) : (
        <Grid item xs={12}>
          <Typography variant="body2">{i18n.t("No products found")}</Typography>
        </Grid>
      )}
    </Grid>
    {canLoadMore && (
      <Button color="primary" onClick={handleLoadMore}>
        {i18n.t("Load more", { context: "button" })}
      </Button>
    )}
  </>
);

export default ProductList;
